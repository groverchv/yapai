"""Transporte de tokens por cookies HttpOnly (navegadores) o Bearer (otros clientes).

AUTH_TRANSPORT:
- "bearer": solo Authorization header (clientes no-web: apps móviles, scripts).
- "cookie": solo cookies HttpOnly+Secure+SameSite=Lax (navegadores — sin tokens
  en localStorage ⇒ XSS no puede robar sesiones).
- "both": acepta ambos y emite ambos (navegadores usan cookies; el cuerpo JSON
  sigue incluyendo tokens para clientes que los necesiten).

CSRF: SameSite=Lax ya bloquea POST cross-site con cookies; además las mutaciones
autenticadas por cookie exigen el header `X-Requested-With` (un origen externo
no puede añadirlo sin pasar CORS preflight). Ver CsrfCookieMiddleware en main.
"""
from app.core.config import settings
from app.schemas.auth import TokenPair
from fastapi import Request
from fastapi.responses import Response

ACCESS_COOKIE = "yapai_access"
REFRESH_COOKIE = "yapai_refresh"

# El refresh solo viaja a los endpoints de auth — minimiza exposición
_REFRESH_PATH = "/api/v1/auth"


def _secure() -> bool:
    return settings.ENV == "production"


def _domain() -> str | None:
    return settings.COOKIE_DOMAIN or None


def _usa_cookies() -> bool:
    return settings.AUTH_TRANSPORT in ("cookie", "both")


def set_auth_cookies(response: Response, tokens: TokenPair) -> None:
    """Emite las cookies de sesión junto a la respuesta de tokens."""
    if not _usa_cookies():
        return
    response.set_cookie(
        ACCESS_COOKIE, tokens.access_token,
        max_age=tokens.expires_in, httponly=True, secure=_secure(),
        samesite="lax", domain=_domain(), path="/api/v1",
    )
    # El refresh vive solo el tiempo del refresh token
    response.set_cookie(
        REFRESH_COOKIE, tokens.refresh_token,
        max_age=settings.REFRESH_TOKEN_DAYS * 86400, httponly=True,
        secure=_secure(), samesite="lax", domain=_domain(), path=_REFRESH_PATH,
    )


def clear_auth_cookies(response: Response) -> None:
    """Logout: borra ambas cookies (mismos atributos de path/domain)."""
    response.delete_cookie(ACCESS_COOKIE, domain=_domain(), path="/api/v1")
    response.delete_cookie(REFRESH_COOKIE, domain=_domain(), path=_REFRESH_PATH)


def token_desde_request(request: Request) -> str | None:
    """Extrae el access token: Authorization Bearer primero, cookie después."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    if _usa_cookies():
        return request.cookies.get(ACCESS_COOKIE)
    return None


def refresh_desde_request(request: Request) -> str | None:
    """Refresh token desde cookie (los clients Bearer lo mandan en el body)."""
    if not _usa_cookies():
        return None
    return request.cookies.get(REFRESH_COOKIE)


def auth_via_cookie(request: Request) -> bool:
    """True si el request se autenticó con cookie (sujeto a guard CSRF)."""
    auth = request.headers.get("authorization", "")
    return not auth.lower().startswith("bearer ") and bool(request.cookies.get(ACCESS_COOKIE))
