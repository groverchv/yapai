"""OTP de login para clientes (segundo factor tras teléfono+CI).

Proveedores de envío (`OTP_PROVIDER`):
- `log`: escribe el código en el log de la app (solo desarrollo; la
  validación de producción lo rechaza).
- `webhook`: POST JSON a `OTP_WEBHOOK_URL` con el código — permite integrar
  cualquier proveedor SMS/WhatsApp sin acoplar el código a uno concreto.
"""
import logging
import secrets
from datetime import timedelta

import httpx
from app.core.config import settings
from app.core.security import sha256_hex, utcnow
from app.core.utils import aware_utc
from app.models import Cliente, OtpCode
from sqlalchemy import select, update
from sqlalchemy.orm import Session

logger = logging.getLogger("yapai.otp")


def _nuevo_codigo() -> str:
    """Código numérico de 6 dígitos criptográficamente aleatorio."""
    return f"{secrets.randbelow(1_000_000):06d}"


def enviar_codigo(telefono: str, codigo: str) -> None:
    """Despacha el código al canal configurado. Falla en silencio controlado:
    el login no debe romperse porque el proveedor SMS esté caído — el cliente
    puede reintentar."""
    if settings.OTP_PROVIDER == "webhook":
        try:
            headers = {"Authorization": f"Bearer {settings.OTP_WEBHOOK_TOKEN}"} if settings.OTP_WEBHOOK_TOKEN else {}
            httpx.post(
                settings.OTP_WEBHOOK_URL,
                json={"telefono": telefono, "codigo": codigo,
                      "ttl_minutos": settings.OTP_TTL_MINUTES},
                headers=headers, timeout=10.0,
            ).raise_for_status()
            return
        except Exception:
            logger.exception("No se pudo enviar OTP por webhook (OTP_WEBHOOK_URL)")
            return
    # provider == "log" (solo dev): nunca en producción (validador de settings)
    logger.info("[OTP DEV] Código para %s: %s (válido %s min)",
                telefono, codigo, settings.OTP_TTL_MINUTES)


def _en_cooldown(otp: OtpCode | None) -> bool:
    """True si el OTP más reciente se emitió hace menos de OTP_RESEND_COOLDOWN_SEG
    (anti-spam/costo SMS). El código vigente sigue funcionando — solo se evita
    despachar uno nuevo por cada reintento."""
    if not otp or not otp.created_at:
        return False
    return aware_utc(otp.created_at) > utcnow() - timedelta(
        seconds=settings.OTP_RESEND_COOLDOWN_SEG)


def crear_otp(db: Session, cliente: Cliente) -> None:
    """Invalida códigos previos y emite uno nuevo (hash en DB, plano al canal).
    Si hay un código aún vigente dentro del cooldown, no reenvía (el código
    anterior sigue válido) — protege costo SMS ante reintentos."""
    vigente = db.scalar(
        select(OtpCode)
        .where(OtpCode.cliente_id == cliente.id, OtpCode.usado_en.is_(None))
        .order_by(OtpCode.id.desc())
    )
    if _en_cooldown(vigente):
        return
    db.execute(
        update(OtpCode)
        .where(OtpCode.cliente_id == cliente.id, OtpCode.usado_en.is_(None))
        .values(usado_en=utcnow())
    )
    codigo = _nuevo_codigo()
    db.add(OtpCode(
        cliente_id=cliente.id, telefono=cliente.telefono,
        codigo_hash=sha256_hex(codigo),
        expira_en=utcnow() + timedelta(minutes=settings.OTP_TTL_MINUTES),
    ))
    db.flush()
    enviar_codigo(cliente.telefono, codigo)


def crear_otp_telefono(db: Session, telefono: str) -> None:
    """OTP pre-registro: el cliente aún no existe — el código se liga solo al
    número. Mismo cooldown: no reenvía si hay uno vigente reciente."""
    vigente = db.scalar(
        select(OtpCode)
        .where(OtpCode.telefono == telefono, OtpCode.cliente_id.is_(None),
               OtpCode.usado_en.is_(None))
        .order_by(OtpCode.id.desc())
    )
    if _en_cooldown(vigente):
        return
    db.execute(
        update(OtpCode)
        .where(OtpCode.telefono == telefono, OtpCode.cliente_id.is_(None),
               OtpCode.usado_en.is_(None))
        .values(usado_en=utcnow())
    )
    codigo = _nuevo_codigo()
    db.add(OtpCode(
        telefono=telefono,
        codigo_hash=sha256_hex(codigo),
        expira_en=utcnow() + timedelta(minutes=settings.OTP_TTL_MINUTES),
    ))
    db.flush()
    enviar_codigo(telefono, codigo)


def _otp_activo(db: Session, cliente_id: int) -> OtpCode | None:
    otp = db.scalar(
        select(OtpCode)
        .where(OtpCode.cliente_id == cliente_id, OtpCode.usado_en.is_(None))
        .order_by(OtpCode.id.desc())
    )
    if otp and aware_utc(otp.expira_en) < utcnow():
        return None
    return otp


def verificar_otp(db: Session, cliente: Cliente, codigo: str) -> bool:
    """True si el código es correcto.

    IMPORTANTE: el incremento de `intentos` se commitea aquí mismo. El endpoint
    responde 401 en caso de fallo y el get_db hace rollback — sin este commit
    los intentos fallidos nunca persistirían (fuerza bruta sin límite).
    En el éxito solo hace flush: el caller commitea junto con los tokens."""
    otp = _otp_activo(db, cliente.id)
    if not otp or otp.intentos >= settings.OTP_MAX_INTENTOS:
        return False
    otp.intentos += 1
    if secrets.compare_digest(otp.codigo_hash, sha256_hex(codigo.strip())):
        otp.usado_en = utcnow()
        db.flush()
        return True
    if otp.intentos >= settings.OTP_MAX_INTENTOS:
        otp.usado_en = utcnow()  # agotado: exige nuevo login
    db.commit()
    return False


def verificar_otp_telefono(db: Session, telefono: str, codigo: str) -> bool:
    """Verifica un OTP de registro (ligado a teléfono, sin cliente aún).
    Misma persistencia de `intentos` que el login para frenar fuerza bruta."""
    otp = db.scalar(
        select(OtpCode)
        .where(OtpCode.telefono == telefono, OtpCode.cliente_id.is_(None),
               OtpCode.usado_en.is_(None))
        .order_by(OtpCode.id.desc())
    )
    if not otp or aware_utc(otp.expira_en) < utcnow():
        return False
    if otp.intentos >= settings.OTP_MAX_INTENTOS:
        return False
    otp.intentos += 1
    if secrets.compare_digest(otp.codigo_hash, sha256_hex(codigo.strip())):
        otp.usado_en = utcnow()
        db.flush()
        return True
    if otp.intentos >= settings.OTP_MAX_INTENTOS:
        otp.usado_en = utcnow()
    db.commit()
    return False
