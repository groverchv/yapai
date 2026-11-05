from app.core.deps import require_superadmin
from app.core.security import utcnow
from app.db.session import get_db
from app.models import EstadoLiquidacion, Liquidacion, Tenant, Usuario
from app.schemas.admin import (
    GenerarLiquidacionesIn,
    LiquidacionGenerada,
    LiquidacionOut,
    Pagina,
)
from app.services.audit import registrar_audit
from app.services.liquidacion import generar_liquidaciones
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_superadmin)])


def _out(db: Session, liq: Liquidacion) -> LiquidacionOut:
    socio = db.get(Tenant, liq.tenant_id)
    aprobador = db.get(Usuario, liq.aprobada_por) if liq.aprobada_por else None
    return LiquidacionOut(
        id=liq.id, tenant_id=liq.tenant_id,
        socio=socio.nombre_comercial if socio else f"#{liq.tenant_id}",
        periodo=liq.periodo, clientes_nuevos=liq.clientes_nuevos,
        canjes_validados=liq.canjes_validados,
        costo_registro_unit=float(liq.costo_registro_unit),
        costo_canje_unit=float(liq.costo_canje_unit),
        monto_total=float(liq.monto_total), moneda=liq.moneda,
        estado=liq.estado.value,
        pagada_en=liq.pagada_en,
        aprobada_por=aprobador.nombre if aprobador else None,
        created_at=liq.created_at,
    )


@router.get("", response_model=Pagina[LiquidacionOut])
def listar_liquidaciones(
    periodo: str | None = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    estado: EstadoLiquidacion | None = None,
    tenant_id: int | None = None,
    page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
):
    filtros = []
    if periodo:
        filtros.append(Liquidacion.periodo == periodo)
    if estado:
        filtros.append(Liquidacion.estado == estado)
    if tenant_id:
        filtros.append(Liquidacion.tenant_id == tenant_id)
    total = db.scalar(select(func.count(Liquidacion.id)).where(*filtros)) or 0
    rows = db.scalars(
        select(Liquidacion).where(*filtros)
        .order_by(Liquidacion.periodo.desc(), Liquidacion.id.desc())
        .offset((page - 1) * size).limit(size)
    ).all()
    return Pagina(items=[_out(db, liq) for liq in rows], total=total, page=page, size=size)


@router.post("/generar", response_model=LiquidacionGenerada)
def generar(data: GenerarLiquidacionesIn, db: Session = Depends(get_db),
            admin: Usuario = Depends(require_superadmin)):
    resultado = generar_liquidaciones(db, data.periodo, admin.id)
    db.commit()
    return LiquidacionGenerada(**resultado)


@router.get("/{liquidacion_id}", response_model=LiquidacionOut)
def detalle_liquidacion(liquidacion_id: int, db: Session = Depends(get_db)):
    liq = db.get(Liquidacion, liquidacion_id)
    if not liq:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Liquidación no encontrada")
    return _out(db, liq)


@router.post("/{liquidacion_id}/pagar", response_model=LiquidacionOut)
def marcar_pagada(liquidacion_id: int, db: Session = Depends(get_db),
                  admin: Usuario = Depends(require_superadmin)):
    """Consolidación: marca como pagada auditando al usuario interno (regla #13)."""
    liq = db.get(Liquidacion, liquidacion_id)
    if not liq:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Liquidación no encontrada")
    if liq.estado == EstadoLiquidacion.pagada:
        raise HTTPException(status.HTTP_409_CONFLICT, "La liquidación ya fue pagada")
    liq.estado = EstadoLiquidacion.pagada
    liq.pagada_en = utcnow()
    liq.aprobada_por = admin.id
    registrar_audit(db, admin.id, "marcar_liquidacion_pagada", "liquidacion", liq.id,
                    {"monto": float(liq.monto_total), "periodo": liq.periodo})
    db.commit()
    return _out(db, liq)
