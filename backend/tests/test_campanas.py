"""Invariantes del motor de marketing: multiplicador, referidos, vigencia, inactivos."""
import uuid
from datetime import timedelta

from app.core.security import utcnow
from app.models import Campana, Cliente, MovimientoPuntos, Pantalla, Premio, TipoMovimiento
from sqlalchemy import select


def _limpiar_campanas(db):
    db.query(Campana).delete()
    db.commit()


def _campana(client, headers, **over):
    ahora = utcnow()
    data = {
        "nombre": "x2 test", "multiplicador": 2,
        "inicio": (ahora - timedelta(days=1)).isoformat(),
        "fin": (ahora + timedelta(days=30)).isoformat(),
    }
    data.update(over)
    return client.post("/api/v1/socio/campanas", json=data, headers=headers)


def _registrar(cliente_client, **kw):
    """Registro vía kiosco con token demo; kw sobreescribe campos."""
    data = {
        "nombre": f"C {uuid.uuid4().hex[:6]}", "ci": uuid.uuid4().hex[:8],
        "telefono": f"7{uuid.uuid4().int % 10**7:07d}", "acepto_terminos": True,
    }
    data.update(kw)
    return cliente_client.post("/api/v1/kiosco/kiosco-demo-001/registro", json=data)


def _habilitar_pantalla(db):
    """Habilita la pantalla demo directo en DB (el flujo PIN ya se prueba
    en test_invariantes)."""
    p = db.scalar(select(Pantalla).where(Pantalla.device_token == "kiosco-demo-001"))
    p.habilitada_hasta = utcnow() + timedelta(hours=8)
    db.commit()


def test_crud_campanas(client, owner_headers):
    r = _campana(client, owner_headers)
    assert r.status_code == 201, r.text
    c = r.json()
    assert c["vigente"] is True and c["multiplicador"] == 2

    lista = client.get("/api/v1/socio/campanas", headers=owner_headers).json()
    assert len(lista) == 1

    r2 = client.patch(f"/api/v1/socio/campanas/{c['id']}",
                      json={"activa": False}, headers=owner_headers)
    assert r2.json()["activa"] is False

    assert client.delete(f"/api/v1/socio/campanas/{c['id']}",
                         headers=owner_headers).status_code == 204
    assert client.get("/api/v1/socio/campanas", headers=owner_headers).json() == []


def test_campana_multiplica_registro_y_ruleta(client, db, owner_headers):
    """x2 vigente → registro da el doble y ruleta también; el ledger lo registra."""
    _limpiar_campanas(db)
    _campana(client, owner_headers)
    _habilitar_pantalla(db)

    r = _registrar(client)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["puntos_otorgados"] == 600  # 300 base × 2
    assert body["multiplicador"] == 2 and body["campana"] == "x2 test"

    g = client.post("/api/v1/kiosco/kiosco-demo-001/ruleta/girar",
                    json={"cliente_id": body["cliente_id"]}).json()
    assert g["multiplicador"] == 2


def test_campana_no_vigente_no_multiplica(client, db, owner_headers):
    _limpiar_campanas(db)
    ahora = utcnow()
    _campana(client, owner_headers, nombre="futura",
             inicio=(ahora + timedelta(days=5)).isoformat(),
             fin=(ahora + timedelta(days=10)).isoformat())
    _habilitar_pantalla(db)
    r = _registrar(client)
    assert r.json()["multiplicador"] == 1
    assert r.json()["puntos_otorgados"] == 300


def test_referido_otorga_bonus_al_referidor(client, db, owner_headers):
    _habilitar_pantalla(db)
    r1 = _registrar(client)
    assert r1.status_code == 201
    codigo = db.scalar(select(Cliente.codigo_referido)
                       .where(Cliente.id == r1.json()["cliente_id"]))
    assert codigo

    r2 = _registrar(client, codigo_referido=codigo)
    assert r2.status_code == 201
    assert r2.json()["referido_bonus"] == 100

    referidor = db.get(Cliente, r1.json()["cliente_id"])
    db.expire(referidor)
    mov = db.scalar(select(MovimientoPuntos).where(
        MovimientoPuntos.cliente_id == referidor.id,
        MovimientoPuntos.tipo == TipoMovimiento.referido,
    ))
    assert mov and mov.puntos == 100


def test_premio_vencido_no_canjeable_ni_visible(client, db, owner_headers):
    """vigencia_hasta pasada → fuera del catálogo del cliente y bloqueado al canjear."""
    premio = db.scalar(select(Premio).where(Premio.id == 1))
    premio.vigencia_hasta = utcnow() - timedelta(days=1)
    db.commit()

    cli = client.post("/api/v1/auth/cliente/login",
                      json={"telefono": "70000001", "ci": "12345678"})
    assert cli.status_code == 200
    h = {"Authorization": f"Bearer {cli.json()['tokens']['access_token']}"}
    catalogo = client.get("/api/v1/cliente/comercios/1/premios", headers=h).json()
    assert all(p["id"] != premio.id for p in catalogo)

    pase = client.post("/api/v1/cliente/pases", json={"premio_id": premio.id}, headers=h)
    assert pase.status_code == 400
    assert "venció" in pase.json()["detail"]

    premio.vigencia_hasta = None  # restaurar para otros tests
    db.commit()


def test_inactivos_segmento(client, db, owner_headers):
    """Devuelve clientes sin actividad reciente; 0 con dias muy alto."""
    todos = client.get("/api/v1/socio/campanas/inactivos?dias=0&",
                       headers=owner_headers)
    # dias=0 es inválido (ge=1)
    assert todos.status_code == 422
    r = client.get("/api/v1/socio/campanas/inactivos?dias=365",
                   headers=owner_headers)
    assert r.status_code == 200
    csv_r = client.get("/api/v1/socio/campanas/inactivos.csv?dias=365",
                       headers=owner_headers)
    assert csv_r.status_code == 200
    assert "telefono" in csv_r.text.splitlines()[0]
