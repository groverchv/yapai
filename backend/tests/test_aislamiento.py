"""Aislamiento multi-tenant: un owner nunca lee/escribe recursos de otro tenant.

Cada recurso se crea con el owner A (signup propio) y se intenta tocar con el
owner B — la API debe responder 404 (no existe) o 403, nunca 200 con datos.
"""
import uuid

import pytest


def _signup_owner(client, etiqueta: str):
    suf = uuid.uuid4().hex[:8]
    r = client.post("/api/v1/auth/signup", json={
        "negocio_nombre": f"{etiqueta} {suf}",
        "owner_nombre": f"Dueño {etiqueta}",
        "email": f"{etiqueta.lower()}-{suf}@test.com",
        "password": "TestPass12345",
    })
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}


@pytest.fixture()
def owner_a(client):
    return _signup_owner(client, "TenantA")


@pytest.fixture()
def owner_b(client):
    return _signup_owner(client, "TenantB")


def _crear_premio(client, headers):
    r = client.post("/api/v1/socio/premios", headers=headers,
                    json={"nombre": "Premio A", "costo_puntos": 10})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _crear_sucursal(client, headers):
    r = client.post("/api/v1/socio/sucursales", headers=headers,
                    json={"nombre": "Sucursal A"})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _crear_campana(client, headers):
    r = client.post("/api/v1/socio/campanas", headers=headers, json={
        "nombre": "Campaña A", "multiplicador": 2,
        "inicio": "2030-01-01T00:00:00Z", "fin": "2030-01-31T00:00:00Z",
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _crear_empleado(client, headers):
    suf = uuid.uuid4().hex[:8]
    r = client.post("/api/v1/socio/empleados", headers=headers,
                    json={"nombre": "Cajero A", "email": f"cajero-{suf}@test.com"})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_premio_no_visible_ni_editable_por_otro_tenant(client, owner_a, owner_b):
    pid = _crear_premio(client, owner_a)

    for r in (
        client.patch(f"/api/v1/socio/premios/{pid}", headers=owner_b, json={"nombre": "hackeado"}),
        client.post(f"/api/v1/socio/premios/{pid}/desactivar", headers=owner_b),
        client.post(f"/api/v1/socio/premios/{pid}/activar", headers=owner_b),
    ):
        assert r.status_code in (403, 404), r.text

    # El listado del otro tenant no lo contiene
    lista = client.get("/api/v1/socio/premios", headers=owner_b).json()
    assert all(p["id"] != pid for p in lista)


def test_sucursal_no_editable_por_otro_tenant(client, owner_a, owner_b):
    sid = _crear_sucursal(client, owner_a)

    assert client.patch(f"/api/v1/socio/sucursales/{sid}", headers=owner_b,
                        json={"nombre": "hackeado"}).status_code in (403, 404)
    assert client.post(f"/api/v1/socio/sucursales/{sid}/suspender",
                       headers=owner_b).status_code in (403, 404)


def test_campana_no_editable_por_otro_tenant(client, owner_a, owner_b):
    cid = _crear_campana(client, owner_a)

    assert client.patch(f"/api/v1/socio/campanas/{cid}", headers=owner_b,
                        json={"nombre": "hackeada"}).status_code in (403, 404)
    assert client.delete(f"/api/v1/socio/campanas/{cid}",
                         headers=owner_b).status_code in (403, 404)


def test_empleado_no_editable_por_otro_tenant(client, owner_a, owner_b):
    eid = _crear_empleado(client, owner_a)

    assert client.patch(f"/api/v1/socio/empleados/{eid}", headers=owner_b,
                        json={"nombre": "hackeado"}).status_code in (403, 404)
    assert client.post(f"/api/v1/socio/empleados/{eid}/suspender",
                       headers=owner_b).status_code in (403, 404)
    assert client.post(f"/api/v1/socio/empleados/{eid}/reenviar",
                       headers=owner_b).status_code in (403, 404)


def test_recursos_protegidos_exigen_rol_owner(client, owner_a, cajero_headers):
    """El cajero (rol menor) no puede administrar recursos del tenant."""
    assert client.get("/api/v1/socio/empleados", headers=cajero_headers).status_code == 403
    assert client.get("/api/v1/socio/premios", headers=cajero_headers).status_code == 403


def test_superadmin_no_puede_usar_routers_de_socio(client, admin_headers):
    """El superadmin opera por /admin, no por los routers de tenant."""
    assert client.get("/api/v1/socio/premios", headers=admin_headers).status_code in (403, 404)
