"""Planes SaaS: límites por tenant y estado del trial.

Convenciones:
- Límite 0 = ilimitado.
- Tenant sin plan asignado = sin restricciones (cuentas históricas/admin).
"""
from app.models import Cliente, Pantalla, Plan, Sucursal, Tenant, Usuario
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

RECURSOS = ("sucursales", "pantallas", "clientes", "empleados")


def plan_de(db: Session, tenant: Tenant) -> Plan | None:
    return db.get(Plan, tenant.plan_id) if tenant.plan_id else None


def plan_inicial(db: Session) -> Plan | None:
    """Plan por defecto para signups: slug 'starter' o el activo de menor orden."""
    plan = db.scalar(select(Plan).where(Plan.slug == "starter", Plan.activo == True))  # noqa: E712
    if not plan:
        plan = db.scalar(select(Plan).where(Plan.activo == True).order_by(Plan.orden).limit(1))  # noqa: E712
    return plan


def uso_actual(db: Session, tenant_id: int) -> dict[str, int]:
    return {
        "sucursales": db.scalar(select(func.count(Sucursal.id)).where(
            Sucursal.tenant_id == tenant_id)) or 0,
        "pantallas": db.scalar(select(func.count(Pantalla.id))
            .join(Sucursal, Pantalla.sucursal_id == Sucursal.id)
            .where(Sucursal.tenant_id == tenant_id)) or 0,
        "clientes": db.scalar(select(func.count(Cliente.id)).where(
            Cliente.tenant_registro_id == tenant_id)) or 0,
        "empleados": db.scalar(select(func.count(Usuario.id)).where(
            Usuario.tenant_id == tenant_id)) or 0,
    }


def verificar_limite(db: Session, tenant: Tenant, recurso: str) -> None:
    """403 upgrade_required si el tenant superó el límite de su plan."""
    plan = plan_de(db, tenant)
    limite = getattr(plan, f"max_{recurso}", 0) if plan else 0
    if not limite:
        return
    uso = uso_actual(db, tenant.id)[recurso]
    if uso >= limite:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={
                "code": "upgrade_required",
                "recurso": recurso,
                "limite": limite,
                "uso": uso,
                "mensaje": f"Alcanzaste el límite de {recurso} de tu plan {plan.nombre}. "
                           "Mejora tu plan para continuar.",
            },
        )


def verificar_ruleta(db: Session, tenant: Tenant) -> None:
    """403 si el plan no incluye la ruleta del kiosco."""
    plan = plan_de(db, tenant)
    if plan and not plan.ruleta_habilitada:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={
                "code": "upgrade_required",
                "recurso": "ruleta",
                "mensaje": "La ruleta no está incluida en tu plan. Mejora tu plan para activarla.",
            },
        )
