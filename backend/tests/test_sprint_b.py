"""Regresiones del Sprint B: expiración de puntos, offboarding, audit viewer,
gestión de superadmins, push broadcast, referido en registro de app."""
from datetime import timedelta

from app.core.security import utcnow
from app.jobs.limpieza import purgar_tenants_baja
from app.models import (
    Cliente,
    EstadoCliente,
    EstadoTenant,
    EstadoUsuario,
    MovimientoPuntos,
    RolUsuario,
    Tenant,
    TipoMovimiento,
    Usuario,
)
from app.services.puntos import expirar_puntos_viejos
from sqlalchemy import func, select


def _tenant(db) -> Tenant:
    # El tenant demo es el primero del seed; la anonimización cambia su nombre,
    # así que se busca por posición (id más bajo).
    return db.scalar(select(Tenant).order_by(Tenant.id).limit(1))


def _cliente_demo(db) -> Cliente:
    return db.scalar(select(Cliente).where(Cliente.ci == "12345678"))


def test_expiracion_puntos_respeta_ttl(db):
    """Puntos ganados hace más del TTL expiran; los recientes no."""
    tenant = _tenant(db)
    tenant.puntos_ttl_meses = 1
    cliente = _cliente_demo(db)
    viejo = utcnow() - timedelta(days=45)
    # created_at explícito: server_default solo aplica si no se pasa valor.
    # saldo_puntos es un cache en Cliente — hay que mantenerlo a mano.
    m = MovimientoPuntos(cliente_id=cliente.id, tenant_id=tenant.id,
                         tipo=TipoMovimiento.ruleta, puntos=500,
                         created_at=viejo)
    db.add(m)
    cliente.saldo_puntos += 500
    db.commit()

    saldo_antes = cliente.saldo_puntos
    n = expirar_puntos_viejos(db, tenant)
    db.commit()
    db.refresh(cliente)
    assert n == 500
    assert cliente.saldo_puntos == saldo_antes - 500
    # Idempotente: segunda corrida no vuelve a expirar lo mismo
    assert expirar_puntos_viejos(db, tenant) == 0
    tenant.puntos_ttl_meses = 0
    db.commit()


def test_expiracion_ttl_cero_noop(db):
    tenant = _tenant(db)
    tenant.puntos_ttl_meses = 0
    assert expirar_puntos_viejos(db, tenant) == 0


def test_audit_viewer(client, admin_headers):
    r = client.get("/api/v1/admin/audit?page=1&size=10", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data
    r2 = client.get("/api/v1/admin/audit?accion=inexistente_zzz", headers=admin_headers)
    assert r2.json()["total"] == 0


def test_superadmins_ciclo(client, admin_headers, db):
    # Listar: existe el admin seed
    r = client.get("/api/v1/admin/usuarios", headers=admin_headers)
    assert r.status_code == 200
    inicial = len(r.json())
    assert inicial >= 1

    # Crear
    r = client.post("/api/v1/admin/usuarios",
                    json={"email": "admin2@yapai.com", "nombre": "Admin Dos"},
                    headers=admin_headers)
    assert r.status_code == 201, r.text
    uid = r.json()["id"]

    # No puedes desactivarte a ti mismo
    me = db.scalar(select(Usuario).where(Usuario.email == "admin@yapai.com"))
    r = client.post(f"/api/v1/admin/usuarios/{me.id}/desactivar", headers=admin_headers)
    assert r.status_code == 409

    # Desactivar al nuevo
    r = client.post(f"/api/v1/admin/usuarios/{uid}/desactivar", headers=admin_headers)
    assert r.status_code == 200
    db.refresh(db.get(Usuario, uid))
    assert db.get(Usuario, uid).estado == EstadoUsuario.suspendido

    # Reactivar
    r = client.post(f"/api/v1/admin/usuarios/{uid}/reactivar", headers=admin_headers)
    assert r.status_code == 200


def test_superadmin_sin_acceso_owner(client, owner_headers):
    """El visor de audit y gestión de admins son solo superadmin."""
    assert client.get("/api/v1/admin/audit", headers=owner_headers).status_code in (401, 403)
    assert client.get("/api/v1/admin/usuarios", headers=owner_headers).status_code in (401, 403)


def test_socio_baja_y_export(client, owner_headers, db):
    """Export devuelve datos; baja exige password y suspende el tenant."""
    r = client.get("/api/v1/socio/cuenta/exportar", headers=owner_headers)
    assert r.status_code == 200
    data = r.json()
    assert "tenant" in data and "clientes" in data and "movimientos_puntos" in data

    r = client.post("/api/v1/socio/cuenta/baja", json={"password": "mala"},
                    headers=owner_headers)
    assert r.status_code == 401

    r = client.post("/api/v1/socio/cuenta/baja", json={"password": "Owner123!"},
                    headers=owner_headers)
    assert r.status_code == 200, r.text

    tenant = _tenant(db)
    db.refresh(tenant)
    assert tenant.estado == EstadoTenant.suspendido
    assert tenant.baja_solicitada_en is not None

    # El tenant suspendido bloquea al owner: cualquier endpoint posterior da 401/403
    r = client.post("/api/v1/socio/cuenta/baja", json={"password": "Owner123!"},
                    headers=owner_headers)
    assert r.status_code in (401, 403)

    # Restaurar para no romper tests posteriores (owner/login requiere tenant activo)
    from app.services.tenants import reactivar_tenant
    reactivar_tenant(db, tenant, actor_id=1)
    db.commit()


def test_purga_baja_anonimiza(db):
    """La purga anonimiza PII y no toca el ledger append-only.

    Usa un tenant desechable propio (la purga es destructiva por diseño —
    no puede tocar el seed compartido).
    """
    from app.models import EstadoUsuario, Sucursal

    t = Tenant(nombre_comercial="BajaTest SRL", nit_rut="nit-baja-1",
               email_contacto="baja@test.com", baja_solicitada_en=utcnow() - timedelta(days=31))
    db.add(t)
    db.flush()
    u = Usuario(email="owner-baja@test.com", nombre="Owner Baja",
                rol=RolUsuario.owner, tenant_id=t.id, password_hash="x")
    c = Cliente(nombre="Cli Baja", ci="ci-baja-1", telefono="tel-baja-1",
                estado=EstadoCliente.activo, tenant_registro_id=t.id,
                saldo_puntos=200, codigo_referido="BAJA001")
    s = Sucursal(tenant_id=t.id, nombre="Suc Baja")
    db.add_all([u, c, s])
    db.flush()
    db.add(MovimientoPuntos(cliente_id=c.id, tenant_id=t.id,
                            tipo=TipoMovimiento.registro, puntos=200))
    db.commit()
    total_movs = db.scalar(select(func.count(MovimientoPuntos.id)))

    n = purgar_tenants_baja()
    assert n >= 1
    db.refresh(t)
    db.refresh(c)
    db.refresh(u)
    assert t.nit_rut == f"del-nit-{t.id}"
    assert t.email_contacto is None
    assert u.email == f"del-{u.id}@baja.yapai"
    assert u.estado == EstadoUsuario.suspendido
    assert c.nombre == "Cuenta eliminada"
    assert c.ci == f"del-ci-{c.id}"
    assert c.estado == EstadoCliente.eliminado
    assert c.saldo_puntos == 0
    # El ledger crece (anulación del saldo) pero jamás se borra
    assert db.scalar(select(func.count(MovimientoPuntos.id))) > total_movs
    assert t.baja_solicitada_en is None


def test_registro_app_paga_referido(client, db):
    """Registro en app con código → bonus al referidor (tenant de origen)."""
    from app.services.campanas import asegurar_codigo_referido
    referidor = _cliente_demo(db)
    if referidor is None or referidor.estado != EstadoCliente.activo:
        # el test anterior pudo anonimizarlo: crear uno nuevo registrado en demo
        tenant = _tenant(db)
        referidor = Cliente(nombre="Ref", ci="ref-1", telefono="ref-tel-1",
                            estado=EstadoCliente.activo,
                            tenant_registro_id=tenant.id, saldo_puntos=0)
        db.add(referidor)
        db.flush()
    asegurar_codigo_referido(db, referidor)
    db.commit()
    assert referidor.codigo_referido
    saldo_antes = referidor.saldo_puntos
    tenant = db.get(Tenant, referidor.tenant_registro_id)

    r = client.post("/api/v1/auth/cliente/registro", json={
        "nombre": "Nuevo Ref", "ci": "ci-ref-2", "telefono": "tel-ref-2",
        "codigo_referido": referidor.codigo_referido,
    })
    assert r.status_code in (200, 201), r.text
    db.refresh(referidor)
    esperado = saldo_antes + (tenant.puntos_referido if tenant else 0)
    assert referidor.saldo_puntos == esperado
