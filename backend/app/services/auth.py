from datetime import timezone

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    crear_access_token, crear_refresh_token, decodificar_token,
    generar_token_plano, sha256_hex, utcnow,
)
from app.models import Cliente, RefreshToken, SujetoTipo, Usuario
from app.schemas.auth import TokenPair


def _aware(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def emitir_par_tokens(db: Session, sujeto_tipo: SujetoTipo, sujeto_id: int, rol: str, tenant_id: int | None = None) -> TokenPair:
    prefijo = "u" if sujeto_tipo == SujetoTipo.usuario else "c"
    sub = f"{prefijo}:{sujeto_id}"
    access = crear_access_token(sub=sub, rol=rol, tenant_id=tenant_id)
    refresh, expira = crear_refresh_token(sub)
    db.add(RefreshToken(
        sujeto_tipo=sujeto_tipo,
        sujeto_id=sujeto_id,
        token_hash=sha256_hex(refresh),
        expira_en=expira,
    ))
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_MINUTES * 60,
    )


def _refresh_invalido() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o revocado")


def rotar_refresh(db: Session, refresh_token: str) -> tuple[TokenPair, str, int]:
    """Valida el refresh, lo revoca y emite par nuevo. Retorna (tokens, sub, sujeto_id)."""
    try:
        payload = decodificar_token(refresh_token)
    except jwt.PyJWTError:
        raise _refresh_invalido()
    if payload.get("type") != "refresh":
        raise _refresh_invalido()

    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == sha256_hex(refresh_token)))
    if not row or row.revocado or _aware(row.expira_en) < utcnow():
        raise _refresh_invalido()

    row.revocado = True
    sub: str = payload["sub"]
    tipo, sujeto_id = sub[0], int(sub[2:])

    if tipo == "u":
        usuario = db.scalar(select(Usuario).where(Usuario.id == sujeto_id))
        if not usuario:
            raise _refresh_invalido()
        par = emitir_par_tokens(db, SujetoTipo.usuario, usuario.id, usuario.rol.value, usuario.tenant_id)
    elif tipo == "c":
        cliente = db.scalar(select(Cliente).where(Cliente.id == sujeto_id))
        if not cliente:
            raise _refresh_invalido()
        par = emitir_par_tokens(db, SujetoTipo.cliente, cliente.id, "cliente")
    else:
        raise _refresh_invalido()
    return par, sub, sujeto_id


def revocar_refresh(db: Session, refresh_token: str) -> None:
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == sha256_hex(refresh_token)))
    if row:
        row.revocado = True


def revocar_todos_refresh(db: Session, sujeto_tipo: SujetoTipo, sujeto_id: int) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.sujeto_tipo == sujeto_tipo, RefreshToken.sujeto_id == sujeto_id)
        .values(revocado=True)
    )


def crear_onboarding_token(db: Session, email: str, tenant_id: int) -> str:
    """Genera token plano (se envía por email); en DB queda solo el hash."""
    from datetime import timedelta
    from app.models import OnboardingToken
    plano = generar_token_plano()
    db.add(OnboardingToken(
        token_hash=sha256_hex(plano),
        email=email,
        tenant_id=tenant_id,
        expira_en=utcnow() + timedelta(hours=settings.ONBOARDING_TOKEN_HOURS),
    ))
    return plano
