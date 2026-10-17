"""Invariantes de billing: emisión idempotente, pago, mora y suspensión por impago."""
import uuid
from datetime import timedelta

from sqlalchemy import select

from app.core.security import utcnow
from app.jobs.facturacion import ejecutar_una_vez
from app.models import EstadoFactura, EstadoTenant, FacturaPlan, Plan, Tenant, Usuario
from app.services.billing import estado_cuenta


def _tenant_facturable(client, db) -> Tenant:
    """Crea un tenant nuevo vía signup, le asigna el plan Pro y le vence el trial
    para que sea facturable. Cada test usa un tenant distinto (la factura es
    única por tenant+período)."""
    suf = uuid.uuid4().hex[:8]
    r = client.post("/api/v1/auth/signup", json={
        "negocio_nombre": f"Negocio {suf}",
        "owner_nombre": "Dueño Test",
        "email": f"owner-{suf}@test.com",
        "password": "TestPass123",
    })
    assert r.status_code == 201, r.text
    tenant = db.scalar(
        select(Tenant).join(Usuario, Usuario.tenant_id == Tenant.id)
        .where(Usuario.email == f"owner-{suf}@test.com")
    )
    tenant.plan_id = db.scalar(select(Plan.id).where(Plan.slug == "pro"))
    tenant.trial_fin = utcnow() - timedelta(days=1)
    db.commit()
    return tenant


def _factura_de(db, tenant_id: int) -> FacturaPlan | None:
    return db.scalar(
        select(FacturaPlan).where(FacturaPlan.tenant_id == tenant_id)
        .order_by(FacturaPlan.id.desc())
    )


def test_generar_facturas_emite_y_es_idempotente(client, db, admin_headers):
    """Emite para tenants con plan pago y trial vencido; no duplica por período."""
    t = _tenant_facturable(client, db)
    r = client.post("/api/v1/admin/facturacion/generar", headers=admin_headers)
    assert r.status_code == 201, r.text
    f = _factura_de(db, t.id)
    assert f is not None and f.estado == EstadoFactura.pendiente
    assert f.plan_nombre == "Pro" and float(f.monto) > 0
    assert f.vence_en is not None

    n_antes = len(db.scalars(select(FacturaPlan)).all())
    r2 = client.post("/api/v1/admin/facturacion/generar", headers=admin_headers)
    assert r2.json()["emitidas"] == 0
    assert len(db.scalars(select(FacturaPlan)).all()) == n_antes


def test_no_factura_en_trial_ni_plan_gratis(client, db, admin_headers):
    """Tenant recién registrado (trial + Starter) no recibe factura."""
    suf = uuid.uuid4().hex[:8]
    r = client.post("/api/v1/auth/signup", json={
        "negocio_nombre": f"Trial {suf}", "owner_nombre": "Owner Trial",
        "email": f"trial-{suf}@test.com", "password": "TestPass123",
    })
    assert r.status_code == 201, r.text
    client.post("/api/v1/admin/facturacion/generar", headers=admin_headers)
    tenant = db.scalar(
        select(Tenant).join(Usuario, Usuario.tenant_id == Tenant.id)
        .where(Usuario.email == f"trial-{suf}@test.com")
    )
    assert _factura_de(db, tenant.id) is None


def test_pagar_y_anular_factura(client, db, admin_headers):
    t = _tenant_facturable(client, db)
    client.post("/api/v1/admin/facturacion/generar", headers=admin_headers)
    f = _factura_de(db, t.id)

    r = client.post(f"/api/v1/admin/facturacion/{f.id}/pagar",
                    json={"metodo": "qr", "referencia": "REF-1"}, headers=admin_headers)
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "pagada"
    assert r.json()["pagada_en"] is not None

    # Pagar de nuevo es idempotente; anular una pagada da conflicto
    assert client.post(f"/api/v1/admin/facturacion/{f.id}/pagar",
                       json={"metodo": "qr"}, headers=admin_headers).status_code == 200
    assert client.post(f"/api/v1/admin/facturacion/{f.id}/anular",
                       headers=admin_headers).status_code == 409


def test_socio_ve_estado_de_cuenta_y_facturas(client, db, admin_headers):
    t = _tenant_facturable(client, db)
    owner = db.scalar(select(Usuario).where(
        Usuario.tenant_id == t.id, Usuario.rol == "owner"))
    from tests.conftest import login
    headers = login(client, owner.email, "TestPass123")

    client.post("/api/v1/admin/facturacion/generar", headers=admin_headers)
    r = client.get("/api/v1/socio/facturacion", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["estado"] == "pendiente"
    assert len(body["facturas"]) == 1

    fid = body["facturas"][0]["id"]
    client.post(f"/api/v1/admin/facturacion/{fid}/pagar",
                json={"metodo": "transferencia"}, headers=admin_headers)
    assert client.get("/api/v1/socio/facturacion", headers=headers).json()["estado"] == "al_dia"


def test_job_marca_vencidas(client, db, admin_headers):
    """El job convierte pendiente→vencida cuando pasa vence_en."""
    t = _tenant_facturable(client, db)
    client.post("/api/v1/admin/facturacion/generar", headers=admin_headers)
    f = _factura_de(db, t.id)
    f.vence_en = utcnow() - timedelta(days=1)
    db.commit()

    res = ejecutar_una_vez()
    assert res["vencidas"] >= 1
    db.expire_all()
    assert _factura_de(db, t.id).estado == EstadoFactura.vencida
    assert estado_cuenta(db, t) == "vencida"


def test_suspension_automatica_por_impago(client, db, admin_headers):
    """Factura vencida más allá de la gracia → tenant suspendido."""
    t = _tenant_facturable(client, db)
    client.post("/api/v1/admin/facturacion/generar", headers=admin_headers)
    f = _factura_de(db, t.id)
    f.vence_en = utcnow() - timedelta(days=30)
    f.estado = EstadoFactura.vencida
    db.commit()

    res = ejecutar_una_vez()
    assert t.id in res["suspendidos"]
    db.expire_all()
    assert db.get(Tenant, t.id).estado == EstadoTenant.suspendido


def test_facturacion_estado_en_detalle_socio(client, db, admin_headers):
    t = _tenant_facturable(client, db)
    client.post("/api/v1/admin/facturacion/generar", headers=admin_headers)
    r = client.get(f"/api/v1/admin/socios/{t.id}", headers=admin_headers)
    assert r.status_code == 200, r.text
    assert r.json()["facturacion_estado"] == "pendiente"
