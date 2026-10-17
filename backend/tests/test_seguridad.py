"""Invariantes de hardening: headers de seguridad, 2FA TOTP y rate limiting."""
import uuid

import pyotp


def _signup_socio(client):
    suf = uuid.uuid4().hex[:8]
    r = client.post("/api/v1/auth/signup", json={
        "negocio_nombre": f"Sec {suf}",
        "owner_nombre": "Dueño Sec",
        "email": f"sec-{suf}@test.com",
        "password": "TestPass123",
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
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123"})
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
    r = client.post("/api/v1/auth/2fa/deshabilitar", headers=headers, json={"password": "TestPass123"})
    assert r.status_code == 200
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123"})
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
