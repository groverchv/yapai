from datetime import date, datetime, time, timedelta

from app.core.deps import require_superadmin
from app.db.session import get_db
from app.models import (
    Cliente,
    EstadoFactura,
    EstadoLiquidacion,
    EstadoTenant,
    FacturaPlan,
    Liquidacion,
    MovimientoPuntos,
    Tenant,
    TipoMovimiento,
)
from app.schemas.admin import (
    DashboardOut,
    DistribucionTipoItem,
    KpisGlobales,
    KpisSocio,
    Pagina,
    SerieDia,
    TopSocioItem,
    TransaccionOut,
)
from app.services.export import csv_response
from app.services.kpis import calcular_kpis_socio
from app.services.transacciones import (
    filtros_transacciones,
    stmt_transacciones,
    to_transaccion_out,
)
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_superadmin)])


@router.get("/transacciones", response_model=Pagina[TransaccionOut])
def transacciones_globales(
    desde: date | None = None, hasta: date | None = None,
    tenant_id: int | None = None, sucursal_id: int | None = None,
    cliente: str | None = None, tipo: TipoMovimiento | None = None,
    page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=200),
    format: str | None = Query(None, pattern="^csv$"),
    db: Session = Depends(get_db),
):
    """Monitor global de transacciones: solo lectura, filtros combinables, CSV."""
    filtros = filtros_transacciones(desde, hasta, tenant_id, sucursal_id, cliente, tipo)
    stmt = stmt_transacciones(filtros)
    if format == "csv":
        rows = db.execute(stmt).all()
        return csv_response(
            "transacciones.csv",
            ["id", "fecha", "socio", "sucursal", "cliente", "ci", "tipo", "puntos", "ejecutado_por", "premio"],
            [(r.id, r.created_at, r.socio or "", r.sucursal or "", r.cliente_nombre, r.cliente_ci,
              r.tipo.value, r.puntos, r.ejecutado_por or "", r.premio or "") for r in rows],
        )
    total = db.scalar(
        select(func.count(MovimientoPuntos.id))
        .join(Cliente, MovimientoPuntos.cliente_id == Cliente.id)
        .where(*filtros)
    ) or 0
    rows = db.execute(stmt.offset((page - 1) * size).limit(size)).all()
    return Pagina(items=[to_transaccion_out(r) for r in rows], total=total, page=page, size=size)


@router.get("/socios/{tenant_id}/rendimiento", response_model=KpisSocio)
def rendimiento_socio(tenant_id: int, desde: date | None = None, hasta: date | None = None,
                      db: Session = Depends(get_db)):
    return calcular_kpis_socio(db, tenant_id, desde, hasta)


def _ttfs_medio(db: Session) -> float | None:
    """Tiempo medio (horas) desde el alta del socio hasta su primer giro de ruleta."""
    from app.services.kpis import horas_a_primer_giro
    tenants = db.scalars(select(Tenant)).all()
    valores = [h for t in tenants if (h := horas_a_primer_giro(db, t)) is not None]
    return round(sum(valores) / len(valores), 1) if valores else None


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    hoy = datetime.combine(date.today(), time.min)
    hace_30 = hoy - timedelta(days=29)

    facturas_pend = db.execute(
        select(
            func.count(FacturaPlan.id),
            func.coalesce(func.sum(FacturaPlan.monto), 0)
        ).where(FacturaPlan.estado.in_([EstadoFactura.pendiente, EstadoFactura.vencida]))
    ).first()
    cnt_facturas_pend = facturas_pend[0] if facturas_pend else 0
    monto_facturas_pend = float(facturas_pend[1]) if facturas_pend else 0.0

    kpis = KpisGlobales(
        socios_activos=db.scalar(select(func.count(Tenant.id)).where(Tenant.estado == EstadoTenant.activo)) or 0,
        socios_suspendidos=db.scalar(select(func.count(Tenant.id)).where(Tenant.estado == EstadoTenant.suspendido)) or 0,
        transacciones_hoy=db.scalar(
            select(func.count(MovimientoPuntos.id)).where(MovimientoPuntos.created_at >= hoy)
        ) or 0,
        liquidaciones_pendientes=db.scalar(
            select(func.count(Liquidacion.id)).where(Liquidacion.estado == EstadoLiquidacion.pendiente)
        ) or 0,
        monto_pendiente=float(db.scalar(
            select(func.coalesce(func.sum(Liquidacion.monto_total), 0))
            .where(Liquidacion.estado == EstadoLiquidacion.pendiente)
        ) or 0),
        clientes_totales=db.scalar(select(func.count(Cliente.id))) or 0,
        ttfs_medio_h=_ttfs_medio(db),
        facturas_pendientes=cnt_facturas_pend,
        monto_facturacion_pendiente=monto_facturas_pend,
    )

    # Serie diaria 30d
    por_dia = db.execute(
        select(func.date(MovimientoPuntos.created_at), func.count(MovimientoPuntos.id))
        .where(MovimientoPuntos.created_at >= hace_30)
        .group_by(func.date(MovimientoPuntos.created_at))
    ).all()
    mapa = {str(f): c for f, c in por_dia}
    serie = [
        SerieDia(fecha=(hace_30 + timedelta(days=i)).date().isoformat(),
                 total=mapa.get((hace_30 + timedelta(days=i)).date().isoformat(), 0))
        for i in range(30)
    ]

    # Distribución por tipo de transacción (últimos 30 días)
    tipos_rows = db.execute(
        select(MovimientoPuntos.tipo, func.count(MovimientoPuntos.id))
        .where(MovimientoPuntos.created_at >= hace_30)
        .group_by(MovimientoPuntos.tipo)
    ).all()
    total_movs_30d = sum(c for _, c in tipos_rows) or 1
    distribucion_tipos = [
        DistribucionTipoItem(
            tipo=t.value if hasattr(t, "value") else str(t),
            cantidad=c,
            porcentaje=round((c / total_movs_30d) * 100, 1),
        )
        for t, c in tipos_rows
    ]
    distribucion_tipos.sort(key=lambda x: x.cantidad, reverse=True)

    # Top Socios por volumen de transacciones
    top_tenants_rows = db.execute(
        select(
            Tenant.id,
            Tenant.nombre_comercial,
            Tenant.logo_url,
            func.count(MovimientoPuntos.id).label("total_tx"),
            func.count(func.distinct(MovimientoPuntos.cliente_id)).label("total_cli"),
        )
        .join(Tenant, MovimientoPuntos.tenant_id == Tenant.id)
        .group_by(Tenant.id, Tenant.nombre_comercial, Tenant.logo_url)
        .order_by(func.count(MovimientoPuntos.id).desc())
        .limit(5)
    ).all()

    top_socios = [
        TopSocioItem(
            id=r.id,
            nombre=r.nombre_comercial,
            logo_url=r.logo_url,
            transacciones=r.total_tx,
            clientes=r.total_cli,
        )
        for r in top_tenants_rows
    ]

    ultimas = db.execute(stmt_transacciones([]).limit(10)).all()
    return DashboardOut(
        kpis=kpis,
        transacciones_30d=serie,
        ultimas_transacciones=[to_transaccion_out(r) for r in ultimas],
        top_socios=top_socios,
        distribucion_tipos=distribucion_tipos,
    )

