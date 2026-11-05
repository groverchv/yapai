from app.core.deps import require_owner
from app.db.session import get_db
from app.models import EstadoPase, EstadoPremio, PaseDigital, Premio, Usuario
from app.schemas.socio import PremioIn, PremioOut, PremioUpdate
from app.services.audit import registrar_audit
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_owner)])


def _pases_activos(db: Session, premio_id: int) -> int:
    return db.scalar(
        select(func.count(PaseDigital.id)).where(
            PaseDigital.premio_id == premio_id, PaseDigital.estado == EstadoPase.activo
        )
    ) or 0


def _out(db: Session, p: Premio) -> PremioOut:
    return PremioOut(
        id=p.id, nombre=p.nombre, descripcion=p.descripcion,
        costo_puntos=p.costo_puntos, imagen_url=p.imagen_url,
        stock_limitado=p.stock_limitado, stock=p.stock,
        estado=p.estado.value, pases_activos=_pases_activos(db, p.id),
        vigencia_hasta=p.vigencia_hasta,
    )


def _estado_por_stock(p: Premio) -> EstadoPremio:
    if p.stock_limitado and (p.stock or 0) <= 0:
        return EstadoPremio.agotado
    return EstadoPremio.activo


def _get_premio(db: Session, tenant_id: int, premio_id: int) -> Premio:
    p = db.scalar(select(Premio).where(Premio.id == premio_id, Premio.tenant_id == tenant_id))
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Premio no encontrado")
    return p


@router.get("", response_model=list[PremioOut])
def listar_premios(usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Premio).where(Premio.tenant_id == usuario.tenant_id).order_by(Premio.id)
    ).all()
    return [_out(db, p) for p in rows]


@router.post("", response_model=PremioOut, status_code=status.HTTP_201_CREATED)
def crear_premio(data: PremioIn, usuario: Usuario = Depends(require_owner),
                 db: Session = Depends(get_db)):
    if data.stock_limitado and data.stock is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Stock requerido si el inventario es limitado")
    p = Premio(tenant_id=usuario.tenant_id, **data.model_dump())
    p.estado = _estado_por_stock(p)
    db.add(p)
    db.flush()
    registrar_audit(db, usuario.id, "crear_premio", "premio", p.id)
    db.commit()
    return _out(db, p)


@router.patch("/{premio_id}", response_model=PremioOut)
def editar_premio(premio_id: int, data: PremioUpdate,
                  usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    p = _get_premio(db, usuario.tenant_id, premio_id)
    cambios = data.model_dump(exclude_unset=True)

    # Regla #6: costo inmutable si hay pases digitales activos
    if "costo_puntos" in cambios and cambios["costo_puntos"] != p.costo_puntos:
        activos = _pases_activos(db, p.id)
        if activos > 0:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"No se puede cambiar el costo: hay {activos} pase(s) activo(s) pendientes de canje.",
            )

    for campo, valor in cambios.items():
        setattr(p, campo, valor)

    # Recalcular estado según stock (regla #10)
    if p.estado != EstadoPremio.inactivo:
        p.estado = _estado_por_stock(p)
    registrar_audit(db, usuario.id, "editar_premio", "premio", p.id, cambios)
    db.commit()
    return _out(db, p)


@router.post("/{premio_id}/desactivar", response_model=PremioOut)
def desactivar_premio(premio_id: int, usuario: Usuario = Depends(require_owner),
                      db: Session = Depends(get_db)):
    p = _get_premio(db, usuario.tenant_id, premio_id)
    p.estado = EstadoPremio.inactivo
    registrar_audit(db, usuario.id, "desactivar_premio", "premio", p.id)
    db.commit()
    return _out(db, p)


@router.post("/{premio_id}/activar", response_model=PremioOut)
def activar_premio(premio_id: int, usuario: Usuario = Depends(require_owner),
                   db: Session = Depends(get_db)):
    p = _get_premio(db, usuario.tenant_id, premio_id)
    p.estado = _estado_por_stock(p)
    registrar_audit(db, usuario.id, "activar_premio", "premio", p.id)
    db.commit()
    return _out(db, p)
