"""Campañas de marketing: multiplicador activo, códigos de referido,
segmento de clientes inactivos."""
import secrets
from datetime import timedelta

from app.core.security import utcnow
from app.models import Campana, Cliente, EstadoCliente, MovimientoPuntos
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

_ALFABETO_CODIGO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sin 0/O/1/I/L — fácil de dictar


def _aware(dt):
    return dt if dt is None or dt.tzinfo is not None else dt.replace(tzinfo=utcnow().tzinfo)


def multiplicador_activo(db: Session, tenant_id: int, sucursal_id: int | None) -> tuple[int, Campana | None]:
    """Multiplicador vigente para (tenant, sucursal). Una campaña específica de
    sucursal tiene prioridad sobre una general; si hay varias, gana la mayor."""
    ahora = utcnow()
    camps = db.scalars(
        select(Campana).where(
            Campana.tenant_id == tenant_id,
            Campana.activa == True,  # noqa: E712
            or_(Campana.sucursal_id.is_(None), Campana.sucursal_id == sucursal_id),
        )
    ).all()
    vigentes = [c for c in camps if _aware(c.inicio) <= ahora <= _aware(c.fin)]
    if not vigentes:
        return 1, None
    especificas = [c for c in vigentes if c.sucursal_id == sucursal_id]
    elegida = max(especificas or vigentes, key=lambda c: c.multiplicador)
    return max(1, elegida.multiplicador), elegida


def generar_codigo_referido(db: Session) -> str:
    for _ in range(20):
        code = "".join(secrets.choice(_ALFABETO_CODIGO) for _ in range(8))
        if not db.scalar(select(Cliente.id).where(Cliente.codigo_referido == code)):
            return code
    raise RuntimeError("No se pudo generar el código de referido")


def asegurar_codigo_referido(db: Session, cliente: Cliente) -> str:
    """Backfill: el cliente puede ser anterior a los referidos."""
    if not cliente.codigo_referido:
        cliente.codigo_referido = generar_codigo_referido(db)
    return cliente.codigo_referido


def inactivos(db: Session, tenant_id: int, dias: int = 30, limite: int = 500):
    """Clientes activos cuya última actividad en el tenant fue hace >dias."""
    ult = (
        select(MovimientoPuntos.cliente_id, func.max(MovimientoPuntos.created_at).label("ult"))
        .where(MovimientoPuntos.tenant_id == tenant_id)
        .group_by(MovimientoPuntos.cliente_id)
        .subquery()
    )
    corte = utcnow() - timedelta(days=dias)
    rows = db.execute(
        select(Cliente, ult.c.ult)
        .join(ult, Cliente.id == ult.c.cliente_id)
        .where(Cliente.estado == EstadoCliente.activo, ult.c.ult < corte)
        .order_by(ult.c.ult)
        .limit(limite)
    ).all()
    return [(c, _aware(u)) for c, u in rows]
