"""Invariantes de hardening: headers de seguridad, 2FA TOTP y rate limiting."""
import uuid

import pyotp


def _signup_socio(client):
    suf = uuid.uuid4().hex[:8]
    r = client.post("/api/v1/auth/signup", json={
        "negocio_nombre": f"Sec {suf}",
        "owner_nombre": "Dueño Sec",
        "email": f"sec-{suf}@test.com",
        "password": "TestPass12345",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    return body["usuario"]["email"], {"Authorization": f"Bearer {body['tokens']['access_token']}"}


def test_headers_de_seguridad_en_respuestas(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "no-referrer" in r.headers["referrer-policy"]
    assert "content-security-policy" in r.headers
    assert "camera=()" in r.headers["permissions-policy"]


def test_2fa_endpoints_requieren_auth(client):
    assert client.post("/api/v1/auth/2fa/setup").status_code in (401, 403)
    assert client.post("/api/v1/auth/2fa/habilitar", json={"codigo": "123456"}).status_code in (401, 403)


def test_flujo_2fa_completo(client):
    email, headers = _signup_socio(client)

    # Setup: devuelve secret, URI otpauth y QR — aún inactivo
    r = client.post("/api/v1/auth/2fa/setup", headers=headers)
    assert r.status_code == 200, r.text
    setup = r.json()
    assert setup["provisioning_uri"].startswith("otpauth://totp/")
    assert "<svg" in setup["qr_svg"]
    secret = setup["secret"]

    # No se puede re-setup sin desactivar (aún inactivo sí permite re-setup? → activarlo primero)
    totp = pyotp.TOTP(secret)

    # Código incorrecto → 400, sigue inactivo
    r = client.post("/api/v1/auth/2fa/habilitar", headers=headers, json={"codigo": "000000"})
    assert r.status_code in (400, 401)

    # Código correcto → activa
    r = client.post("/api/v1/auth/2fa/habilitar", headers=headers, json={"codigo": totp.now()})
    assert r.status_code == 200, r.text

    # Login ya no devuelve tokens — devuelve challenge 2FA
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass12345"})
    assert r.status_code == 200
    body = r.json()
    assert body["requires_2fa"] is True
    assert body["tokens"] is None
    pre = body["pre_token"]
    assert pre

    # El pre_token NO sirve como access token
    r = client.get("/api/v1/socio/plan", headers={"Authorization": f"Bearer {pre}"})
    assert r.status_code == 401

    # Código TOTP incorrecto → 400
    r = client.post("/api/v1/auth/login/2fa", json={"pre_token": pre, "codigo": "000000"})
    assert r.status_code in (400, 401)

    # Código correcto → tokens normales
    r = client.post("/api/v1/auth/login/2fa", json={"pre_token": pre, "codigo": totp.now()})
    assert r.status_code == 200, r.text
    assert r.json()["tokens"]["access_token"]
    assert r.json()["usuario"]["totp_habilitado"] is True

    # Desactivar con contraseña incorrecta → 401
    r = client.post("/api/v1/auth/2fa/deshabilitar", headers=headers, json={"password": "mal"})
    assert r.status_code == 401

    # Desactivar bien → login vuelve a ser directo
    r = client.post("/api/v1/auth/2fa/deshabilitar", headers=headers, json={"password": "TestPass12345"})
    assert r.status_code == 200
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass12345"})
    assert r.json()["requires_2fa"] is False
    assert r.json()["tokens"]["access_token"]


def test_login_2fa_rechaza_pre_token_invalido(client):
    r = client.post("/api/v1/auth/login/2fa", json={"pre_token": "token-falso", "codigo": "123456"})
    assert r.status_code == 401


def test_rate_limit_login(client):
    # 10 intentos/min por IP — el 11.º debe dar 429
    codigos = [
        client.post("/api/v1/auth/login",
                    json={"email": "nadie@test.com", "password": "x"}).status_code
        for _ in range(11)
    ]
    assert 429 in codigos


# --- Endurecimiento Fase Seguridad (auditoría 2026-11) ---

# Configuración que PASA el validador de producción — base para los tests
_PROD_SEGURO = {
    "DEBUG": False,
    "JWT_SECRET": "x" * 40,
    "CORS_ORIGINS": "https://app.yapai.com,https://admin.yapai.com",
    "SEED_ADMIN_PASSWORD": "Clave123Larga",
    "SEED_DEMO": False,
    "POSTGRES_PASSWORD": "pg-segura-123",
    "CLIENTE_OTP_ENABLED": True,
    "OTP_PROVIDER": "webhook",
    "OTP_WEBHOOK_URL": "https://sms.ejemplo.com/send",
    "REQUIRE_SUPERADMIN_2FA": True,
    "AUTH_TRANSPORT": "both",
    "COOKIE_DOMAIN": ".yapai.com",
}


def test_router_dev_no_existe(client):
    """El proxy PostgREST sin auth fue eliminado — cualquier ruta /dev da 404."""
    assert client.get("/api/v1/dev/postgrest-proxy/usuarios").status_code == 404
    assert client.get("/api/v1/dev/postgrest-proxy/cliente").status_code == 404


def test_docs_habilitados_solo_fuera_de_produccion():
    """La propiedad gates /docs, /redoc y /openapi.json en producción."""
    from app.core.config import Settings

    assert Settings(ENV="development").docs_habilitados is True
    assert Settings(ENV="production", **_PROD_SEGURO).docs_habilitados is False
    assert Settings(ENV="production", DOCS_ENABLED=True,
                    **_PROD_SEGURO).docs_habilitados is True


def test_validador_produccion_rechaza_defaults():
    """ENV=production con configuración insegura debe abortar el arranque."""
    import pytest
    from app.core.config import Settings
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(ENV="production")  # todo por defecto → varios errores
    with pytest.raises(ValidationError):
        Settings(ENV="production", **{**_PROD_SEGURO, "DEBUG": True})
    with pytest.raises(ValidationError):
        Settings(ENV="production", **{**_PROD_SEGURO, "CORS_ORIGINS": "*"})
    # OTP en 'log', 2FA opcional o cookies sin dominio → inseguro en prod
    for kwargs in (
        {"OTP_PROVIDER": "log"},
        {"REQUIRE_SUPERADMIN_2FA": False},
        {"COOKIE_DOMAIN": ""},
        {"CLIENTE_OTP_ENABLED": False},
    ):
        with pytest.raises(ValidationError):
            Settings(ENV="production", **{**_PROD_SEGURO, **kwargs})


def test_validador_produccion_acepta_config_segura():
    from app.core.config import Settings

    s = Settings(ENV="production", **_PROD_SEGURO)
    assert s.ENV == "production"


def test_password_policy_signup(client):
    """Passwords <12 chars o sin letra+dígito son rechazadas en signup."""
    base = {"negocio_nombre": "Negocio X", "owner_nombre": "Dueño X",
            "email": "pw-x@test.com"}
    r = client.post("/api/v1/auth/signup", json={**base, "password": "corta1A"})
    assert r.status_code == 422
    r = client.post("/api/v1/auth/signup", json={**base, "password": "sololetraslarguisima"})
    assert r.status_code == 422


def test_forgot_password_rate_limited(client):
    """3 solicitudes/hora por IP — la 4.ª debe dar 429 (anti email-bombing)."""
    codigos = [
        client.post("/api/v1/auth/forgot-password",
                    json={"email": "nadie@test.com"}).status_code
        for _ in range(4)
    ]
    assert codigos[:3] == [200, 200, 200]
    assert codigos[3] == 429


def test_refresh_token_reuso_revoca_familia(client, db):
    """Presentar un refresh ya rotado revoca TODAS las sesiones del sujeto."""
    r = client.post("/api/v1/auth/login",
                    json={"email": "owner@demo.com", "password": "Owner123!"})
    assert r.status_code == 200
    viejo = r.json()["tokens"]["refresh_token"]

    # Rotación legítima: viejo queda revocado, nuevo emitido
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": viejo})
    assert r.status_code == 200
    nuevo = r.json()["refresh_token"]

    # Reuso del viejo → 401 + la familia entera queda revocada
    assert client.post("/api/v1/auth/refresh",
                       json={"refresh_token": viejo}).status_code == 401
    assert client.post("/api/v1/auth/refresh",
                       json={"refresh_token": nuevo}).status_code == 401


def test_validar_imagen_magic_bytes():
    """La validación de uploads mira el contenido, no el Content-Type."""
    import pytest
    from app.services.media import leer_imagen_validada, validar_imagen

    assert validar_imagen(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32) == "ok"
    assert validar_imagen(b"\xff\xd8\xff\xe0" + b"\x00" * 32) == "ok"
    assert validar_imagen(b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 8) == "ok"
    # SVG y contenido falso son rechazados
    assert validar_imagen(b'<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>') is None
    assert validar_imagen(b"MZ\x90\x00" + b"\x00" * 64) is None
    with pytest.raises(ValueError):
        leer_imagen_validada(b"no soy imagen")


def test_login_no_revela_usuario_inexistente(client):
    """Mismo código de error para usuario inexistente y password incorrecta."""
    r1 = client.post("/api/v1/auth/login",
                     json={"email": "noexiste@test.com", "password": "x"})
    r2 = client.post("/api/v1/auth/login",
                     json={"email": "owner@demo.com", "password": "x"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json()["detail"] == r2.json()["detail"]


# --- Cookies HttpOnly (transporte de sesión en navegadores) ---


def test_login_emite_cookies_httponly(client):
    """El login setea yapai_access + yapai_refresh con flag HttpOnly."""
    r = client.post("/api/v1/auth/login",
                    json={"email": "owner@demo.com", "password": "Owner123!"})
    assert r.status_code == 200
    set_cookie = r.headers.get("set-cookie", "")
    assert "yapai_access=" in set_cookie and "yapai_refresh=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "samesite=lax" in set_cookie.lower()


def test_cookie_auth_sin_header(client):
    """Con la cookie de sesión, la API autentica sin Authorization."""
    client.post("/api/v1/auth/login",
                json={"email": "owner@demo.com", "password": "Owner123!"})
    # El jar del TestClient envía yapai_access automáticamente
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["usuario"]["email"] == "owner@demo.com"


def test_csrf_guard_sin_header(client):
    """Mutación autenticada por cookie sin X-Requested-With → 403.
    Con Bearer no aplica (Authorization no es credencial ambiental)."""
    from app.main import app
    from fastapi.testclient import TestClient

    # Cliente SIN el header CSRF por defecto
    c2 = TestClient(app)
    c2.post("/api/v1/auth/login",
            json={"email": "owner@demo.com", "password": "Owner123!"})
    r = c2.post("/api/v1/socio/campanas", json={"nombre": "x", "inicio": "2030-01-01",
                                                "fin": "2030-01-02", "multiplicador": 2})
    assert r.status_code == 403
    assert "X-Requested-With" in r.json()["detail"]

    # Con el header pasa el guard (la ruta decide luego por datos válidos)
    r = c2.post("/api/v1/socio/campanas", headers={"X-Requested-With": "XMLHttpRequest"},
                json={"nombre": "x", "inicio": "2030-01-01",
                      "fin": "2030-01-02", "multiplicador": 2})
    assert r.status_code != 403


def test_logout_limpia_cookies(client):
    client.post("/api/v1/auth/login",
                json={"email": "owner@demo.com", "password": "Owner123!"})
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    # Las cookies quedan vacías/expiradas → /me ya no autentica por cookie
    assert client.get("/api/v1/auth/me").status_code in (401, 403)
