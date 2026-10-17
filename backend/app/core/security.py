import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

_password_hash = PasswordHash((Argon2Hasher(),))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Passwords y PINs (mismo hasher argon2, regla #14) ---

def hash_secret(plain: str) -> str:
    return _password_hash.hash(plain)


def verify_secret(plain: str, hashed: str) -> bool:
    try:
        return _password_hash.verify(plain, hashed)
    except Exception:
        return False


# --- Tokens de un solo uso (onboarding / reset). En DB se guarda sha256. ---

def generar_token_plano(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def generar_pin_corto(length: int = 6) -> str:
    """PIN alfanumérico corto para respaldo del pase (sin caracteres ambiguos)."""
    alphabet = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


# --- JWT ---

def crear_access_token(sub: str, rol: str, tenant_id: int | None = None) -> str:
    ahora = utcnow()
    payload = {
        "sub": sub,
        "rol": rol,
        "type": "access",
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES),
    }
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def crear_refresh_token(sub: str) -> tuple[str, datetime]:
    ahora = utcnow()
    expira = ahora + timedelta(days=settings.REFRESH_TOKEN_DAYS)
    payload = {
        "sub": sub,
        "type": "refresh",
        "jti": secrets.token_hex(16),
        "iat": ahora,
        "exp": expira,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM), expira


def decodificar_token(token: str) -> dict:
    """Lanza jwt.PyJWTError si es inválido o expiró."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
