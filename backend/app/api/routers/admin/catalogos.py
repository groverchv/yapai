from app.core.deps import require_superadmin
from app.core.utils import slugify
from app.db.session import get_db
from app.models import CategoriaNegocio, EsquemaComision, Liquidacion, Tenant, Usuario
from app.schemas.admin import (
    CategoriaIn,
    CategoriaOut,
    CategoriaUpdate,
    EsquemaIn,
    EsquemaOut,
    EsquemaUpdate,
)
from app.services.audit import registrar_audit
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_superadmin)])


# ---------- Categorías de negocio ----------

def _categoria_out(db: Session, cat: CategoriaNegocio) -> CategoriaOut:
    vinculados = db.scalar(
        select(func.count(Tenant.id)).where(Tenant.categoria_id == cat.id)
    ) or 0
    return CategoriaOut(
        id=cat.id, nombre=cat.nombre, slug=cat.slug,
        icono_url=cat.icono_url, activa=cat.activa, socios_vinculados=vinculados,
    )


@router.get("/categorias", response_model=list[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    rows = db.scalars(select(CategoriaNegocio).order_by(CategoriaNegocio.nombre)).all()
    return [_categoria_out(db, c) for c in rows]


@router.post("/categorias", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def crear_categoria(data: CategoriaIn, db: Session = Depends(get_db), admin: Usuario = Depends(require_superadmin)):
    slug = data.slug or slugify(data.nombre)
    if db.scalar(select(CategoriaNegocio).where(CategoriaNegocio.slug == slug)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una categoría con ese slug")
    cat = CategoriaNegocio(nombre=data.nombre, slug=slug, icono_url=data.icono_url, activa=data.activa)
    db.add(cat)
    db.flush()
    registrar_audit(db, admin.id, "crear_categoria", "categoria", cat.id)
    db.commit()
    return _categoria_out(db, cat)


@router.patch("/categorias/{cat_id}", response_model=CategoriaOut)
def editar_categoria(cat_id: int, data: CategoriaUpdate, db: Session = Depends(get_db),
                     admin: Usuario = Depends(require_superadmin)):
    cat = db.get(CategoriaNegocio, cat_id)
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")
    cambios = data.model_dump(exclude_unset=True)
    nuevo_slug = cambios.get("slug")
    if nuevo_slug and nuevo_slug != cat.slug:
        if db.scalar(select(CategoriaNegocio).where(CategoriaNegocio.slug == nuevo_slug, CategoriaNegocio.id != cat.id)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una categoría con ese slug")
    for campo, valor in cambios.items():
        setattr(cat, campo, valor)
    registrar_audit(db, admin.id, "editar_categoria", "categoria", cat.id, cambios)
    db.commit()
    return _categoria_out(db, cat)


@router.delete("/categorias/{cat_id}")
def eliminar_categoria(cat_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(require_superadmin)):
    """Regla #4: no se elimina físicamente si tiene socios vinculados."""
    cat = db.get(CategoriaNegocio, cat_id)
    if not cat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")
    vinculados = db.scalar(select(func.count(Tenant.id)).where(Tenant.categoria_id == cat.id)) or 0
    if vinculados > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"No se puede eliminar: {vinculados} socio(s) vinculado(s). Desactívela en su lugar.",
        )
    registrar_audit(db, admin.id, "eliminar_categoria", "categoria", cat.id, {"nombre": cat.nombre})
    db.delete(cat)
    db.commit()
    return {"detail": "Categoría eliminada"}


# ---------- Esquemas de comisión ----------

def _esquema_out(db: Session, e: EsquemaComision) -> EsquemaOut:
    tenants = db.scalar(select(func.count(Tenant.id)).where(Tenant.esquema_comision_id == e.id)) or 0
    liquidaciones = db.scalar(
        select(func.count(Liquidacion.id))
        .join(Tenant, Liquidacion.tenant_id == Tenant.id)
        .where(Tenant.esquema_comision_id == e.id)
    ) or 0
    return EsquemaOut(
        id=e.id, nombre=e.nombre, costo_registro=float(e.costo_registro),
        costo_canje=float(e.costo_canje), moneda=e.moneda, activo=e.activo,
        has_usage=(tenants + liquidaciones) > 0,
    )


@router.get("/esquemas", response_model=list[EsquemaOut])
def listar_esquemas(db: Session = Depends(get_db)):
    rows = db.scalars(select(EsquemaComision).order_by(EsquemaComision.nombre)).all()
    return [_esquema_out(db, e) for e in rows]


@router.post("/esquemas", response_model=EsquemaOut, status_code=status.HTTP_201_CREATED)
def crear_esquema(data: EsquemaIn, db: Session = Depends(get_db), admin: Usuario = Depends(require_superadmin)):
    if db.scalar(select(EsquemaComision).where(EsquemaComision.nombre == data.nombre)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un esquema con ese nombre")
    e = EsquemaComision(**data.model_dump())
    db.add(e)
    db.flush()
    registrar_audit(db, admin.id, "crear_esquema", "esquema", e.id)
    db.commit()
    return _esquema_out(db, e)


@router.patch("/esquemas/{esquema_id}", response_model=EsquemaOut)
def editar_esquema(esquema_id: int, data: EsquemaUpdate, db: Session = Depends(get_db),
                   admin: Usuario = Depends(require_superadmin)):
    e = db.get(EsquemaComision, esquema_id)
    if not e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esquema no encontrado")
    cambios = data.model_dump(exclude_unset=True)

    # Regla #5: con uso, los valores numéricos quedan inmutables
    toca_montos = any(
        k in cambios and getattr(e, k) != cambios[k]
        for k in ("costo_registro", "costo_canje", "moneda")
    )
    if toca_montos and _esquema_out(db, e).has_usage:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Esquema con transacciones/liquidaciones asociadas: los montos son inmutables. Cree un esquema nuevo.",
        )
    for campo, valor in cambios.items():
        setattr(e, campo, valor)
    registrar_audit(db, admin.id, "editar_esquema", "esquema", e.id, cambios)
    db.commit()
    return _esquema_out(db, e)


@router.delete("/esquemas/{esquema_id}")
def eliminar_esquema(esquema_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(require_superadmin)):
    e = db.get(EsquemaComision, esquema_id)
    if not e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esquema no encontrado")
    if _esquema_out(db, e).has_usage:
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede eliminar un esquema en uso")
    registrar_audit(db, admin.id, "eliminar_esquema", "esquema", e.id, {"nombre": e.nombre})
    db.delete(e)
    db.commit()
    return {"detail": "Esquema eliminado"}
