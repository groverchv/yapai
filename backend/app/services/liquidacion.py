from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    EstadoLiquidacion, EstadoPase, EsquemaComision, Liquidacion,
    MovimientoPuntos, PaseDigital, Tenant, TipoMovimiento,
)
from app.services.audit import registrar_audit


def rango_periodo(periodo: str) -> tuple[datetime, datetime]:
    """'YYYY-MM' -> (primer día del mes, primer día del mes siguiente)."""
    inicio = datetime.strptime(periodo, "%Y-%m")
    fin = (inicio.replace(day=28) + timedelta(days=4)).replace(day=1)
    return inicio, fin


def generar_liquidaciones(db: Session, periodo: str, actor_id: int) -> dict:
    """Calcula el cobro de cada tenant activo para el periodo (regla #12).

    Monto = (Clientes Nuevos × Costo Registro) + (Canjes Validados × Costo Canje)
    Idempotente: actualiza pendientes, no toca las ya pagadas.
    """
    inicio, fin = rango_periodo(periodo)
    tenants = db.scalars(select(Tenant)).all()
    generadas = actualizadas = omitidas = 0

    for tenant in tenants:
        clientes_nuevos = db.scalar(
            select(func.count(MovimientoPuntos.id)).where(
                MovimientoPuntos.tenant_id == tenant.id,
                MovimientoPuntos.tipo == TipoMovimiento.registro,
                MovimientoPuntos.created_at >= inicio,
                MovimientoPuntos.created_at < fin,
            )
        ) or 0
        canjes = db.scalar(
            select(func.count(PaseDigital.id)).where(
                PaseDigital.tenant_id == tenant.id,
                PaseDigital.estado == EstadoPase.canjeado,
                PaseDigital.canjeado_en >= inicio,
                PaseDigital.canjeado_en < fin,
            )
        ) or 0

        esquema = db.get(EsquemaComision, tenant.esquema_comision_id) if tenant.esquema_comision_id else None
        costo_reg = float(esquema.costo_registro) if esquema else 0.0
        costo_canje = float(esquema.costo_canje) if esquema else 0.0
        moneda = esquema.moneda if esquema else "BOB"
        monto = clientes_nuevos * costo_reg + canjes * costo_canje

        existente = db.scalar(
            select(Liquidacion).where(
                Liquidacion.tenant_id == tenant.id, Liquidacion.periodo == periodo
            )
        )
        if existente:
            if existente.estado == EstadoLiquidacion.pagada:
                omitidas += 1
                continue
            existente.clientes_nuevos = clientes_nuevos
            existente.canjes_validados = canjes
            existente.costo_registro_unit = costo_reg
            existente.costo_canje_unit = costo_canje
            existente.monto_total = monto
            existente.moneda = moneda
            actualizadas += 1
        else:
            db.add(Liquidacion(
                tenant_id=tenant.id, periodo=periodo,
                clientes_nuevos=clientes_nuevos, canjes_validados=canjes,
                costo_registro_unit=costo_reg, costo_canje_unit=costo_canje,
                monto_total=monto, moneda=moneda,
            ))
            generadas += 1

    registrar_audit(db, actor_id, "generar_liquidaciones", "liquidacion", None,
                    {"periodo": periodo, "generadas": generadas,
                     "actualizadas": actualizadas, "omitidas_pagadas": omitidas})
    return {"periodo": periodo, "generadas": generadas,
            "actualizadas": actualizadas, "omitidas_pagadas": omitidas}
