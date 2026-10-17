from datetime import date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import EstadoPase, MovimientoPuntos, PaseDigital, Tenant, TipoMovimiento
from app.schemas.admin import KpisSocio


def horas_a_primer_giro(db: Session, tenant: Tenant) -> float | None:
    """Horas desde el alta del tenant hasta su primer giro de ruleta (None si aún no hay)."""
    primer = db.scalar(
        select(func.min(MovimientoPuntos.created_at)).where(
            MovimientoPuntos.tenant_id == tenant.id,
            MovimientoPuntos.tipo == TipoMovimiento.ruleta,
        )
    )
    if not primer or not tenant.created_at:
        return None
    return round((primer - tenant.created_at).total_seconds() / 3600, 1)

_TIPOS_EMISION = (TipoMovimiento.registro, TipoMovimiento.ruleta, TipoMovimiento.bonus_manual)


def calcular_kpis_socio(
    db: Session, tenant_id: int,
    desde: date | None, hasta: date | None,
    sucursal_id: int | None = None,
) -> KpisSocio:
    """Métricas de rendimiento de un socio en un rango (default: todo el histórico)."""
    base = [MovimientoPuntos.tenant_id == tenant_id]
    if sucursal_id:
        base.append(MovimientoPuntos.sucursal_id == sucursal_id)
    if desde:
        base.append(MovimientoPuntos.created_at >= datetime.combine(desde, time.min))
    if hasta:
        base.append(MovimientoPuntos.created_at <= datetime.combine(hasta, time.max))

    clientes_nuevos = db.scalar(
        select(func.count(MovimientoPuntos.id)).where(*base, MovimientoPuntos.tipo == TipoMovimiento.registro)
    ) or 0
    puntos_emitidos = db.scalar(
        select(func.coalesce(func.sum(MovimientoPuntos.puntos), 0)).where(
            *base, MovimientoPuntos.tipo.in_(_TIPOS_EMISION), MovimientoPuntos.puntos > 0
        )
    ) or 0
    puntos_consumidos = abs(db.scalar(
        select(func.coalesce(func.sum(MovimientoPuntos.puntos), 0)).where(
            *base, MovimientoPuntos.tipo == TipoMovimiento.canje
        )
    ) or 0)
    canjes_exitosos = db.scalar(
        select(func.count(MovimientoPuntos.id)).where(*base, MovimientoPuntos.tipo == TipoMovimiento.canje)
    ) or 0
    tenant = db.get(Tenant, tenant_id)
    return KpisSocio(
        clientes_nuevos=clientes_nuevos,
        puntos_emitidos=puntos_emitidos,
        puntos_consumidos=puntos_consumidos,
        canjes_exitosos=canjes_exitosos,
        horas_a_primer_giro=horas_a_primer_giro(db, tenant) if tenant else None,
    )
