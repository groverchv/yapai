"""Job de facturación SaaS: genera facturas del período, marca vencidas
y suspende por impago tras el período de gracia.

Corre cada hora dentro de la app (lifespan). Standalone:
`python -m app.jobs.facturacion`.
"""
import asyncio
import logging

from app.db.session import SessionLocal
from app.services.billing import (
    avisar_trials_por_vencer,
    generar_facturas,
    marcar_vencidas,
    suspender_por_impago,
)

logger = logging.getLogger(__name__)

INTERVALO_SEG = 3600  # cada hora


def ejecutar_una_vez() -> dict:
    db = SessionLocal()
    try:
        creadas = generar_facturas(db)
        vencidas = marcar_vencidas(db)
        suspendidos = suspender_por_impago(db)
        avisados = avisar_trials_por_vencer(db)
        db.commit()
        if creadas or vencidas or suspendidos or avisados:
            logger.info(
                "Facturación: %d emitidas, %d vencidas, suspendidos: %s, trials avisados: %d",
                len(creadas), vencidas, suspendidos or "ninguno", avisados,
            )
        return {"emitidas": len(creadas), "vencidas": vencidas,
                "suspendidos": suspendidos, "trials_avisados": avisados}
    finally:
        db.close()


async def loop_facturacion(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await asyncio.to_thread(ejecutar_una_vez)
        except Exception:
            logger.exception("Error en el job de facturación")
        try:
            await asyncio.wait_for(stop.wait(), timeout=INTERVALO_SEG)
        except asyncio.TimeoutError:
            pass


if __name__ == "__main__":
    print(ejecutar_una_vez())
