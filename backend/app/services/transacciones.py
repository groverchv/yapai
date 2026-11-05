from datetime import date, datetime, time

from app.models import (
    Cliente,
    MovimientoPuntos,
    Premio,
    Sucursal,
    Tenant,
    TipoMovimiento,
    Usuario,
)
from app.schemas.admin import TransaccionOut
from sqlalchemy import or_, select


def stmt_transacciones(filtros: list):
    return (
        select(
            MovimientoPuntos.id, MovimientoPuntos.created_at, MovimientoPuntos.tenant_id,
            Tenant.nombre_comercial.label("socio"),
            Sucursal.nombre.label("sucursal"),
            Cliente.id.label("cliente_id"), Cliente.nombre.label("cliente_nombre"),
            Cliente.ci.label("cliente_ci"),
            MovimientoPuntos.tipo, MovimientoPuntos.puntos,
            Usuario.nombre.label("ejecutado_por"),
            Premio.nombre.label("premio"),
            MovimientoPuntos.detalle,
        )
        .join(Cliente, MovimientoPuntos.cliente_id == Cliente.id)
        .outerjoin(Tenant, MovimientoPuntos.tenant_id == Tenant.id)
        .outerjoin(Sucursal, MovimientoPuntos.sucursal_id == Sucursal.id)
        .outerjoin(Usuario, MovimientoPuntos.ejecutado_por == Usuario.id)
        .outerjoin(Premio, MovimientoPuntos.premio_id == Premio.id)
        .where(*filtros)
        .order_by(MovimientoPuntos.created_at.desc())
    )


def filtros_transacciones(
    desde: date | None = None, hasta: date | None = None,
    tenant_id: int | None = None, sucursal_id: int | None = None,
    cliente: str | None = None, tipo: TipoMovimiento | None = None,
    ejecutado_por: int | None = None,
) -> list:
    filtros = []
    if desde:
        filtros.append(MovimientoPuntos.created_at >= datetime.combine(desde, time.min))
    if hasta:
        filtros.append(MovimientoPuntos.created_at <= datetime.combine(hasta, time.max))
    if tenant_id:
        filtros.append(MovimientoPuntos.tenant_id == tenant_id)
    if sucursal_id:
        filtros.append(MovimientoPuntos.sucursal_id == sucursal_id)
    if tipo:
        filtros.append(MovimientoPuntos.tipo == tipo)
    if ejecutado_por:
        filtros.append(MovimientoPuntos.ejecutado_por == ejecutado_por)
    if cliente:
        like = f"%{cliente}%"
        filtros.append(or_(
            Cliente.ci.ilike(like), Cliente.telefono.ilike(like), Cliente.nombre.ilike(like)
        ))
    return filtros


def to_transaccion_out(r) -> TransaccionOut:
    return TransaccionOut(
        id=r.id, created_at=r.created_at, tenant_id=r.tenant_id,
        socio=r.socio, sucursal=r.sucursal, cliente_id=r.cliente_id,
        cliente_nombre=r.cliente_nombre, cliente_ci=r.cliente_ci,
        tipo=r.tipo.value, puntos=r.puntos, ejecutado_por=r.ejecutado_por,
        premio=r.premio, detalle=r.detalle,
    )
