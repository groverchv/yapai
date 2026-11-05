from app.core.deps import require_superadmin
from app.db.session import get_db
from app.models import Plan, Tenant, Usuario
from app.schemas.admin import PlanIn, PlanOut, PlanUpdate
from app.services.audit import registrar_audit
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_superadmin)])


def _out(db: Session, p: Plan) -> PlanOut:
    asignados = db.scalar(
        select(func.count(Tenant.id)).where(Tenant.plan_id == p.id)
    ) or 0
    return PlanOut(
        id=p.id, slug=p.slug, nombre=p.nombre, descripcion=p.descripcion,
        precio_mensual=float(p.precio_mensual), moneda=p.moneda,
        max_sucursales=p.max_sucursales, max_pantallas=p.max_pantallas,
        max_clientes=p.max_clientes, max_empleados=p.max_empleados,
        ruleta_habilitada=p.ruleta_habilitada, orden=p.orden, activo=p.activo,
        tenants_asignados=asignados,
    )


@router.get("", response_model=list[PlanOut])
def listar_planes(db: Session = Depends(get_db)):
    rows = db.scalars(select(Plan).order_by(Plan.orden, Plan.id)).all()
    return [_out(db, p) for p in rows]


@router.post("", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def crear_plan(data: PlanIn, db: Session = Depends(get_db),
               admin: Usuario = Depends(require_superadmin)):
    if db.scalar(select(Plan).where(Plan.slug == data.slug)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un plan con ese slug")
    p = Plan(**data.model_dump())
    db.add(p)
    db.flush()
    registrar_audit(db, admin.id, "crear_plan", "plan", p.id)
    db.commit()
    return _out(db, p)


@router.patch("/{plan_id}", response_model=PlanOut)
def editar_plan(plan_id: int, data: PlanUpdate, db: Session = Depends(get_db),
                admin: Usuario = Depends(require_superadmin)):
    p = db.get(Plan, plan_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(p, campo, valor)
    registrar_audit(db, admin.id, "editar_plan", "plan", p.id,
                    data.model_dump(exclude_unset=True))
    db.commit()
    return _out(db, p)
