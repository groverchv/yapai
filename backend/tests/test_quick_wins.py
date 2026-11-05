"""Tests de los quick wins UX: próximo premio, puntos por comercio,
consentimiento de kiosco y KPIs del período espejo.

Los clientes de prueba se crean por test (como en test_invariantes) para no
depender del saldo del cliente demo que otros tests pueden tocar.
"""
import uuid
from datetime import timedelta

from app.core.security import utcnow
from app.models import (
    Cliente,
    EstadoPremio,
    MovimientoPuntos,
    Pantalla,
    Premio,
    Tenant,
    TipoMovimiento,
)
from sqlalchemy import select, text

API = "/api/v1"
_counter = {"n": 0}


def _cliente_login(client, ci, telefono):
    r = client.post(f"{API}/auth/cliente/login",
                    json={"ci": ci, "telefono": telefono})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}


def _nuevo_cliente(db, client, saldo=0):
    """Cliente aislado con saldo directo; devuelve (cliente_id, headers)."""
    _counter["n"] += 1
    n = _counter["n"]
    ci, tel = f"QW{n:08d}", f"76{n:06d}"
    db.execute(text(
        "INSERT INTO clientes (nombre, ci, telefono, estado, saldo_puntos,"
        " puntos_congelados) VALUES (:nm, :ci, :tel, 'activo', :s, 0)"),
        {"nm": f"QW {n}", "ci": ci, "tel": tel, "s": saldo})
    db.commit()
    cid = db.scalar(select(Cliente.id).where(Cliente.ci == ci))
    return cid, _cliente_login(client, ci, tel)


def _tenant_demo_id(db):
    return db.scalar(select(Premio.tenant_id).where(
        Premio.nombre == "Pizza familiar gratis"))


def _tenant_con_premio(db, costo):
    """Tenant + premio aislados: los tests de próximo premio no deben depender
    del catálogo demo (otros tests consumen su stock / cambian su estado)."""
    _counter["n"] += 1
    n = _counter["n"]
    t = Tenant(nombre_comercial=f"QW Store {n}", nit_rut=f"QW{n:010d}")
    db.add(t)
    db.flush()
    p = Premio(tenant_id=t.id, nombre=f"Premio QW {n}", costo_puntos=costo,
               stock_limitado=False)
    db.add(p)
    db.commit()
    return t.id, p


def _movimiento(db, cliente_id, tenant_id, puntos, tipo=TipoMovimiento.registro,
                cuando=None):
    m = MovimientoPuntos(cliente_id=cliente_id, tenant_id=tenant_id,
                         tipo=tipo, puntos=puntos)
    if cuando:
        m.created_at = cuando
    db.add(m)
    db.commit()
    return m


def _habilitar_pantalla(db):
    p = db.scalar(select(Pantalla).where(Pantalla.device_token == "kiosco-demo-001"))
    p.habilitada_hasta = utcnow() + timedelta(hours=8)
    db.commit()


# ---------- próximo-premio ----------

def test_proximo_premio_inalcanzable(db, client):
    """Saldo 400 → la meta más cercana en su comercio cuesta 500: faltante 100."""
    tid, premio = _tenant_con_premio(db, 500)
    cid, headers = _nuevo_cliente(db, client, saldo=400)
    _movimiento(db, cid, tid, 300)

    r = client.get(f"{API}/cliente/proximo-premio", headers=headers)
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["premio_id"] == premio.id
    assert b["costo_puntos"] == 500
    assert b["saldo"] == 400 and b["faltante"] == 100
    assert b["alcanzable"] is False
    assert b["tenant_id"] == tid and b["comercio"]


def test_proximo_premio_alcanzable(db, client):
    """Saldo 600 → puede pagar el premio de 500: devuelve el más caro alcanzable."""
    tid, premio = _tenant_con_premio(db, 500)
    cid, headers = _nuevo_cliente(db, client, saldo=600)
    _movimiento(db, cid, tid, 50)

    b = client.get(f"{API}/cliente/proximo-premio", headers=headers).json()
    assert b["alcanzable"] is True and b["faltante"] == 0
    assert b["premio_id"] == premio.id


def test_proximo_premio_sin_premios_404(db, client):
    """Sin premios activos en ningún tenant → 404."""
    cid, headers = _nuevo_cliente(db, client, saldo=0)
    _movimiento(db, cid, _tenant_demo_id(db), 10)

    premios = db.scalars(select(Premio)).all()
    estados = [(p.id, p.estado) for p in premios]
    try:
        for p in premios:
            p.estado = EstadoPremio.inactivo
        db.commit()
        r = client.get(f"{API}/cliente/proximo-premio", headers=headers)
        assert r.status_code == 404
    finally:
        for p in premios:
            p.estado = dict(estados)[p.id]
        db.commit()


# ---------- puntos_ganados en directorio ----------

def test_directorio_puntos_ganados(db, client):
    """El directorio expone los puntos que el cliente ganó por comercio."""
    tid = _tenant_demo_id(db)
    cid, headers = _nuevo_cliente(db, client, saldo=0)
    _movimiento(db, cid, tid, 300)
    _movimiento(db, cid, tid, 50, tipo=TipoMovimiento.ruleta)
    # Un canje NEGATIVO no cuenta como ganancia
    _movimiento(db, cid, tid, -150, tipo=TipoMovimiento.canje)
    # Un movimiento de OTRO tenant no contamina
    _movimiento(db, cid, None, 999)

    r = client.get(f"{API}/cliente/comercios", headers=headers)
    assert r.status_code == 200, r.text
    items = {c["id"]: c for c in r.json()}
    assert items[tid]["puntos_ganados"] == 350

    # Cliente sin actividad → 0 en todos
    _, headers2 = _nuevo_cliente(db, client, saldo=0)
    items2 = {c["id"]: c for c in
              client.get(f"{API}/cliente/comercios", headers=headers2).json()}
    assert items2[tid]["puntos_ganados"] == 0


# ---------- consentimiento kiosco ----------

def test_kiosco_registro_requiere_consentimiento(db, client):
    """Sin acepto_terminos → 400; con true → 201 y queda evidencia en el movimiento."""
    _habilitar_pantalla(db)
    data = {"nombre": "K Test", "ci": uuid.uuid4().hex[:8],
            "telefono": f"7{uuid.uuid4().int % 10**7:07d}"}

    r = client.post(f"{API}/kiosco/kiosco-demo-001/registro",
                    json={**data, "acepto_terminos": False})
    assert r.status_code == 400
    r2 = client.post(f"{API}/kiosco/kiosco-demo-001/registro", json=data)
    assert r2.status_code == 400  # campo omitido también rechaza

    ok = client.post(f"{API}/kiosco/kiosco-demo-001/registro",
                     json={**data, "acepto_terminos": True})
    assert ok.status_code == 201, ok.text
    mov = db.scalar(select(MovimientoPuntos).where(
        MovimientoPuntos.cliente_id == ok.json()["cliente_id"],
        MovimientoPuntos.tipo == TipoMovimiento.registro))
    assert mov.detalle["consentido_terminos"] is True


# ---------- previos (período espejo) ----------

def test_resumen_previos_periodo_espejo(db, client, owner_headers):
    """Con rango explícito, previos trae los KPIs del período inmediato anterior."""
    hoy = utcnow().date()
    desde, hasta = hoy, hoy + timedelta(days=6)  # 7 días
    # Movimiento en el período ANTERIOR (espejo): día (desde-7)..(desde-1)
    _movimiento(db, _nuevo_cliente(db, client)[0], _tenant_demo_id(db), 40,
                tipo=TipoMovimiento.ruleta,
                cuando=utcnow() - timedelta(days=3))

    r = client.get(f"{API}/socio/metricas/resumen",
                   params={"desde": str(desde), "hasta": str(hasta)},
                   headers=owner_headers)
    assert r.status_code == 200, r.text
    prev = r.json()["previos"]
    assert prev is not None
    assert prev["puntos_otorgados"] >= 40

    # Sin rango → previos no se calcula (el frontend decide cuándo comparar)
    r2 = client.get(f"{API}/socio/metricas/resumen", headers=owner_headers)
    assert r2.json()["previos"] is None
