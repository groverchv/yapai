"""Sprint C: comprobante manual, /status, funnel, sesiones del cliente, demo."""
import pytest
from app.core.config import settings
from app.models import (
    EstadoFactura,
    FacturaPlan,
    Pantalla,
    RefreshToken,
    RolUsuario,
    SujetoTipo,
    Usuario,
)
from sqlalchemy import select
from tests.conftest import login
from tests.test_facturacion import _tenant_facturable

API = "/api/v1"


# --- C2: /status público ---

def test_status_publico_sin_auth(client):
    r = client.get("/status")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "operational"


# --- C1: comprobante manual ---

def _tenant_con_factura(client, db, admin_headers, suf: str):
    """Tenant facturable (plan pago, trial vencido) + factura emitida."""
    t = _tenant_facturable(client, db)
    r = client.post(f"{API}/admin/facturacion/generar", headers=admin_headers)
    assert r.status_code == 201, r.text
    f = db.scalar(select(FacturaPlan).where(FacturaPlan.tenant_id == t.id)
                  .order_by(FacturaPlan.id.desc()))
    assert f is not None and f.estado == EstadoFactura.pendiente
    return t, f


def _owner_de(client, tenant_id: int, db) -> dict:
    """Headers del owner de un tenant dado (busca su email en la BD)."""
    email = db.scalar(select(Usuario.email).where(
        Usuario.tenant_id == tenant_id, Usuario.rol == RolUsuario.owner))
    return login(client, email, "TestPass12345")


def test_subir_comprobante_y_admin_lo_ve(client, db, admin_headers):
    t, f = _tenant_con_factura(client, db, admin_headers, "comp1")
    h = _owner_de(client, t.id, db)
    r = client.post(f"{API}/socio/facturacion/{f.id}/comprobante",
                    json={"url": "https://res.cloudinary.com/x/recibo.jpg"},
                    headers=h)
    assert r.status_code == 200, r.text

    # El admin ve el link en el listado
    r2 = client.get(f"{API}/admin/facturacion?size=200", headers=admin_headers)
    assert r2.status_code == 200
    item = next(i for i in r2.json()["items"] if i["id"] == f.id)
    assert item["comprobante_url"].endswith("recibo.jpg")

    # El admin confirma manualmente el pago
    r3 = client.post(f"{API}/admin/facturacion/{f.id}/pagar",
                     json={"metodo": "transferencia", "referencia": "TRX-1"},
                     headers=admin_headers)
    assert r3.status_code == 200
    assert r3.json()["estado"] == "pagada"


def test_comprobante_factura_ajena_404(client, db, admin_headers):
    """Un socio no puede subir comprobante a factura de otro tenant."""
    t, f = _tenant_con_factura(client, db, admin_headers, "comp2")
    h_otro = _owner_de(client, t.id, db)  # owner del tenant A
    # Factura del tenant B (demo u otro)
    t2, f2 = _tenant_con_factura(client, db, admin_headers, "comp3")
    r = client.post(f"{API}/socio/facturacion/{f2.id}/comprobante",
                    json={"url": "https://x/r.jpg"},
                    headers=h_otro)
    assert r.status_code == 404


def test_comprobante_sin_auth_401(client, db, admin_headers):
    t, f = _tenant_con_factura(client, db, admin_headers, "comp4")
    client.cookies.clear()  # el jar retiene la cookie del login previo
    r = client.post(f"{API}/socio/facturacion/{f.id}/comprobante",
                    json={"url": "https://x/r.jpg"})
    assert r.status_code == 401


# --- C3: funnel ---

def test_funnel_admin(client, admin_headers):
    r = client.get(f"{API}/admin/funnel", headers=admin_headers)
    assert r.status_code == 200
    etapas = r.json()
    assert len(etapas) == 5
    assert etapas[0]["nombre"] == "Signups"
    assert etapas[0]["cantidad"] >= 1
    for e in etapas:
        assert 0 <= e["porcentaje"] <= 100


def test_funnel_sin_admin_403(client, owner_headers):
    assert client.get(f"{API}/admin/funnel", headers=owner_headers).status_code == 403


# --- C4: sesiones del cliente ---

def _cliente_tokens(client):
    """Login directo — devuelve access + refresh (el helper de invariantes solo da headers)."""
    r = client.post(f"{API}/auth/cliente/login",
                    json={"ci": "12345678", "telefono": "70000001"})
    assert r.status_code == 200, r.text
    return r.json()["tokens"]


def test_listar_y_revocar_sesiones(client):
    tokens = _cliente_tokens(client)
    h = {"Authorization": f"Bearer {tokens['access_token']}"}

    r = client.get(f"{API}/cliente/me/sesiones", headers=h)
    assert r.status_code == 200
    sesiones = r.json()
    assert len(sesiones) >= 1
    sid = sesiones[0]["id"]

    r2 = client.delete(f"{API}/cliente/me/sesiones/{sid}", headers=h)
    assert r2.status_code == 200

    # El refresh revocado ya no rota
    r3 = client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r3.status_code == 401


def test_revocar_sesion_ajena_404(client, db):
    tokens = _cliente_tokens(client)
    h = {"Authorization": f"Bearer {tokens['access_token']}"}
    ajena = db.scalar(select(RefreshToken.id).where(
        RefreshToken.sujeto_tipo == SujetoTipo.usuario))
    if not ajena:
        pytest.skip("sin refresh de usuario")
    assert client.delete(f"{API}/cliente/me/sesiones/{ajena}", headers=h).status_code == 404


def test_cerrar_todas_las_sesiones(client):
    tokens = _cliente_tokens(client)
    h = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = client.delete(f"{API}/cliente/me/sesiones", headers=h)
    assert r.status_code == 200
    assert client.get(f"{API}/cliente/me/sesiones", headers=h).json() == []


# --- C5: demo pública ---

def test_demo_sin_config_no_disponible(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_DEVICE_TOKEN", "")
    r = client.get(f"{API}/auth/demo")
    assert r.status_code == 200
    assert r.json()["disponible"] is False


def test_demo_disponible_y_kiosco_sin_pin(client, db, monkeypatch):
    pantalla = db.scalar(select(Pantalla).where(Pantalla.device_token == "kiosco-demo-001"))
    if not pantalla:
        pytest.skip("sin pantalla demo en seed")
    pantalla.habilitada_hasta = None  # simular expirada — el bypass demo la ignora
    db.flush()
    monkeypatch.setattr(settings, "DEMO_DEVICE_TOKEN", "kiosco-demo-001")

    r = client.get(f"{API}/auth/demo")
    assert r.json()["disponible"] is True
    assert r.json()["device_token"] == "kiosco-demo-001"

    r2 = client.get(f"{API}/kiosco/kiosco-demo-001/config")
    assert r2.status_code == 200, r2.text
    assert r2.json()["comercio"]
