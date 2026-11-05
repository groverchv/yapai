from app.core.deps import require_owner
from app.db.session import get_db
from app.models import (
    EstadoPremio,
    MovimientoPuntos,
    Pantalla,
    Premio,
    RolUsuario,
    RuletaSegmento,
    Sucursal,
    Tenant,
    TipoMovimiento,
    Usuario,
)
from app.schemas.socio import OnboardingOut, PasoOnboarding
from app.services.planes import plan_de
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_owner)])


@router.get("", response_model=OnboardingOut)
def onboarding(usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    """Checklist de activación del socio (wizard del dashboard)."""
    tenant = db.get(Tenant, usuario.tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant no encontrado")
    tid = tenant.id
    plan = plan_de(db, tenant)

    tiene_sucursal = db.scalar(select(func.count(Sucursal.id)).where(Sucursal.tenant_id == tid)) > 0
    tiene_pantalla = db.scalar(
        select(func.count(Pantalla.id))
        .join(Sucursal, Pantalla.sucursal_id == Sucursal.id)
        .where(Sucursal.tenant_id == tid)
    ) > 0
    tiene_premio = db.scalar(select(func.count(Premio.id)).where(
        Premio.tenant_id == tid, Premio.estado == EstadoPremio.activo)) > 0
    tiene_cajero = db.scalar(select(func.count(Usuario.id)).where(
        Usuario.tenant_id == tid, Usuario.rol == RolUsuario.cajero)) > 0
    primer_giro = db.scalar(select(func.count(MovimientoPuntos.id)).where(
        MovimientoPuntos.tenant_id == tid, MovimientoPuntos.tipo == TipoMovimiento.ruleta)) > 0

    pasos = [
        PasoOnboarding(clave="sucursal", etiqueta="Crea tu primera sucursal",
                       hecho=bool(tiene_sucursal), href="/sucursales"),
        PasoOnboarding(clave="pantalla", etiqueta="Registra una pantalla de kiosco",
                       hecho=bool(tiene_pantalla), href="/sucursales"),
        PasoOnboarding(clave="premio", etiqueta="Crea tu primer premio canjeable",
                       hecho=bool(tiene_premio), href="/premios"),
    ]
    if not plan or plan.ruleta_habilitada:
        tiene_ruleta = db.scalar(select(func.count(RuletaSegmento.id)).where(
            RuletaSegmento.tenant_id == tid, RuletaSegmento.activo == True)) > 0  # noqa: E712
        pasos.append(PasoOnboarding(clave="ruleta", etiqueta="Configura la ruleta del kiosco",
                                    hecho=bool(tiene_ruleta), href="/ruleta"))
    pasos += [
        PasoOnboarding(clave="empleado", etiqueta="Invita a un cajero",
                       hecho=bool(tiene_cajero), href="/empleados"),
        PasoOnboarding(clave="primer_giro", etiqueta="Primer cliente girando la ruleta",
                       hecho=bool(primer_giro), href=None),
    ]
    completados = sum(1 for p in pasos if p.hecho)
    return OnboardingOut(
        pasos=pasos, completados=completados,
        total=len(pasos), completado=completados == len(pasos),
    )
