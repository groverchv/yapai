from app.core.deps import get_current_cliente
from app.core.security import utcnow
from app.db.session import get_db
from app.models import (
    CategoriaNegocio,
    Cliente,
    EstadoPremio,
    EstadoSucursal,
    EstadoTenant,
    MovimientoPuntos,
    Premio,
    Sucursal,
    Tenant,
)
from app.schemas.cliente import (
    ComercioDetalleOut,
    ComercioListOut,
    PremioClienteOut,
    SucursalClienteOut,
)
from app.services.puntos import TIPOS_GANANCIA, saldo_disponible
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(get_current_cliente)])


def _tenant_activo(db: Session, tenant_id: int) -> Tenant:
    t = db.scalar(
        select(Tenant).where(Tenant.id == tenant_id, Tenant.estado == EstadoTenant.activo)
    )
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comercio no encontrado")
    return t


@router.get("/comercios", response_model=list[ComercioListOut])
def directorio(q: str | None = None, categoria_id: int | None = None,
               cliente: Cliente = Depends(get_current_cliente),
               db: Session = Depends(get_db)):
    filtros = [Tenant.estado == EstadoTenant.activo]
    if q:
        filtros.append(Tenant.nombre_comercial.ilike(f"%{q}%"))
    if categoria_id:
        filtros.append(Tenant.categoria_id == categoria_id)
    rows = db.execute(
        select(Tenant, CategoriaNegocio.nombre, func.count(Premio.id))
        .join(CategoriaNegocio, Tenant.categoria_id == CategoriaNegocio.id, isouter=True)
        .join(Premio, (Premio.tenant_id == Tenant.id) & (Premio.estado == EstadoPremio.activo),
              isouter=True)
        .where(*filtros)
        .group_by(Tenant.id, CategoriaNegocio.nombre)
        .order_by(Tenant.nombre_comercial)
    ).all()
    # Puntos que el cliente ganó por comercio (un solo aggregate, evita N+1)
    ganados = dict(db.execute(
        select(MovimientoPuntos.tenant_id, func.sum(MovimientoPuntos.puntos))
        .where(MovimientoPuntos.cliente_id == cliente.id,
               MovimientoPuntos.tenant_id.is_not(None),
               MovimientoPuntos.tipo.in_(TIPOS_GANANCIA),
               MovimientoPuntos.puntos > 0)
        .group_by(MovimientoPuntos.tenant_id)
    ).all())
    return [
        ComercioListOut(
            id=t.id, nombre_comercial=t.nombre_comercial, logo_url=t.logo_url,
            categoria=categoria, total_premios=total,
            puntos_ganados=ganados.get(t.id) or 0,
        ) for t, categoria, total in rows
    ]


@router.get("/comercios/categorias", response_model=list[dict])
def categorias(db: Session = Depends(get_db)):
    """Rubros activos para el filtro del explorador."""
    rows = db.scalars(
        select(CategoriaNegocio).where(CategoriaNegocio.activa == True)  # noqa: E712
        .order_by(CategoriaNegocio.nombre)
    ).all()
    return [{"id": c.id, "nombre": c.nombre} for c in rows]


@router.get("/comercios/{tenant_id}", response_model=ComercioDetalleOut)
def detalle_comercio(tenant_id: int, db: Session = Depends(get_db)):
    t = _tenant_activo(db, tenant_id)
    categoria = db.get(CategoriaNegocio, t.categoria_id) if t.categoria_id else None
    sucursales = db.scalars(
        select(Sucursal).where(
            Sucursal.tenant_id == t.id, Sucursal.estado == EstadoSucursal.activa
        ).order_by(Sucursal.nombre)
    ).all()
    return ComercioDetalleOut(
        id=t.id, nombre_comercial=t.nombre_comercial, logo_url=t.logo_url,
        categoria=categoria.nombre if categoria else None,
        sucursales=[SucursalClienteOut(id=s.id, nombre=s.nombre, direccion=s.direccion,
                                     latitud=s.latitud, longitud=s.longitud)
                    for s in sucursales],
    )


@router.get("/comercios/{tenant_id}/premios", response_model=list[PremioClienteOut])
def catalogo(tenant_id: int, cliente: Cliente = Depends(get_current_cliente),
             db: Session = Depends(get_db)):
    _tenant_activo(db, tenant_id)
    ahora = utcnow()
    rows = db.scalars(
        select(Premio).where(
            Premio.tenant_id == tenant_id, Premio.estado == EstadoPremio.activo,
            or_(Premio.vigencia_hasta.is_(None), Premio.vigencia_hasta > ahora),
        ).order_by(Premio.costo_puntos)
    ).all()
    disponible = saldo_disponible(cliente)
    return [
        PremioClienteOut(
            id=p.id, nombre=p.nombre, descripcion=p.descripcion,
            costo_puntos=p.costo_puntos, imagen_url=p.imagen_url,
            alcanzable=p.costo_puntos <= disponible,
            vigencia_hasta=p.vigencia_hasta,
        ) for p in rows
    ]
