"""Job de expiración de pases digitales.

Corre en background dentro de la app (lifespan). En producción puede
alternativamente ejecutarse como cron: `python -m app.jobs.expiracion`.
"""

import asyncio
import logging

from app.db.session import SessionLocal
from app.services.puntos import expirar_pases_vencidos

logger = logging.getLogger(__name__)

INTERVALO_SEG = 300  # cada 5 minutos


def ejecutar_una_vez() -> int:
    db = SessionLocal()
    try:
        n = expirar_pases_vencidos(db)
        if n:
            logger.info("Expiración: %d pases liberados", n)
        return n
    finally:
        db.close()


async def loop_expiracion(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await asyncio.to_thread(ejecutar_una_vez)
        except Exception:
            logger.exception("Error en job de expiración de pases")
        try:
            await asyncio.wait_for(stop.wait(), timeout=INTERVALO_SEG)
        except asyncio.TimeoutError:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"Pases expirados liberados: {ejecutar_una_vez()}")
