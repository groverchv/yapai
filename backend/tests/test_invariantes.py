"""Tests de invariantes de negocio (reglas del plan, sección 5).

Cada test verifica una regla end-to-end vía API + nivel DB cuando aplica.
Corre contra una SQLite temporal sembrada con app.seed. Los clientes de
prueba se crean por test para aislamiento (el seed solo trae uno).
"""

from datetime import datetime, timedelta, timezone

import pytest
from app.core.security import hash_secret
from app.models import (
    EstadoPase,
    Pantalla,
    PaseDigital,
    PinSucursal,
    Premio,
    Sucursal,
)
from app.services.puntos import expirar_pases_vencidos
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

API = "/api/v1"
_counter = {"n": 0}


def _cliente_login(client, ci="12345678", telefono="70000001"):
    r = client.post(f"{API}/auth/cliente/login", json={"ci": ci, "telefono": telefono})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}


def _nuevo_cliente(db, client, saldo=0):
    """Crea un cliente aislado con saldo directo y devuelve sus headers."""
    _counter["n"] += 1
    n = _counter["n"]
    db.execute(text(
        "INSERT INTO clientes (nombre, ci, telefono, estado, saldo_puntos, puntos_congelados) "
        f"VALUES ('Test {n}', 'CI{n:08d}', '79{n:06d}', 'activo', :s, 0)"),
        {"s": saldo})
    db.commit()
    return _cliente_login(client, ci=f"CI{n:08d}", telefono=f"79{n:06d}")


def _premio(db, nombre):
    """Busca el premio seed por nombre directo en DB."""
    p = db.scalar(select(Premio).where(Premio.nombre.ilike(f"%{nombre}%")))
    assert p, f"premio {nombre} no encontrado"
    return {"id": p.id, "nombre": p.nombre, "costo_puntos": p.costo_puntos}


def _sucursal_cajero(client, cajero_headers):
    ctx = client.get(f"{API}/caja/contexto", headers=cajero_headers).json()
    return ctx["sucursales"][0]["id"], ctx


# ---------- Regla #1: ledger append-only (trigger DB) ----------

def test_ledger_no_permite_update(db_seeded, db):
    with pytest.raises(IntegrityError):
        db.execute(text("UPDATE movimientos_puntos SET puntos=999 WHERE id=1"))
        db.commit()


def test_ledger_no_permite_delete(db_seeded, db):
    with pytest.raises(IntegrityError):
        db.execute(text("DELETE FROM movimientos_puntos WHERE id=1"))
        db.commit()


def test_audit_log_append_only(db_seeded, db):
    db.execute(text(
        "INSERT INTO audit_log (accion, entidad, entidad_id) VALUES ('test', 'x', 1)"))
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(text("DELETE FROM audit_log WHERE entidad='x'"))
        db.commit()


# ---------- Reglas #7-8: congelamiento y anti doble-gasto ----------

def test_pase_congela_y_bloquea_saldo(db_seeded, client, db, owner_headers):
    h = _nuevo_cliente(db, client, saldo=350)
    gaseosa = _premio(db, "Gaseosa")  # 150 pts

    r = client.post(f"{API}/cliente/pases", json={"premio_id": gaseosa["id"]}, headers=h)
    assert r.status_code == 201, r.text
    w = client.get(f"{API}/cliente/wallet", headers=h).json()
    assert w["congelado"] == 150 and w["disponible"] == 200

    pizza = _premio(db, "Pizza")  # 500 pts > 200 disponibles
    r2 = client.post(f"{API}/cliente/pases", json={"premio_id": pizza["id"]}, headers=h)
    assert r2.status_code == 409


def test_cancelar_pase_libera_puntos(db_seeded, client, db, owner_headers):
    h = _nuevo_cliente(db, client, saldo=300)
    gaseosa = _premio(db, "Gaseosa")
    pase = client.post(f"{API}/cliente/pases", json={"premio_id": gaseosa["id"]}, headers=h).json()

    r = client.post(f"{API}/cliente/pases/{pase['id']}/cancelar", headers=h)
    assert r.status_code == 200
    w = client.get(f"{API}/cliente/wallet", headers=h).json()
    assert w["congelado"] == 0 and w["disponible"] == w["saldo"]


def test_expiracion_libera_congelado(db_seeded, client, db, owner_headers):
    h = _nuevo_cliente(db, client, saldo=300)
    gaseosa = _premio(db, "Gaseosa")
    pase = client.post(f"{API}/cliente/pases", json={"premio_id": gaseosa["id"]}, headers=h).json()

    db.execute(text("UPDATE pases_digitales SET expira_en=:f WHERE id=:i"),
               {"f": datetime.now(timezone.utc) - timedelta(minutes=1), "i": pase["id"]})
    db.commit()
    assert expirar_pases_vencidos(db) >= 1
    db.expire_all()
    assert db.get(PaseDigital, pase["id"]).estado == EstadoPase.expirado

    w = client.get(f"{API}/cliente/wallet", headers=h).json()
    assert w["congelado"] == 0


# ---------- Reglas #9-10: canje atómico ----------

def test_canje_atomico_y_no_recanje(db_seeded, client, db, owner_headers, cajero_headers):
    h = _nuevo_cliente(db, client, saldo=350)
    gaseosa = _premio(db, "Gaseosa")
    pase = client.post(f"{API}/cliente/pases", json={"premio_id": gaseosa["id"]}, headers=h).json()
    suc_id, _ = _sucursal_cajero(client, cajero_headers)

    preview = client.get(f"{API}/caja/pases/{pase['pin_corto']}", headers=cajero_headers)
    assert preview.status_code == 200 and preview.json()["estado"] == "activo"

    r = client.post(f"{API}/caja/pases/{pase['pin_corto']}/canjear",
                    json={"sucursal_id": suc_id}, headers=cajero_headers)
    assert r.status_code == 200, r.text
    w = client.get(f"{API}/cliente/wallet", headers=h).json()
    assert w["saldo"] == 200 and w["congelado"] == 0

    r2 = client.post(f"{API}/caja/pases/{pase['pin_corto']}/canjear",
                     json={"sucursal_id": suc_id}, headers=cajero_headers)
    assert r2.status_code == 409


def test_canje_descuenta_stock_y_agota(db_seeded, client, db, owner_headers, cajero_headers):
    """Stock 1 → tras el canje el premio queda agotado automáticamente."""
    h = _nuevo_cliente(db, client, saldo=600)
    pizza = _premio(db, "Pizza")
    db.execute(text("UPDATE premios SET stock=1 WHERE id=:i"), {"i": pizza["id"]})
    db.commit()

    pase = client.post(f"{API}/cliente/pases", json={"premio_id": pizza["id"]}, headers=h).json()
    suc_id, _ = _sucursal_cajero(client, cajero_headers)
    r = client.post(f"{API}/caja/pases/{pase['pin_corto']}/canjear",
                    json={"sucursal_id": suc_id}, headers=cajero_headers)
    assert r.status_code == 200, r.text
    assert r.json()["stock_restante"] == 0
    db.expire_all()
    assert db.get(Premio, pizza["id"]).estado.value == "agotado"


# ---------- Regla #11: límites de bonus ----------

def test_bonus_limites_tx_y_diario(db_seeded, client, db, cajero_headers):
    suc_id, ctx = _sucursal_cajero(client, cajero_headers)
    assert ctx["max_puntos_tx"] == 500 and ctx["max_puntos_dia_cajero"] == 2000
    cliente_id = client.get(f"{API}/caja/clientes/buscar?q=70000001",
                            headers=cajero_headers).json()[0]["id"]

    r = client.post(f"{API}/caja/bonus",
                    json={"cliente_id": cliente_id, "sucursal_id": suc_id,
                          "puntos": 600, "motivo": "compra test"}, headers=cajero_headers)
    assert r.status_code == 429  # supera max_puntos_tx

    for _ in range(4):  # 4 × 500 = 2000 = límite diario
        r = client.post(f"{API}/caja/bonus",
                        json={"cliente_id": cliente_id, "sucursal_id": suc_id,
                              "puntos": 500, "motivo": "compra test"}, headers=cajero_headers)
        assert r.status_code == 200
    r = client.post(f"{API}/caja/bonus",
                    json={"cliente_id": cliente_id, "sucursal_id": suc_id,
                          "puntos": 1, "motivo": "compra test"}, headers=cajero_headers)
    assert r.status_code == 429


# ---------- Reglas #2-3: aislamiento y suspensión ----------

def test_cajero_no_accede_a_socio(db_seeded, client, cajero_headers):
    assert client.get(f"{API}/socio/empleados", headers=cajero_headers).status_code == 403


def test_suspension_tenant_bloquea_login(db_seeded, client, admin_headers):
    socios = client.get(f"{API}/admin/socios?q=Don Yapai", headers=admin_headers).json()
    tid = socios["items"][0]["id"]

    assert client.post(f"{API}/admin/socios/{tid}/suspender", headers=admin_headers).status_code == 200
    r = client.post(f"{API}/auth/login", json={"email": "owner@demo.com", "password": "Owner123!"})
    assert r.status_code == 403

    client.post(f"{API}/admin/socios/{tid}/reactivar", headers=admin_headers)
    r = client.post(f"{API}/auth/login", json={"email": "owner@demo.com", "password": "Owner123!"})
    assert r.status_code == 200


# ---------- Regla #5: montos de esquema inmutables con uso ----------

def test_esquema_montos_inmutables_con_uso(db_seeded, client, admin_headers):
    r = client.post(f"{API}/admin/liquidaciones/generar",
                    json={"periodo": "2025-01"}, headers=admin_headers)
    assert r.status_code == 200, r.text
    esq = client.get(f"{API}/admin/esquemas", headers=admin_headers).json()
    esq_id = next(e["id"] for e in esq if e["nombre"] == "Estándar")
    r = client.patch(f"{API}/admin/esquemas/{esq_id}",
                     json={"costo_canje": 9.99}, headers=admin_headers)
    assert r.status_code == 409


# ---------- Regla #14 + rate limit: PIN de pantalla ----------

def test_pin_habilitacion_y_rate_limit(db_seeded, client, db):
    suc = db.scalar(select(Sucursal).where(Sucursal.nombre == "Sucursal Centro"))
    db.add(PinSucursal(sucursal_id=suc.id, pin_hash=hash_secret("4521")))
    db.commit()

    r = client.post(f"{API}/caja/pantalla/habilitar",
                    json={"device_token": "kiosco-demo-001", "pin": "9999"})
    assert r.status_code == 401
    r = client.post(f"{API}/caja/pantalla/habilitar",
                    json={"device_token": "kiosco-demo-001", "pin": "4521"})
    assert r.status_code == 200
    db.expire_all()
    assert db.scalar(select(Pantalla).where(
        Pantalla.device_token == "kiosco-demo-001")).habilitada_hasta is not None

    # 5 intentos más → el 6to es 429 (lock anti brute-force por IP)
    for _ in range(5):
        client.post(f"{API}/caja/pantalla/habilitar",
                    json={"device_token": "kiosco-demo-001", "pin": "0000"})
    r = client.post(f"{API}/caja/pantalla/habilitar",
                    json={"device_token": "kiosco-demo-001", "pin": "0000"})
    assert r.status_code == 429


# ---------- Regla #15: baja de cliente ----------

def test_baja_cliente_bloquea_login(db_seeded, client, db):
    h = _nuevo_cliente(db, client, saldo=0)
    r = client.delete(f"{API}/cliente/me", headers=h)
    assert r.status_code == 200
    n = _counter["n"]
    r = client.post(f"{API}/auth/cliente/login",
                    json={"ci": f"CI{n:08d}", "telefono": f"79{n:06d}"})
    assert r.status_code == 401


# ---------- Kiosco: pantalla habilitada requerida ----------

def test_kiosco_requiere_habilitacion(db_seeded, client, db):
    db.execute(text("UPDATE pantallas SET habilitada_hasta=NULL"))
    db.commit()
    r = client.get(f"{API}/kiosco/kiosco-demo-001/config")
    assert r.status_code == 403
