from datetime import date, datetime, time, timedelta

from app.core.deps import require_owner
from app.db.session import get_db
from app.models import (
    Cliente,
    EstadoPase,
    EstadoPremio,
    MovimientoPuntos,
    PaseDigital,
    Premio,
    RolUsuario,
    Sucursal,
    TipoMovimiento,
    Usuario,
)
from app.schemas.admin import Pagina, SerieDia, TransaccionOut
from app.schemas.socio import (
    PremioStockBajo,
    ResumenPrevio,
    ResumenSocio,
    TopPremioSocio,
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

STOCK_CRITICO = 3

router = APIRouter(dependencies=[Depends(require_owner)])


@router.get("/metricas/resumen", response_model=ResumenSocio)
def resumen(desde: date | None = None, hasta: date | None = None,
            sucursal_id: int | None = None,
            usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    kpis = calcular_kpis_socio(db, usuario.tenant_id, desde, hasta, sucursal_id)
    stock_bajo = db.scalars(
        select(Premio).where(
            Premio.tenant_id == usuario.tenant_id,
            Premio.stock_limitado == True,  # noqa: E712
            Premio.stock <= STOCK_CRITICO,
            Premio.estado != EstadoPremio.inactivo,
        )
    ).all()

    hoy = datetime.combine(date.today(), time.min)
    hace_30 = hoy - timedelta(days=29)

    base_t = [MovimientoPuntos.tenant_id == usuario.tenant_id]
    if sucursal_id:
        base_t.append(MovimientoPuntos.sucursal_id == sucursal_id)

    tx_hoy = db.scalar(
        select(func.count(MovimientoPuntos.id)).where(*base_t, MovimientoPuntos.created_at >= hoy)
    ) or 0

    clientes_totales = db.scalar(
        select(func.count(Cliente.id)).where(Cliente.tenant_registro_id == usuario.tenant_id)
    ) or 0

    pases_activos = db.scalar(
        select(func.count(PaseDigital.id)).where(
            PaseDigital.tenant_id == usuario.tenant_id,
            PaseDigital.estado == EstadoPase.activo,
        )
    ) or 0

    # Serie diaria 30d
    por_dia = db.execute(
        select(func.date(MovimientoPuntos.created_at), func.count(MovimientoPuntos.id))
        .where(*base_t, MovimientoPuntos.created_at >= hace_30)
        .group_by(func.date(MovimientoPuntos.created_at))
    ).all()
    mapa = {str(f): c for f, c in por_dia}
    serie = [
        SerieDia(fecha=(hace_30 + timedelta(days=i)).date().isoformat(),
                 total=mapa.get((hace_30 + timedelta(days=i)).date().isoformat(), 0))
        for i in range(30)
    ]

    # Top Premios más canjeados
    top_premios_rows = db.execute(
        select(
            Premio.id, Premio.nombre, Premio.costo_puntos, Premio.stock, Premio.imagen_url,
            func.count(MovimientoPuntos.id).label("total_canjes")
        )
        .outerjoin(MovimientoPuntos, MovimientoPuntos.premio_id == Premio.id)
        .where(Premio.tenant_id == usuario.tenant_id, Premio.estado != EstadoPremio.inactivo)
        .group_by(Premio.id, Premio.nombre, Premio.costo_puntos, Premio.stock, Premio.imagen_url)
        .order_by(func.count(MovimientoPuntos.id).desc(), Premio.id)
        .limit(6)
    ).all()

    top_premios = [
        TopPremioSocio(
            id=r[0], nombre=r[1], costo_puntos=r[2], stock=r[3], imagen_url=r[4], total_canjes=r[5]
        )
        for r in top_premios_rows
    ]

    tasa_redencion = 0.0
    if kpis.puntos_emitidos > 0:
        tasa_redencion = round((kpis.puntos_consumidos / kpis.puntos_emitidos) * 100, 1)

    # Período espejo anterior para los Δ% del dashboard (solo con rango explícito)
    previos = None
    if desde and hasta:
        dias = (hasta - desde).days + 1
        kpis_prev = calcular_kpis_socio(
            db, usuario.tenant_id,
            desde - timedelta(days=dias), desde - timedelta(days=1), sucursal_id,
        )
        previos = ResumenPrevio(
            clientes_nuevos=kpis_prev.clientes_nuevos,
            puntos_otorgados=kpis_prev.puntos_emitidos,
            puntos_consumidos=kpis_prev.puntos_consumidos,
            canjes_exitosos=kpis_prev.canjes_exitosos,
        )

    return ResumenSocio(
        clientes_nuevos=kpis.clientes_nuevos,
        puntos_otorgados=kpis.puntos_emitidos,
        puntos_consumidos=kpis.puntos_consumidos,
        canjes_exitosos=kpis.canjes_exitosos,
        stock_critico=[PremioStockBajo(id=p.id, nombre=p.nombre, stock=p.stock or 0)
                       for p in stock_bajo],
        clientes_totales=clientes_totales,
        tasa_redencion=tasa_redencion,
        transacciones_hoy=tx_hoy,
        pases_activos=pases_activos,
        transacciones_30d=serie,
        top_premios=top_premios,
        previos=previos,
    )


@router.get("/transacciones", response_model=Pagina[TransaccionOut])
def transacciones_local(
    desde: date | None = None, hasta: date | None = None,
    sucursal_id: int | None = None, cajero_id: int | None = None,
    cliente: str | None = None, tipo: TipoMovimiento | None = None,
    page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=200),
    format: str | None = Query(None, pattern="^csv$"),
    usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db),
):
    """Auditoría del local: ledger inmutable de solo lectura."""
    filtros = filtros_transacciones(
        desde, hasta, usuario.tenant_id, sucursal_id, cliente, tipo, cajero_id
    )
    stmt = stmt_transacciones(filtros)
    if format == "csv":
        rows = db.execute(stmt).all()
        return csv_response(
            "transacciones_local.csv",
            ["id", "fecha", "sucursal", "cliente", "ci", "tipo", "puntos", "cajero", "premio"],
            [(r.id, r.created_at, r.sucursal or "", r.cliente_nombre, r.cliente_ci,
              r.tipo.value, r.puntos, r.ejecutado_por or "", r.premio or "") for r in rows],
        )
    total = db.scalar(
        select(func.count(MovimientoPuntos.id))
        .join(Cliente, MovimientoPuntos.cliente_id == Cliente.id)
        .where(*filtros)
    ) or 0
    rows = db.execute(stmt.offset((page - 1) * size).limit(size)).all()
    return Pagina(items=[to_transaccion_out(r) for r in rows], total=total, page=page, size=size)


@router.get("/transacciones/filtros", response_model=dict)
def opciones_filtros(usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    """Sucursales y cajeros del tenant para poblar los selects de filtro."""
    sucursales = db.scalars(
        select(Sucursal).where(Sucursal.tenant_id == usuario.tenant_id).order_by(Sucursal.nombre)
    ).all()
    cajeros = db.scalars(
        select(Usuario).where(
            Usuario.tenant_id == usuario.tenant_id, Usuario.rol == RolUsuario.cajero
        ).order_by(Usuario.nombre)
    ).all()
    return {
        "sucursales": [{"id": s.id, "nombre": s.nombre} for s in sucursales],
        "cajeros": [{"id": c.id, "nombre": c.nombre} for c in cajeros],
    }
