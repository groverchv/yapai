from app.core.security import utcnow
from app.models import (
    EstadoPantalla,
    EstadoTenant,
    EstadoUsuario,
    Pantalla,
    Sucursal,
    SujetoTipo,
    Tenant,
    Usuario,
)
from app.services.audit import registrar_audit
from app.services.auth import revocar_todos_refresh
from sqlalchemy import select, update
from sqlalchemy.orm import Session


def suspender_tenant(db: Session, tenant: Tenant, actor_id: int | None) -> None:
    """Baja lógica: bloquea acceso al portal Y a las pantallas físicas (regla #2)."""
    ahora = utcnow()
    tenant.estado = EstadoTenant.suspendido
    tenant.suspendido_en = ahora
    tenant.suspendido_por = actor_id

    usuarios = db.scalars(select(Usuario).where(Usuario.tenant_id == tenant.id)).all()
    for u in usuarios:
        u.estado = EstadoUsuario.suspendido
        revocar_todos_refresh(db, SujetoTipo.usuario, u.id)

    db.execute(
        update(Pantalla)
        .where(Pantalla.sucursal_id.in_(
            select(Sucursal.id).where(Sucursal.tenant_id == tenant.id)
        ))
        .values(estado=EstadoPantalla.bloqueada, habilitada_hasta=None)
    )
    registrar_audit(db, actor_id, "suspender_socio", "tenant", tenant.id,
                    {"usuarios_afectados": len(usuarios)})


def reactivar_tenant(db: Session, tenant: Tenant, actor_id: int) -> None:
    """Reactiva el tenant. Las pantallas vuelven a 'activa' pero requieren PIN nuevo."""
    tenant.estado = EstadoTenant.activo
    tenant.suspendido_en = None
    tenant.suspendido_por = None

    db.execute(
        update(Usuario)
        .where(Usuario.tenant_id == tenant.id)
        .values(estado=EstadoUsuario.activo)
    )
    db.execute(
        update(Pantalla)
        .where(Pantalla.sucursal_id.in_(
            select(Sucursal.id).where(Sucursal.tenant_id == tenant.id)
        ))
        .values(estado=EstadoPantalla.activa, habilitada_hasta=None)
    )
    registrar_audit(db, actor_id, "reactivar_socio", "tenant", tenant.id)
