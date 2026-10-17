"""Billing por plan: facturas mensuales, estado de cuenta, cobro y mora.

Reglas:
- Solo se factura a tenants con plan de precio > 0 y con el trial ya vencido.
- Una factura por tenant por período ('YYYY-MM') — generación idempotente.
- pendiente → vencida cuando pasa vence_en (job).
- vencida + FACTURA_GRACIA_DIAS sin pagar → tenant suspendido (regla de negocio).
- El admin marca pagada con método + referencia (manual hoy; pasarela después).
"""
from datetime import date, timedelta
from calendar import monthrange

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import utcnow
from app.models import (
    EstadoFactura, EstadoTenant, FacturaPlan, Plan, Tenant, Usuario,
)


def periodo_de(fecha: date | None = None) -> str:
    f = fecha or utcnow().date()
    return f"{f.year:04d}-{f.month:02d}"


def _vencimiento(periodo: str, emitida: date) -> date:
    """Vence el día FACTURA_VENCE_DIA del mes; si se emite después, +7 días."""
    anio, mes = (int(x) for x in periodo.split("-"))
    vence = date(anio, mes, min(settings.FACTURA_VENCE_DIA, monthrange(anio, mes)[1]))
    return max(vence, emitida + timedelta(days=7))


def en_trial(tenant: Tenant) -> bool:
    if not tenant.trial_fin:
        return False
    fin = tenant.trial_fin
    if fin.tzinfo is None:
        fin = fin.replace(tzinfo=utcnow().tzinfo)
    return fin > utcnow()


def generar_facturas(db: Session, periodo: str | None = None) -> list[FacturaPlan]:
    """Emite la factura del período para cada tenant que corresponde. Idempotente."""
    p = periodo or periodo_de()
    creadas = []
    tenants = db.scalars(
        select(Tenant).where(Tenant.estado == EstadoTenant.activo, Tenant.plan_id.isnot(None))
    ).all()
    for tenant in tenants:
        plan = db.get(Plan, tenant.plan_id)
        if not plan or not plan.activo or float(plan.precio_mensual) <= 0:
            continue
        if en_trial(tenant):
            continue
        existe = db.scalar(
            select(FacturaPlan).where(
                FacturaPlan.tenant_id == tenant.id, FacturaPlan.periodo == p)
        )
        if existe:
            continue
        f = FacturaPlan(
            tenant_id=tenant.id, plan_id=plan.id, plan_nombre=plan.nombre,
            periodo=p, monto=plan.precio_mensual, moneda=plan.moneda,
            vence_en=_vencimiento(p, utcnow().date()),
        )
        db.add(f)
        creadas.append(f)
    db.flush()
    return creadas


def marcar_vencidas(db: Session) -> int:
    """pendiente + vence_en pasado → vencida. Retorna cuántas cambiaron."""
    n = 0
    pendientes = db.scalars(
        select(FacturaPlan).where(FacturaPlan.estado == EstadoFactura.pendiente)
    ).all()
    for f in pendientes:
        vence = f.vence_en
        if vence.tzinfo is None:
            vence = vence.replace(tzinfo=utcnow().tzinfo)
        if vence < utcnow():
            f.estado = EstadoFactura.vencida
            n += 1
    db.flush()
    return n


def suspender_por_impago(db: Session) -> list[int]:
    """Suspende tenants con factura vencida más allá del período de gracia."""
    from app.services.tenants import suspender_tenant

    limite = utcnow() - timedelta(days=settings.FACTURA_GRACIA_DIAS)
    vencidas = db.scalars(
        select(FacturaPlan).where(FacturaPlan.estado == EstadoFactura.vencida)
    ).all()
    suspendidos = []
    for f in vencidas:
        vence = f.vence_en
        if vence.tzinfo is None:
            vence = vence.replace(tzinfo=utcnow().tzinfo)
        if vence >= limite:
            continue
        tenant = db.get(Tenant, f.tenant_id)
        if tenant and tenant.estado == EstadoTenant.activo:
            suspender_tenant(db, tenant, None)
            suspendidos.append(tenant.id)
    db.flush()
    return suspendidos


def estado_cuenta(db: Session, tenant: Tenant) -> str:
    """al_dia | pendiente | vencida (peor estado de sus facturas no anuladas)."""
    estados = db.scalars(
        select(FacturaPlan.estado).where(
            FacturaPlan.tenant_id == tenant.id,
            FacturaPlan.estado != EstadoFactura.anulada,
        )
    ).all()
    if EstadoFactura.vencida in estados:
        return "vencida"
    if EstadoFactura.pendiente in estados:
        return "pendiente"
    return "al_dia"


def pagar_factura(db: Session, factura: FacturaPlan, admin: Usuario,
                  metodo: str, referencia: str | None) -> None:
    factura.estado = EstadoFactura.pagada
    factura.pagada_en = utcnow()
    factura.metodo = metodo
    factura.referencia = referencia
    factura.aprobada_por = admin.id
