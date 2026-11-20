"""Job diario: expira puntos según `tenant.puntos_ttl_meses` (0 = nunca).

Corre solo en el runner dedicado (`python -m app.jobs.runner`) para no
duplicar trabajo en despliegues multi-worker.
"""

import asyncio
import logging

from app.db.session import SessionLocal
from app.models import Tenant
from app.services.puntos import expirar_puntos_viejos
from sqlalchemy import select

logger = logging.getLogger(__name__)

INTERVALO_SEG = 24 * 3600  # una vez al día


def ejecutar_una_vez() -> int:
    total = 0
    db = SessionLocal()
    try:
        tenants = db.scalars(
            select(Tenant).where(Tenant.puntos_ttl_meses > 0)
        ).all()
        for tenant in tenants:
            try:
                n = expirar_puntos_viejos(db, tenant)
                db.commit()
                total += n
                if n:
                    logger.info("Tenant %s: %d puntos expirados", tenant.id, n)
            except Exception:
                db.rollback()
                logger.exception("Falló expiración de puntos tenant %s", tenant.id)
        return total
    finally:
        db.close()


async def loop_puntos_ttl(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await asyncio.to_thread(ejecutar_una_vez)
        except Exception:
            logger.exception("Error en job de expiración de puntos")
        try:
            await asyncio.wait_for(stop.wait(), timeout=INTERVALO_SEG)
        except asyncio.TimeoutError:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"Puntos expirados: {ejecutar_una_vez()}")
