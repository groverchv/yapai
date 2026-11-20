"""Rate limiting por ventana deslizante (memoria) o fija (Redis).

Por defecto corre en memoria — suficiente para una instancia. Si `REDIS_URL`
está definido, usa Redis (INCR+EXPIRE atómico) y los límites se comparten
entre todos los workers/instancias.
"""

import logging
import threading
import time
from collections import defaultdict, deque
from typing import Callable, Protocol

from app.core.config import settings
from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


class _Almacen(Protocol):
    def hit(self, key: str, intentos: int, ventana_seg: int) -> tuple[bool, int]:
        """Registra un intento. Devuelve (permitido, espera_seg_si_bloqueado)."""
        ...


class _AlmacenMemoria:
    def __init__(self):
        self.ventanas: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def hit(self, key: str, intentos: int, ventana_seg: int) -> tuple[bool, int]:
        ahora = time.monotonic()
        with self.lock:
            dq = self.ventanas[key]
            while dq and ahora - dq[0] > ventana_seg:
                dq.popleft()
            if len(dq) >= intentos:
                return False, int(ventana_seg - (ahora - dq[0]))
            dq.append(ahora)
            return True, 0


class _AlmacenRedis:
    def __init__(self, url: str):
        import redis  # dependencia opcional — solo se importa con REDIS_URL

        self._r = redis.Redis.from_url(url, decode_responses=True)

    def hit(self, key: str, intentos: int, ventana_seg: int) -> tuple[bool, int]:
        k = f"rl:{key}:{int(time.time() // ventana_seg)}"
        n = self._r.incr(k)
        if n == 1:
            self._r.expire(k, ventana_seg)
        if n > intentos:
            ttl = self._r.ttl(k)
            return False, max(1, int(ttl))
        return True, 0


def _construir_almacen() -> _Almacen:
    if settings.REDIS_URL:
        try:
            return _AlmacenRedis(settings.REDIS_URL)
        except Exception:
            logger.exception("No se pudo conectar a Redis — rate limiting en memoria")
    return _AlmacenMemoria()


# Compartido por todos los limitadores del proceso
_almacen: _Almacen = _construir_almacen()


class RateLimiter:
    """Permite `intentos` por `ventana_seg` por clave; al exceder, 429."""

    def __init__(self, intentos: int, ventana_seg: int, clave: Callable[[Request], str]):
        self.intentos = intentos
        self.ventana_seg = ventana_seg
        self.clave = clave

    def __call__(self, request: Request) -> None:
        key = f"{request.url.path}:{self.clave(request)}"
        try:
            permitido, espera = _almacen.hit(key, self.intentos, self.ventana_seg)
        except Exception:
            # Redis caído: no bloquear el servicio por el rate limiter
            logger.exception("Rate limiter falló — permitiendo request")
            return
        if not permitido:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"Demasiados intentos. Reintenta en {espera}s.",
            )


def por_ip(request: Request) -> str:
    # Tras --proxy-headers + forwarded_allow_ips, request.client.host ya es la IP
    # real del cliente. Sin proxies de confianza configurados es la conexión directa.
    return request.client.host if request.client else "unknown"


def por_ip_y_path_param(nombre: str):
    """Clave IP + parámetro de ruta (ej. device_token del kiosco)."""
    def clave(request: Request) -> str:
        return f"{por_ip(request)}:{request.path_params.get(nombre, '')}"
    return clave


# Limitadores predefinidos
login_limiter = RateLimiter(intentos=10, ventana_seg=60, clave=por_ip)
# Login de cliente (tel+CI son datos semi-públicos): ventana más estricta
cliente_login_limiter = RateLimiter(intentos=5, ventana_seg=300, clave=por_ip)
# Verificación de OTP: algo más de margen que OTP_MAX_INTENTOS (5) para que
# un intento legítimo tras varios fallos aún pueda llegar al endpoint.
cliente_otp_limiter = RateLimiter(intentos=8, ventana_seg=300, clave=por_ip)
# PIN de caja: 5 intentos → bloqueo 15 min (seguridad, sección 10 del plan)
pin_limiter = RateLimiter(intentos=5, ventana_seg=900, clave=por_ip)
# Signup público: 5 altas/hora por IP (anti-spam de tenants)
signup_limiter = RateLimiter(intentos=5, ventana_seg=3600, clave=por_ip)
# 2FA: código de 6 dígitos — ventana corta anti fuerza bruta
totp_limiter = RateLimiter(intentos=5, ventana_seg=300, clave=por_ip)
# Recuperación/onboarding de contraseña: anti email-bombing y brute force de tokens
recovery_limiter = RateLimiter(intentos=3, ventana_seg=3600, clave=por_ip)
# Refresh/logout: el token va firmado, pero limitamos abuso de endpoint
token_limiter = RateLimiter(intentos=20, ventana_seg=60, clave=por_ip)
# Kiosco: registro y ruleta por IP + pantalla (el device_token va en la URL)
kiosco_limiter = RateLimiter(intentos=30, ventana_seg=300, clave=por_ip_y_path_param("device_token"))
# Webhook Stripe: reintentos legítimos de Stripe + defensa ante ráfagas
webhook_limiter = RateLimiter(intentos=120, ventana_seg=60, clave=por_ip)

# Compat: los tests limpian las ventanas en memoria
_ventanas = getattr(_almacen, "ventanas", {})
