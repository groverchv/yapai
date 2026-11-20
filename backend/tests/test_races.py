"""Tests de condiciones de carrera y atomicidad.

En SQLite no se puede forzar interleaving real de hilos como en Postgres,
pero sí se verifican los GUARDAS atómicos que hacen imposible el resultado
corrupto incluso bajo concurrencia:
- stock: UPDATE condicional (stock>0) → nunca negativo, doble canje → 409
- ruleta: check giros/día bajo SELECT FOR UPDATE → segundo giro → 429
- PIN: contador del limiter es atómico → 6to intento → 429
"""

from app.core.security import hash_secret
from app.models import (
    EstadoPase,
    EstadoPremio,
    MovimientoPuntos,
    PaseDigital,
    PinSucursal,
    Premio,
    Sucursal,
    TipoMovimiento,
)
from sqlalchemy import select
from test_invariantes import _nuevo_cliente

API = "/api/v1"


def _premio_stock_1(db, owner_headers, client):
    """Crea un premio de stock limitado = 1 vía API del socio."""
    r = client.post(f"{API}/socio/premios", headers=owner_headers, json={
        "nombre": "Premio Único Carrera", "costo_puntos": 50,
        "stock_limitado": True, "stock": 1,
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _hacer_pase(client, headers, premio_id):
    r = client.post(f"{API}/cliente/pases", json={"premio_id": premio_id}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _sucursal_cajero(client, cajero_headers):
    return client.get(f"{API}/caja/contexto", headers=cajero_headers).json()["sucursales"][0]["id"]


def _canjear(client, pin_corto, sucursal_id, cajero_headers):
    return client.post(f"{API}/caja/pases/{pin_corto}/canjear",
                       json={"sucursal_id": sucursal_id}, headers=cajero_headers)


def _habilitar_pantalla(client, db):
    """PIN de sucursal + habilitación de kiosco-demo-001 (requisito de girar)."""
    suc = db.scalar(select(Sucursal).where(Sucursal.nombre == "Sucursal Centro"))
    if not db.get(PinSucursal, suc.id):
        db.add(PinSucursal(sucursal_id=suc.id, pin_hash=hash_secret("4521")))
        db.commit()
    r = client.post(f"{API}/caja/pantalla/habilitar",
                    json={"device_token": "kiosco-demo-001", "pin": "4521"})
    assert r.status_code == 200, r.text


def test_stock_no_negativo_doble_canje(db_seeded, client, db, owner_headers, cajero_headers):
    """Premio con stock=1: dos clientes con pase, el 2do canje aborta con 409
    y el stock jamás queda negativo (UPDATE condicional atómico)."""
    premio_id = _premio_stock_1(db, owner_headers, client)
    sucursal_id = _sucursal_cajero(client, cajero_headers)
    h1 = _nuevo_cliente(db, client, saldo=100)
    h2 = _nuevo_cliente(db, client, saldo=100)
    pase1 = _hacer_pase(client, h1, premio_id)
    pase2 = _hacer_pase(client, h2, premio_id)

    r1 = _canjear(client, pase1["pin_corto"], sucursal_id, cajero_headers)
    assert r1.status_code == 200, r1.text

    # Segundo canje del ÚLTIMO stock: la guarda atómica lo rechaza
    r2 = _canjear(client, pase2["pin_corto"], sucursal_id, cajero_headers)
    assert r2.status_code == 409, r2.text

    db.expire_all()
    premio = db.get(Premio, premio_id)
    assert premio.stock == 0
    assert premio.estado == EstadoPremio.agotado
    # El pase rechazado sigue activo y sus puntos congelados intactos
    assert db.get(PaseDigital, pase2["id"]).estado == EstadoPase.activo


def test_stock_cero_rechaza_canje_directo(db_seeded, client, db, owner_headers, cajero_headers):
    """Pase generado cuando había stock; premio agotado antes del canje → 409
    sin débito de puntos."""
    premio_id = _premio_stock_1(db, owner_headers, client)
    sucursal_id = _sucursal_cajero(client, cajero_headers)
    h = _nuevo_cliente(db, client, saldo=100)
    pase = _hacer_pase(client, h, premio_id)
    # Agotar el stock por fuera (otro canje ganó la carrera)
    db.execute(
        Premio.__table__.update().where(Premio.id == premio_id).values(stock=0))
    db.commit()
    r = _canjear(client, pase["pin_corto"], sucursal_id, cajero_headers)
    assert r.status_code == 409, r.text
    # Sin movimiento de canje en el ledger para ese pase
    n = db.scalar(select(MovimientoPuntos.id).where(
        MovimientoPuntos.pase_id == pase["id"],
        MovimientoPuntos.tipo == TipoMovimiento.canje))
    assert n is None


def test_ruleta_un_giro_por_dia(db_seeded, client, db):
    """El giro corre bajo SELECT FOR UPDATE del cliente: el check de giros/día
    es serializable — un segundo giro (incluso 'simultáneo') es 429."""
    _habilitar_pantalla(client, db)
    h = _nuevo_cliente(db, client, saldo=0)
    r_me = client.get(f"{API}/cliente/me", headers=h)
    cliente_id = r_me.json()["id"]

    r1 = client.post(f"{API}/kiosco/kiosco-demo-001/ruleta/girar",
                     json={"cliente_id": cliente_id})
    assert r1.status_code == 200, r1.text

    r2 = client.post(f"{API}/kiosco/kiosco-demo-001/ruleta/girar",
                     json={"cliente_id": cliente_id})
    assert r2.status_code == 429, r2.text

    # Solo UN movimiento ruleta en el ledger
    n = db.scalar(select(MovimientoPuntos.id).where(
        MovimientoPuntos.cliente_id == cliente_id,
        MovimientoPuntos.tipo == TipoMovimiento.ruleta).limit(2).offset(1))
    assert n is None


def test_pin_lockout_sexto_intento_429(db_seeded, client, db):
    """El limiter de PIN es atómico: 5 fallos → el 6to request ni llega a
    verificar el PIN (429), sea concurrente o secuencial. El PIN correcto
    también recibe 429 — la ventana protege contra fuerza bruta."""
    suc = db.scalar(select(Sucursal).where(Sucursal.nombre == "Sucursal Centro"))
    if not db.get(PinSucursal, suc.id):
        db.add(PinSucursal(sucursal_id=suc.id, pin_hash=hash_secret("4521")))
        db.commit()

    resultados = []
    for _ in range(5):
        r = client.post(f"{API}/caja/pantalla/habilitar",
                        json={"device_token": "kiosco-demo-001", "pin": "0000"})
        resultados.append(r.status_code)
    assert resultados == [401] * 5

    # 6to intento: bloqueado por el limiter aun con el PIN correcto
    r = client.post(f"{API}/caja/pantalla/habilitar",
                    json={"device_token": "kiosco-demo-001", "pin": "4521"})
    assert r.status_code == 429
