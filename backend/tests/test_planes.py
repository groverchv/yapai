"""Invariantes del modelo SaaS: signup, trial y límites de plan."""
import uuid

from app.models import Plan, Tenant, Usuario
from sqlalchemy import select
from tests.conftest import login


def _signup(client, **over):
    suf = uuid.uuid4().hex[:8]
    data = {
        "negocio_nombre": f"Negocio {suf}",
        "owner_nombre": "Dueño Test",
        "email": f"owner-{suf}@test.com",
        "password": "TestPass123",
    }
    data.update(over)
    return client.post("/api/v1/auth/signup", json=data)


def test_signup_crea_tenant_en_trial_con_plan_inicial(client, db):
    r = _signup(client)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["aprobado"] is True
    assert body["tokens"]["access_token"]

    tenant = db.scalar(select(Tenant).join(Usuario, Usuario.tenant_id == Tenant.id)
                       .where(Usuario.email == body["usuario"]["email"]))
    assert tenant.plan_id is not None
    assert tenant.trial_fin is not None
    plan = db.get(Plan, tenant.plan_id)
    assert plan.slug == "starter"


def test_signup_email_duplicado_409(client):
    r = _signup(client, email="owner@demo.com")
    assert r.status_code == 409


def test_limite_sucursales_bloquea_con_upgrade_required(client):
    r = _signup(client)
    headers = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}
    r1 = client.post("/api/v1/socio/sucursales", json={"nombre": "Local 1"}, headers=headers)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/socio/sucursales", json={"nombre": "Local 2"}, headers=headers)
    assert r2.status_code == 403
    detalle = r2.json()["detail"]
    assert detalle["code"] == "upgrade_required"
    assert detalle["recurso"] == "sucursales"
    assert detalle["limite"] == 1


def test_ruleta_bloqueada_en_plan_starter(client):
    r = _signup(client)
    headers = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}
    r2 = client.post("/api/v1/socio/ruleta/segmentos",
                     json={"etiqueta": "10 pts", "puntos": 10, "peso": 1}, headers=headers)
    assert r2.status_code == 403
    assert r2.json()["detail"]["code"] == "upgrade_required"


def test_upgrade_por_admin_desbloquea(client, admin_headers):
    r = _signup(client)
    headers = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}
    tenant_id = r.json()["usuario"]["tenant_id"]

    pro = client.get("/api/v1/admin/planes", headers=admin_headers)
    pro_id = next(p["id"] for p in pro.json() if p["slug"] == "pro")
    r_up = client.patch(f"/api/v1/admin/socios/{tenant_id}/plan",
                        json={"plan_id": pro_id}, headers=admin_headers)
    assert r_up.status_code == 200
    assert r_up.json()["plan"] == "Pro"

    for i in range(2):
        rs = client.post("/api/v1/socio/sucursales",
                         json={"nombre": f"Local {i}"}, headers=headers)
        assert rs.status_code == 201
    rs_ruleta = client.post("/api/v1/socio/ruleta/segmentos",
                            json={"etiqueta": "5 pts", "puntos": 5, "peso": 1}, headers=headers)
    assert rs_ruleta.status_code == 201


def test_socio_plan_reporta_uso_y_trial(client):
    r = _signup(client)
    headers = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}
    r2 = client.get("/api/v1/socio/plan", headers=headers)
    assert r2.status_code == 200
    d = r2.json()
    assert d["plan_slug"] == "starter"
    assert d["en_trial"] is True
    assert d["dias_trial"] in (13, 14)
    assert d["uso"]["empleados"] == 1


def test_planes_publicos_sin_auth(client):
    r = client.get("/api/v1/auth/planes")
    assert r.status_code == 200
    slugs = [p["slug"] for p in r.json()]
    assert "starter" in slugs and "pro" in slugs


def test_signup_rate_limit(client):
    # signup_limiter: 5/hora por IP — el 6to signup consecutivo debe 429
    codigos = {_signup(client).status_code for _ in range(6)}
    assert 429 in codigos


def test_login_owner_signup_funciona(client):
    r = _signup(client)
    email = r.json()["usuario"]["email"]
    headers = login(client, email, "TestPass123")
    assert "Bearer" in headers["Authorization"]


def test_onboarding_checklist_para_tenant_nuevo(client):
    r = _signup(client)
    headers = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}
    r2 = client.get("/api/v1/socio/onboarding", headers=headers)
    assert r2.status_code == 200
    d = r2.json()
    claves = [p["clave"] for p in d["pasos"]]
    assert claves == ["sucursal", "pantalla", "premio", "empleado", "primer_giro"]
    assert all(p["hecho"] is False for p in d["pasos"])
    assert d["completados"] == 0 and d["completado"] is False


def test_qr_pantalla_devuelve_svg_y_url(client, owner_headers):
    r = client.get("/api/v1/socio/sucursales", headers=owner_headers)
    pantalla_id = r.json()[0]["pantallas"][0]["id"]
    r2 = client.get(f"/api/v1/socio/sucursales/pantallas/{pantalla_id}/qr", headers=owner_headers)
    assert r2.status_code == 200
    d = r2.json()
    assert "<svg" in d["svg"]
    assert "/kiosco/" in d["url"]


def test_kpis_incluyen_tiempo_a_primer_giro(client, admin_headers):
    r = client.get("/api/v1/admin/socios/1/rendimiento", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["horas_a_primer_giro"] is not None
    r2 = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert "ttfs_medio_h" in r2.json()["kpis"]
