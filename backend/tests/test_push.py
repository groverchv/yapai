"""Web Push: endpoints de suscripción del cliente y servicio de envío.

No se envían pushes reales: `_webpush` se mockea donde hace falta y los tests
de configuración parchean `settings` para simular VAPID ausente/presente.
"""
import uuid

from app.core.config import settings
from app.models import Cliente, PushSuscripcion
from app.services import push as push_service
from sqlalchemy import select, text

API = "/api/v1"


def _cliente_login(client, ci, telefono):
    r = client.post(f"{API}/auth/cliente/login",
                    json={"ci": ci, "telefono": telefono})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}


def _nuevo_cliente(db, client):
    ci, tel = f"PS{uuid.uuid4().hex[:8]}", f"75{uuid.uuid4().int % 10**6:06d}"
    db.execute(text(
        "INSERT INTO clientes (nombre, ci, telefono, estado, saldo_puntos,"
        " puntos_congelados) VALUES (:nm, :ci, :tel, 'activo', 0, 0)"),
        {"nm": "Push Test", "ci": ci, "tel": tel})
    db.commit()
    cid = db.scalar(select(Cliente.id).where(Cliente.ci == ci))
    return cid, _cliente_login(client, ci, tel)


def _sub(endpoint="https://push.example.com/sub/abc"):
    return {"endpoint": endpoint, "keys": {"p256dh": "k1", "auth": "a1"}}


def test_vapid_devuelve_clave_o_null(db, client):
    _cid, headers = _nuevo_cliente(db, client)
    r = client.get(f"{API}/cliente/push/vapid", headers=headers)
    assert r.status_code == 200
    assert "public_key" in r.json()


def test_suscripcion_requiere_auth(client):
    r = client.post(f"{API}/cliente/push/suscripcion", json=_sub())
    assert r.status_code == 401


def test_suscripcion_crea_y_hace_upsert(db, client):
    cid, headers = _nuevo_cliente(db, client)
    if not push_service.push_disponible():
        _forzar_vapid(True)

    r = client.post(f"{API}/cliente/push/suscripcion", json=_sub(), headers=headers)
    assert r.status_code == 201, r.text

    sub = db.scalar(select(PushSuscripcion).where(
        PushSuscripcion.endpoint == "https://push.example.com/sub/abc"))
    assert sub and sub.cliente_id == cid

    # Re-suscripción con mismo endpoint: actualiza keys, no duplica
    r = client.post(f"{API}/cliente/push/suscripcion",
                    json={"endpoint": "https://push.example.com/sub/abc",
                          "keys": {"p256dh": "k2", "auth": "a2"}},
                    headers=headers)
    assert r.status_code == 201
    db.expire_all()  # la sesión cachea el objeto del primer scalar
    subs = db.scalars(select(PushSuscripcion).where(
        PushSuscripcion.endpoint == "https://push.example.com/sub/abc")).all()
    assert len(subs) == 1 and subs[0].p256dh == "k2"


def test_desuscribir_elimina(db, client):
    _cid, headers = _nuevo_cliente(db, client)
    if not push_service.push_disponible():
        _forzar_vapid(True)
    ep = "https://push.example.com/sub/borrar"
    client.post(f"{API}/cliente/push/suscripcion", json=_sub(ep), headers=headers)

    r = client.delete(f"{API}/cliente/push/suscripcion",
                      params={"endpoint": ep}, headers=headers)
    assert r.status_code == 204
    assert db.scalar(select(PushSuscripcion).where(
        PushSuscripcion.endpoint == ep)) is None
    # Idempotente: borrar de nuevo también da 204
    r = client.delete(f"{API}/cliente/push/suscripcion",
                      params={"endpoint": ep}, headers=headers)
    assert r.status_code == 204


def test_suscripcion_503_sin_vapid(db, client, monkeypatch):
    _forzar_vapid(False, monkeypatch)
    _cid, headers = _nuevo_cliente(db, client)
    r = client.post(f"{API}/cliente/push/suscripcion", json=_sub(), headers=headers)
    assert r.status_code == 503


def _forzar_vapid(activo: bool, monkeypatch=None):
    """Activa/desactiva VAPID en settings (restaura solo si hay monkeypatch)."""
    obj = monkeypatch
    if obj:
        obj.setattr(settings, "VAPID_PUBLIC_KEY", "pub" if activo else "")
        obj.setattr(settings, "VAPID_PRIVATE_KEY", "priv" if activo else "")
    else:
        settings.VAPID_PUBLIC_KEY = settings.VAPID_PUBLIC_KEY or "pub"
        settings.VAPID_PRIVATE_KEY = settings.VAPID_PRIVATE_KEY or "priv"


def test_enviar_sin_subs_ni_vapid_no_falla(db):
    assert push_service.enviar_push_a_cliente(db, 999999, {}) == 0


def test_enviar_limpia_subs_muertas(db, monkeypatch):
    """410/404 del proveedor push → la suscripción se borra."""
    _forzar_vapid(True, monkeypatch)
    db.execute(text(
        "INSERT INTO clientes (nombre, ci, telefono, estado, saldo_puntos,"
        " puntos_congelados) VALUES ('P', 'PUSHX1', '75000000', 'activo', 0, 0)"))
    db.commit()
    cid = db.scalar(select(Cliente.id).where(Cliente.ci == "PUSHX1"))
    db.add(PushSuscripcion(cliente_id=cid, endpoint="https://push.example.com/muerta",
                           p256dh="k", auth="a"))
    db.commit()

    monkeypatch.setattr(push_service, "_webpush", lambda *_a, **_k: 410)
    enviados = push_service.enviar_push_a_cliente(db, cid, {"titulo": "t"})
    assert enviados == 0
    assert db.scalar(select(PushSuscripcion).where(
        PushSuscripcion.endpoint == "https://push.example.com/muerta")) is None


def test_enviar_cuenta_exitosas(db, monkeypatch):
    _forzar_vapid(True, monkeypatch)
    db.execute(text(
        "INSERT INTO clientes (nombre, ci, telefono, estado, saldo_puntos,"
        " puntos_congelados) VALUES ('P', 'PUSHX2', '75000001', 'activo', 0, 0)"))
    db.commit()
    cid = db.scalar(select(Cliente.id).where(Cliente.ci == "PUSHX2"))
    for i in range(2):
        db.add(PushSuscripcion(cliente_id=cid,
                               endpoint=f"https://push.example.com/ok{i}",
                               p256dh="k", auth="a"))
    db.commit()

    monkeypatch.setattr(push_service, "_webpush", lambda *_a, **_k: None)
    assert push_service.enviar_push_a_cliente(db, cid, {"titulo": "t"}) == 2
