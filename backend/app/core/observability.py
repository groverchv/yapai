"""Observabilidad: request-id, access logs JSON y métricas Prometheus.

- Cada request recibe/propaga X-Request-ID (contextvar + header de respuesta).
- Access log por request: JSON si LOG_JSON=true (producción), línea simple en dev.
- Métricas en /metrics: conteo por ruta+status y histograma de latencia.
- Sentry se activa solo si SENTRY_DSN está configurado.
"""
import json
import logging
import time
import uuid
from contextvars import ContextVar

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

REQUESTS = Counter(
    "yapai_http_requests_total", "Requests HTTP",
    ["method", "path", "status"],
)
LATENCY = Histogram(
    "yapai_http_request_duration_seconds", "Latencia por request (s)",
    ["method", "path"], buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)

logger = logging.getLogger("yapai.access")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request_id_ctx.set(rid)
        t0 = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - t0) * 1000
        # path templado ("/admin/socios/{id}") para no explotar la cardinalidad
        ruta = getattr(request.scope.get("route"), "path", request.url.path)
        REQUESTS.labels(request.method, ruta, response.status_code).inc()
        LATENCY.labels(request.method, ruta).observe(ms / 1000)
        response.headers["X-Request-ID"] = rid
        if settings.LOG_JSON:
            logger.info(json.dumps({
                "request_id": rid, "method": request.method, "path": ruta,
                "status": response.status_code, "ms": round(ms, 1),
                "ip": request.client.host if request.client else None,
            }))
        else:
            logger.info("%s %s -> %s (%.0fms) [%s]",
                        request.method, ruta, response.status_code, ms, rid)
        return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def init_sentry() -> None:
    """Activa Sentry solo si hay DSN configurado (prod/staging)."""
    if not settings.SENTRY_DSN:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
    except ImportError:
        logging.getLogger("yapai").warning(
            "SENTRY_DSN definido pero sentry-sdk no está instalado")
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE,
        environment=settings.ENV,
        send_default_pii=False,
    )
