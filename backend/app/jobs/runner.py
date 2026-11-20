"""Runner de jobs en proceso separado.

En despliegues multi-instancia/multi-worker la API corre con JOBS_ENABLED=false
y este proceso es el único que ejecuta los loops periódicos, evitando jobs
duplicados (doble facturación, doble expiración, doble email):

    python -m app.jobs.runner

Servicio dedicado en deploy/docker-compose.prod.yml (`jobs`).
"""
import asyncio
import logging
import signal

from app.jobs.expiracion import loop_expiracion
from app.jobs.facturacion import loop_facturacion
from app.jobs.limpieza import loop_limpieza
from app.jobs.puntos_ttl import loop_puntos_ttl

logger = logging.getLogger(__name__)


async def main() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            # Windows no soporta add_signal_handler — Ctrl+C llega como KeyboardInterrupt
            pass
    tareas = [
        asyncio.create_task(loop_expiracion(stop)),
        asyncio.create_task(loop_facturacion(stop)),
        asyncio.create_task(loop_limpieza(stop)),
        asyncio.create_task(loop_puntos_ttl(stop)),
    ]
    logger.info("Runner de jobs iniciado (expiración pases 5min, facturación 1h, limpieza+ttl puntos diario)")
    try:
        await stop.wait()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        await asyncio.gather(*tareas)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
