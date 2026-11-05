"""Invariantes de comunicados: CRUD del socio, feed del cliente, aislamiento."""
import uuid
from datetime import timedelta

from app.core.security import utcnow
from app.models import Tenant, Usuario
from sqlalchemy import select

_IMG = "https://res.cloudinary.com/x/image/upload/v1/oferta.png"


def _crear(client, headers, **over):
    data = {"titulo": "Oferta de prueba", "imagen_url": _IMG}
    data.update(over)
    return client.post("/api/v1/socio/comunicados", json=data, headers=headers)


def _cliente_headers(client):
    r = client.post("/api/v1/auth/cliente/login",
                    json={"telefono": "70000001", "ci": "12345678"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}


def _feed_ids(client, headers):
    r = client.get("/api/v1/cliente/comunicados?size=50", headers=headers)
    assert r.status_code == 200, r.text
    return [c["id"] for c in r.json()["items"]]


def _otro_owner(client):
    suf = uuid.uuid4().hex[:8]
    r = client.post("/api/v1/auth/signup", json={
        "negocio_nombre": f"Otro {suf}", "owner_nombre": "Otro Dueño",
        "email": f"otro-{suf}@test.com", "password": "TestPass123",
    })
    assert r.status_code == 201, r.text
    email = f"otro-{suf}@test.com"
    lr = client.post("/api/v1/auth/login",
                     json={"email": email, "password": "TestPass123"})
    return {"Authorization": f"Bearer {lr.json()['tokens']['access_token']}"}


def test_crud_comunicado(client, owner_headers):
    r = _crear(client, owner_headers, descripcion="Solo hoy")
    assert r.status_code == 201, r.text
    c = r.json()
    assert c["estado"] == "borrador" and c["publicado_en"] is None

    lista = client.get("/api/v1/socio/comunicados", headers=owner_headers).json()
    assert any(x["id"] == c["id"] for x in lista)

    r2 = client.patch(f"/api/v1/socio/comunicados/{c['id']}",
                      json={"titulo": "Oferta editada"}, headers=owner_headers)
    assert r2.json()["titulo"] == "Oferta editada"

    r3 = client.post(f"/api/v1/socio/comunicados/{c['id']}/publicar",
                     headers=owner_headers)
    assert r3.json()["estado"] == "publicado"
    assert r3.json()["publicado_en"] is not None

    r4 = client.post(f"/api/v1/socio/comunicados/{c['id']}/archivar",
                     headers=owner_headers)
    assert r4.json()["estado"] == "archivado"

    assert client.delete(f"/api/v1/socio/comunicados/{c['id']}",
                         headers=owner_headers).status_code == 204


def test_feed_solo_publicados_vigentes(client, db, owner_headers):
    """Borrador, archivado y vencido quedan fuera; publicado vigente entra."""
    ch = _cliente_headers(client)
    c_borrador = _crear(client, owner_headers, titulo="Borrador x").json()
    c_pub = _crear(client, owner_headers, titulo="Publicada x").json()
    client.post(f"/api/v1/socio/comunicados/{c_pub['id']}/publicar",
                headers=owner_headers)
    c_venc = _crear(client, owner_headers, titulo="Vencida x",
                    vigencia_hasta=(utcnow() - timedelta(days=1)).isoformat()).json()
    client.post(f"/api/v1/socio/comunicados/{c_venc['id']}/publicar",
                headers=owner_headers)

    ids = _feed_ids(client, ch)
    assert c_pub["id"] in ids
    assert c_borrador["id"] not in ids
    assert c_venc["id"] not in ids

    item = next(c for c in client.get("/api/v1/cliente/comunicados",
                                      headers=ch).json()["items"]
                if c["id"] == c_pub["id"])
    assert item["comercio"] and "imagen_url" in item and "logo_url" in item

    client.post(f"/api/v1/socio/comunicados/{c_pub['id']}/archivar",
                headers=owner_headers)
    assert c_pub["id"] not in _feed_ids(client, ch)


def test_aislamiento_tenant(client, db, owner_headers):
    """Un socio no puede tocar comunicados de otro tenant."""
    c = _crear(client, owner_headers, titulo="Privado x").json()
    otro = _otro_owner(client)
    assert client.patch(f"/api/v1/socio/comunicados/{c['id']}",
                        json={"titulo": "Intento ajeno"},
                        headers=otro).status_code == 404
    for url in [
        f"/api/v1/socio/comunicados/{c['id']}/publicar",
        f"/api/v1/socio/comunicados/{c['id']}/archivar",
    ]:
        r = client.post(url, headers=otro)
        assert r.status_code == 404, (url, r.status_code)
    assert client.delete(f"/api/v1/socio/comunicados/{c['id']}",
                         headers=otro).status_code == 404

    lista_otro = client.get("/api/v1/socio/comunicados", headers=otro).json()
    assert all(x["id"] != c["id"] for x in lista_otro)


def test_premio_de_otro_tenant_rechazado(client, db, owner_headers):
    """premio_id ajeno → 400, no vincula promos de la competencia."""
    _otro_owner(client)
    otro_tenant = db.scalar(
        select(Tenant).join(Usuario, Usuario.tenant_id == Tenant.id)
        .where(Usuario.email.like("otro-%@test.com"))
    )
    from app.models import EstadoPremio, Premio
    p = Premio(tenant_id=otro_tenant.id, nombre="Ajeno", costo_puntos=10,
               estado=EstadoPremio.activo)
    db.add(p)
    db.commit()
    r = _crear(client, owner_headers, titulo="Trampa x", premio_id=p.id)
    assert r.status_code == 400


def test_firma_upload_requiere_owner(client, owner_headers):
    """Sin auth → 401/403; con owner → 200 (Cloudinary configurado) o 503."""
    r = client.post("/api/v1/socio/comunicados/uploads/firma")
    assert r.status_code in (401, 403)
    r2 = client.post("/api/v1/socio/comunicados/uploads/firma?carpeta=premios",
                     headers=owner_headers)
    assert r2.status_code in (200, 503)
    if r2.status_code == 200:
        body = r2.json()
        assert body["signature"] and body["cloud_name"]
        assert "/premios" in body["folder"]

    r3 = client.post("/api/v1/socio/comunicados/uploads/firma?carpeta=../evil",
                     headers=owner_headers)
    assert r3.status_code == 422  # pattern de carpeta rechaza path traversal
