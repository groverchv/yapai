"""OTP de cliente (2.º factor), antifraude de puntos y cadena de auditoría."""
import pytest
from app.core.config import settings
from app.models import AuditLog, Cliente, TipoMovimiento, Usuario
from app.services import otp as otp_service
from app.services.puntos import otorgar
from sqlalchemy import select

_CLIENTE = {"telefono": "70000001", "ci": "12345678"}


@pytest.fixture()
def otp_activo(monkeypatch):
    """Activa CLIENTE_OTP_ENABLED y captura los códigos 'enviados'."""
    codigos: list[str] = []
    monkeypatch.setattr(settings, "CLIENTE_OTP_ENABLED", True)
    monkeypatch.setattr(otp_service, "enviar_codigo",
                        lambda telefono, codigo: codigos.append(codigo))
    return codigos


def test_login_cliente_pide_otp(client, otp_activo):
    r = client.post("/api/v1/auth/cliente/login", json=_CLIENTE)
    assert r.status_code == 200
    body = r.json()
    assert body["otp_requerido"] is True
    assert body["tokens"] is None
    assert len(otp_activo) == 1 and len(otp_activo[0]) == 6


def test_otp_codigo_correcto_emite_tokens(client, otp_activo):
    client.post("/api/v1/auth/cliente/login", json=_CLIENTE)
    r = client.post("/api/v1/auth/cliente/otp/verificar",
                    json={**_CLIENTE, "codigo": otp_activo[0]})
    assert r.status_code == 200
    assert r.json()["tokens"]["access_token"]
    assert r.json()["cliente"]["telefono"] == _CLIENTE["telefono"]


def test_otp_codigo_incorrecto_rechaza(client, otp_activo):
    client.post("/api/v1/auth/cliente/login", json=_CLIENTE)
    mal = "000000" if otp_activo[0] != "000000" else "111111"
    r = client.post("/api/v1/auth/cliente/otp/verificar",
                    json={**_CLIENTE, "codigo": mal})
    assert r.status_code == 401


def test_otp_agota_intentos_y_exige_nuevo_login(client, otp_activo):
    client.post("/api/v1/auth/cliente/login", json=_CLIENTE)
    for _ in range(settings.OTP_MAX_INTENTOS):
        mal = "999999" if otp_activo[0] != "999999" else "000000"
        r = client.post("/api/v1/auth/cliente/otp/verificar",
                        json={**_CLIENTE, "codigo": mal})
        assert r.status_code == 401
    # Agotado: ni el código correcto sirve ya
    r = client.post("/api/v1/auth/cliente/otp/verificar",
                    json={**_CLIENTE, "codigo": otp_activo[0]})
    assert r.status_code == 401
    # Nuevo login emite código nuevo que sí funciona
    client.post("/api/v1/auth/cliente/login", json=_CLIENTE)
    r = client.post("/api/v1/auth/cliente/otp/verificar",
                    json={**_CLIENTE, "codigo": otp_activo[-1]})
    assert r.status_code == 200


def test_otp_invalida_codigos_anteriores(client, otp_activo):
    """Re-login genera código nuevo y el viejo queda inservible."""
    client.post("/api/v1/auth/cliente/login", json=_CLIENTE)
    viejo = otp_activo[0]
    client.post("/api/v1/auth/cliente/login", json=_CLIENTE)
    nuevo = otp_activo[-1]
    assert viejo != nuevo or len(otp_activo) == 2
    r = client.post("/api/v1/auth/cliente/otp/verificar",
                    json={**_CLIENTE, "codigo": viejo})
    assert r.status_code == 401
    r = client.post("/api/v1/auth/cliente/otp/verificar",
                    json={**_CLIENTE, "codigo": nuevo})
    assert r.status_code == 200


# --- Antifraude de emisión ---


def test_fraude_alerta_emisor_velocidad(db):
    """Un emisor que otorga más del umbral en 1h dispara alerta_fraude."""
    cliente = db.scalar(select(Cliente).where(Cliente.ci == "12345678"))
    emisor = db.scalar(select(Usuario).where(Usuario.email == "owner@demo.com"))
    umbral = settings.FRAUDE_PUNTOS_EMISOR_HORA
    otorgar(db, cliente, umbral // 2, TipoMovimiento.bonus_manual,
            ejecutado_por=emisor.id, tenant_id=1)
    otorgar(db, cliente, umbral, TipoMovimiento.bonus_manual,
            ejecutado_por=emisor.id, tenant_id=1)
    alertas = db.scalars(
        select(AuditLog).where(AuditLog.accion == "alerta_fraude")
    ).all()
    assert any(a.detalle.get("tipo") == "emisor_velocidad" for a in alertas)


def test_fraude_alerta_cliente_velocidad(db):
    """Un cliente que recibe más del umbral diario dispara alerta."""
    cliente = db.scalar(select(Cliente).where(Cliente.ci == "12345678"))
    umbral = settings.FRAUDE_PUNTOS_CLIENTE_DIA
    otorgar(db, cliente, umbral + 1, TipoMovimiento.ruleta, tenant_id=1)
    alertas = db.scalars(
        select(AuditLog).where(AuditLog.accion == "alerta_fraude")
    ).all()
    assert any(a.detalle.get("tipo") == "cliente_velocidad" for a in alertas)


def test_fraude_emision_normal_no_alerta(db):
    """Emisiones bajo umbral no generan alertas nuevas."""
    antes = db.scalar(
        select(AuditLog).where(AuditLog.accion == "alerta_fraude").order_by(AuditLog.id.desc())
    )
    antes_id = antes.id if antes else 0
    cliente = db.scalar(select(Cliente).where(Cliente.ci == "12345678"))
    otorgar(db, cliente, 10, TipoMovimiento.bonus_manual, tenant_id=1)
    nuevas = db.scalars(
        select(AuditLog).where(AuditLog.accion == "alerta_fraude", AuditLog.id > antes_id)
    ).all()
    assert not nuevas


# --- Cadena de integridad del audit log ---


def test_audit_hash_chain_se_encadena(db):
    """Cada registro nuevo referencia el hash del anterior."""
    from app.services.audit import registrar_audit

    a = registrar_audit(db, None, "test_chain_a", "test", 1)
    db.flush()
    b = registrar_audit(db, None, "test_chain_b", "test", 2)
    db.flush()
    assert a.registro_hash and len(a.registro_hash) == 64
    assert b.prev_hash == a.registro_hash


def test_audit_chain_detecta_edicion(db):
    """Modificar un campo rompe el hash verificable del registro."""
    from app.services.audit import _hash_registro, registrar_audit

    log = registrar_audit(db, None, "test_tamper", "test", 99, {"x": 1})
    db.flush()
    # Simular edición directa en DB: el hash recomputado ya no coincide
    esperado = _hash_registro(log.prev_hash, log.actor_id, "EDITADA",
                            log.entidad, log.entidad_id, log.detalle)
    assert esperado != log.registro_hash


# --- OTP en registro de cliente + cooldown ---


def test_registro_cliente_dos_fases_otp(client, db, otp_activo):
    """El registro en app exige verificar posesión del teléfono (2 fases)."""
    datos = {"nombre": "Nuevo Registro", "telefono": "79991111", "ci": "CI-REG-1"}
    r = client.post("/api/v1/auth/cliente/registro", json=datos)
    assert r.status_code == 200, r.text
    assert r.json()["otp_requerido"] is True and r.json()["tokens"] is None
    assert len(otp_activo) == 1

    # Sin código o código malo → no crea cuenta
    r = client.post("/api/v1/auth/cliente/registro",
                    json={**datos, "codigo": "000000" if otp_activo[0] != "000000" else "111111"})
    assert r.status_code == 401
    r = client.post("/api/v1/auth/cliente/registro",
                    json={**datos, "codigo": otp_activo[0]})
    assert r.status_code == 200, r.text
    assert r.json()["tokens"]["access_token"]
    assert r.json()["cliente"]["telefono"] == "79991111"


def test_otp_cooldown_no_reenvia(client, db, otp_activo, monkeypatch):
    """Dentro del cooldown no se despacha un código nuevo; el vigente sigue
    funcionando."""
    from app.core.config import settings as _s
    monkeypatch.setattr(_s, "OTP_RESEND_COOLDOWN_SEG", 300)
    client.post("/api/v1/auth/cliente/login", json=_CLIENTE)
    assert len(otp_activo) == 1
    # Re-login inmediato: no reenvía (mismo código vigente)
    client.post("/api/v1/auth/cliente/login", json=_CLIENTE)
    assert len(otp_activo) == 1
    r = client.post("/api/v1/auth/cliente/otp/verificar",
                    json={**_CLIENTE, "codigo": otp_activo[0]})
    assert r.status_code == 200
