import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import api_router
from app.core.config import settings
from app.core.headers import SecurityHeadersMiddleware
from app.core.observability import (
    ObservabilityMiddleware, init_sentry, metrics_response,
)
from app.jobs.expiracion import loop_expiracion
from app.jobs.facturacion import loop_facturacion

init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Jobs en background: expiración de pases (5 min) + facturación/mora (1 h)
    stop = asyncio.Event()
    tareas = []
    if settings.JOBS_ENABLED:
        tareas = [
            asyncio.create_task(loop_expiracion(stop)),
            asyncio.create_task(loop_facturacion(stop)),
        ]
    yield
    stop.set()
    await asyncio.gather(*tareas)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API para Yapai (FastAPI + PostgreSQL / PostgREST)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: en producción definir CORS_ORIGINS en .env (coma-separado)
_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Backend API Yapai v1.1 - Reload trigger
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.include_router(api_router, prefix="/api/v1")

if settings.JWT_SECRET == "yapai-dev-secret-cambiar-en-produccion":
    logging.getLogger("yapai").warning(
        "JWT_SECRET usa el valor por defecto de desarrollo — definí uno propio en .env antes de producción"
    )


@app.get("/metrics", include_in_schema=False)
def metrics():
    """Métricas Prometheus (scraping interno; proteger en el proxy externo)."""
    return metrics_response()


@app.get("/")
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "postgrest_url": settings.POSTGREST_URL
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
