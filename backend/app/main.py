import asyncio
import logging
from contextlib import asynccontextmanager

from app.api.routers import api_router
from app.core.config import settings
from app.core.cookies import auth_via_cookie
from app.core.headers import SecurityHeadersMiddleware
from app.core.observability import (
    ObservabilityMiddleware,
    init_sentry,
    metrics_response,
)
from app.jobs.expiracion import loop_expiracion
from app.jobs.facturacion import loop_facturacion
from app.jobs.limpieza import loop_limpieza
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class CsrfCookieMiddleware(BaseHTTPMiddleware):
    """CSRF guard para requests autenticados por cookie.

    SameSite=Lax ya impide que un sitio externo envíe las cookies en un POST
    cross-site; este header custom es defensa en profundidad (un origen externo
    no puede agregarlo sin superar el preflight CORS). Los clients Bearer no
    están sujetos (Authorization no es credencial ambiental del navegador).

    Solo aplica a rutas autenticadas: las rutas públicas de auth (login, signup,
    refresh…) no usan la cookie como credencial y quedan exentas — en ellas una
    cookie residual no amplifica nada.
    """

    _RUTAS_PUBLICAS = frozenset({
        "/api/v1/auth/login", "/api/v1/auth/login/2fa", "/api/v1/auth/signup",
        "/api/v1/auth/refresh", "/api/v1/auth/logout",
        "/api/v1/auth/forgot-password", "/api/v1/auth/reset-password",
        "/api/v1/auth/onboarding",
        "/api/v1/auth/cliente/login", "/api/v1/auth/cliente/registro",
        "/api/v1/auth/cliente/otp/verificar", "/api/v1/auth/planes",
        "/api/v1/webhooks/stripe",
    })

    async def dispatch(self, request: Request, call_next):
        if (request.method not in ("GET", "HEAD", "OPTIONS")
                and request.url.path not in self._RUTAS_PUBLICAS
                and auth_via_cookie(request)
                and not request.headers.get("x-requested-with")):
            return JSONResponse(
                {"detail": "Falta el header X-Requested-With (protección CSRF)"},
                status_code=403,
            )
        return await call_next(request)

init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Jobs en background: expiración de pases (5 min) + facturación/mora (1 h).
    # En despliegues multi-instancia JOBS_ENABLED=false aquí y corren como
    # proceso aparte (`python -m app.jobs.runner`) para no duplicarlos.
    stop = asyncio.Event()
    tareas = []
    if settings.JOBS_ENABLED:
        tareas = [
            asyncio.create_task(loop_expiracion(stop)),
            asyncio.create_task(loop_facturacion(stop)),
            asyncio.create_task(loop_limpieza(stop)),
        ]
    yield
    stop.set()
    await asyncio.gather(*tareas)


_docs = settings.docs_habilitados
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API para Yapai (FastAPI + PostgreSQL)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if _docs else None,
    redoc_url="/redoc" if _docs else None,
    openapi_url="/openapi.json" if _docs else None,
)

# CORS: en producción definir CORS_ORIGINS en .env (coma-separado, nunca *)
_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_credentials="*" not in _origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ObservabilityMiddleware)
app.add_middleware(CsrfCookieMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.include_router(api_router, prefix="/api/v1")

if settings.JWT_SECRET == "yapai-dev-secret-cambiar-en-produccion":
    logging.getLogger("yapai").warning(
        "JWT_SECRET usa el valor por defecto de desarrollo — definí uno propio en .env antes de producción"
    )

if settings.ENV == "production" and not settings.REDIS_URL:
    logging.getLogger("yapai").warning(
        "REDIS_URL no definido en producción — el rate limiting corre en memoria "
        "y no se comparte entre instancias/workers"
    )

if settings.ENV == "production" and settings.SIGNUP_MODE == "auto":
    logging.getLogger("yapai").warning(
        "SIGNUP_MODE=auto en producción — los tenants se activan sin revisión "
        "ni verificación de email. Considera SIGNUP_MODE=manual."
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
        "docs_url": "/docs" if _docs else None,
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/status", include_in_schema=False)
def status_check():
    """Status público para páginas de estado/monitoreo externo.

    Incluye chequeo real de DB (SELECT 1) — si la DB cae, devuelve 503
    para que el monitor lo detecte.
    """
    from app.db.session import SessionLocal
    from sqlalchemy import text as _text

    db_ok = True
    try:
        db = SessionLocal()
        try:
            db.execute(_text("SELECT 1"))
        finally:
            db.close()
    except Exception:
        db_ok = False
    payload = {"status": "operational" if db_ok else "degraded",
               "version": "1.0.0", "db": "up" if db_ok else "down"}
    from fastapi.responses import JSONResponse
    return JSONResponse(payload, status_code=200 if db_ok else 503)
