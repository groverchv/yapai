from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_owner
from app.db.session import get_db
from app.models import (
    Cliente, EstadoPremio, MovimientoPuntos, Premio, RolUsuario,
    Sucursal, TipoMovimiento, Usuario,
)
from app.schemas.admin import Pagina, TransaccionOut
from app.schemas.socio import PremioStockBajo, ResumenSocio
from app.services.export import csv_response
from app.services.kpis import calcular_kpis_socio
from app.services.transacciones import (
    filtros_transacciones, stmt_transacciones, to_transaccion_out,
)

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
    return ResumenSocio(
        clientes_nuevos=kpis.clientes_nuevos,
        puntos_otorgados=kpis.puntos_emitidos,
        puntos_consumidos=kpis.puntos_consumidos,
        canjes_exitosos=kpis.canjes_exitosos,
        stock_critico=[PremioStockBajo(id=p.id, nombre=p.nombre, stock=p.stock or 0)
                       for p in stock_bajo],
    )


@router.get("/transacciones", response_model=Pagina[TransaccionOut])
def transacciones_local(
    desde: date | None = None, hasta: date | None = None,
    sucursal_id: int | None = None, cajero_id: int | None = None,
    cliente: str | None = None, tipo: TipoMovimiento | None = None,
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=200),
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
