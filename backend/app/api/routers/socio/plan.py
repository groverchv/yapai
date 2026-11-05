from datetime import datetime, timezone

from app.core.deps import require_owner
from app.db.session import get_db
from app.models import Tenant, Usuario
from app.schemas.socio import PlanLimitesOut, PlanUsoOut, SocioPlanOut
from app.services.planes import plan_de, uso_actual
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_owner)])


@router.get("", response_model=SocioPlanOut)
def mi_plan(usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    """Plan actual del socio + uso vs límites + estado del trial."""
    tenant = db.get(Tenant, usuario.tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant no encontrado")
    plan = plan_de(db, tenant)
    uso = uso_actual(db, tenant.id)
    ahora = datetime.now(timezone.utc)
    fin = tenant.trial_fin
    if fin and fin.tzinfo is None:
        fin = fin.replace(tzinfo=timezone.utc)
    en_trial = bool(fin and fin > ahora)
    dias = max(0, (fin - ahora).days) if fin else 0
    return SocioPlanOut(
        plan_id=plan.id if plan else None,
        plan_nombre=plan.nombre if plan else None,
        plan_slug=plan.slug if plan else None,
        precio_mensual=float(plan.precio_mensual) if plan else None,
        moneda=plan.moneda if plan else "BOB",
        limites=PlanLimitesOut(
            max_sucursales=plan.max_sucursales, max_pantallas=plan.max_pantallas,
            max_clientes=plan.max_clientes, max_empleados=plan.max_empleados,
            ruleta_habilitada=plan.ruleta_habilitada,
        ) if plan else None,
        uso=PlanUsoOut(**uso),
        en_trial=en_trial, dias_trial=dias, trial_fin=tenant.trial_fin,
    )
