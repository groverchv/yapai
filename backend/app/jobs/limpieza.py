"""Job de limpieza: purga tokens de un solo uso ya expirados/consumidos.

Corre 1×/día. La info de seguridad no se pierde: refresh revocados se mantienen
(la detección de reúso los necesita) — solo se borran los EXPIRADOS, que ya no
pueden presentarse válidamente.
"""
import asyncio
import logging

from app.core.config import settings
from app.core.security import utcnow
from app.db.session import SessionLocal
from app.models import OnboardingToken, OtpCode, PasswordReset, RefreshToken
from sqlalchemy import delete, or_, select

logger = logging.getLogger("yapai.limpieza")

INTERVALO_SEG = 24 * 3600

# Días que se conservan los datos de un socio que pidió la baja.
BAJA_RETENCION_DIAS = settings.BAJA_RETENCION_DIAS


def purgar_tenants_baja() -> int:
    """Anonimiza socios cuya baja superó el período de retención.

    No borra filas del ledger: movimientos_puntos y audit_log son append-only.
    En su lugar: scrub de PII (tenant/usuarios/clientes → placeholders por id),
    baja lógica de entidades operativas, y borrado SOLO de datos efímeros
    (tokens, OTPs, PINs, suscripciones push, asignaciones M:N, comunicados).
    `baja_solicitada_en` queda en NULL → no reprocesa.
    """
    from datetime import datetime, timedelta, timezone

    from app.models import (
        Campana,
        Cliente,
        Comunicado,
        ConfigPin,
        EmpleadoSucursal,
        EstadoCliente,
        EstadoPantalla,
        EstadoPase,
        EstadoPremio,
        EstadoSucursal,
        EstadoUsuario,
        MovimientoPuntos,
        Pantalla,
        PaseDigital,
        PinCajero,
        PinSucursal,
        Premio,
        PushSuscripcion,
        RuletaSegmento,
        Sucursal,
        SujetoTipo,
        Tenant,
        TipoMovimiento,
        Usuario,
    )
    from sqlalchemy import update

    db = SessionLocal()
    try:
        limite = utcnow() - timedelta(days=BAJA_RETENCION_DIAS)
        tenants = db.scalars(
            select(Tenant).where(Tenant.baja_solicitada_en < limite)
        ).all()
        for t in tenants:
            try:
                cliente_ids = select(Cliente.id).where(
                    Cliente.tenant_registro_id == t.id)
                usuario_ids = select(Usuario.id).where(Usuario.tenant_id == t.id)
                suc_ids = select(Sucursal.id).where(Sucursal.tenant_id == t.id)

                # Efímeros: sí se borran
                db.execute(delete(PushSuscripcion).where(
                    PushSuscripcion.cliente_id.in_(cliente_ids)))
                db.execute(delete(OtpCode).where(
                    OtpCode.cliente_id.in_(cliente_ids)))
                db.execute(delete(RefreshToken).where(
                    RefreshToken.sujeto_id.in_(usuario_ids),
                    RefreshToken.sujeto_tipo == SujetoTipo.usuario))
                db.execute(delete(RefreshToken).where(
                    RefreshToken.sujeto_id.in_(cliente_ids),
                    RefreshToken.sujeto_tipo == SujetoTipo.cliente))
                db.execute(delete(PasswordReset).where(
                    PasswordReset.usuario_id.in_(usuario_ids)))
                db.execute(delete(PinCajero).where(
                    PinCajero.usuario_id.in_(usuario_ids)))
                db.execute(delete(EmpleadoSucursal).where(
                    EmpleadoSucursal.sucursal_id.in_(suc_ids)))
                db.execute(delete(PinSucursal).where(
                    PinSucursal.sucursal_id.in_(suc_ids)))
                db.execute(delete(OnboardingToken).where(
                    OnboardingToken.tenant_id == t.id))
                db.execute(delete(ConfigPin).where(ConfigPin.tenant_id == t.id))
                db.execute(delete(Comunicado).where(Comunicado.tenant_id == t.id))
                db.execute(delete(Campana).where(Campana.tenant_id == t.id))
                db.execute(delete(RuletaSegmento).where(
                    RuletaSegmento.tenant_id == t.id))

                # PII: anonimización en sitio (ledger y audit intactos)
                t.nombre_comercial = f"Cuenta eliminada {t.id}"
                t.razon_social = None
                t.nit_rut = f"del-nit-{t.id}"
                t.email_contacto = None
                t.telefono = None
                t.logo_url = None
                t.stripe_customer_id = None
                t.baja_solicitada_en = None

                for u in db.scalars(
                        select(Usuario).where(Usuario.tenant_id == t.id)).all():
                    u.nombre = "Usuario eliminado"
                    u.email = f"del-{u.id}@baja.yapai"
                    u.password_hash = None
                    u.foto_url = None
                    u.estado = EstadoUsuario.suspendido

                for c in db.scalars(
                        select(Cliente).where(
                            Cliente.tenant_registro_id == t.id)).all():
                    if c.estado != EstadoCliente.eliminado:
                        if c.saldo_puntos > 0:
                            db.add(MovimientoPuntos(
                                cliente_id=c.id, tenant_id=t.id,
                                tipo=TipoMovimiento.anulacion,
                                puntos=-c.saldo_puntos,
                                detalle={"motivo": "baja_socio"},
                            ))
                        c.saldo_puntos = 0
                        c.puntos_congelados = 0
                        c.estado = EstadoCliente.eliminado
                        c.eliminado_en = datetime.now(timezone.utc)
                        c.nombre = "Cuenta eliminada"
                        c.ci = f"del-ci-{c.id}"
                        c.telefono = f"del-tel-{c.id}"
                        c.foto_url = None
                        c.codigo_referido = None

                # Operativas: baja lógica (las filas viven para las FKs del ledger)
                db.execute(update(Sucursal).where(Sucursal.tenant_id == t.id)
                           .values(estado=EstadoSucursal.suspendida))
                db.execute(update(Pantalla).where(Pantalla.sucursal_id.in_(suc_ids))
                           .values(estado=EstadoPantalla.bloqueada))
                db.execute(update(Premio).where(Premio.tenant_id == t.id)
                           .values(estado=EstadoPremio.inactivo))
                db.execute(update(PaseDigital).where(
                    PaseDigital.tenant_id == t.id,
                    PaseDigital.estado == EstadoPase.activo,
                ).values(estado=EstadoPase.cancelado))

                db.commit()
                logger.info("Tenant %s anonimizado tras baja solicitada", t.id)
            except Exception:
                db.rollback()
                logger.exception("Falló la anonimización del tenant %s", t.id)
        return len(tenants)
    finally:
        db.close()


def purgar_tokens_expirados() -> dict[str, int]:
    """Borra tokens expirados. Devuelve el conteo por tabla."""
    db = SessionLocal()
    try:
        ahora = utcnow()
        conteos = {
            "refresh_tokens": db.execute(
                delete(RefreshToken).where(RefreshToken.expira_en < ahora)).rowcount,
            "password_resets": db.execute(
                delete(PasswordReset).where(or_(
                    PasswordReset.expira_en < ahora,
                    PasswordReset.usado_en.is_not(None)))).rowcount,
            "onboarding_tokens": db.execute(
                delete(OnboardingToken).where(or_(
                    OnboardingToken.expira_en < ahora,
                    OnboardingToken.usado_en.is_not(None)))).rowcount,
            "otp_codes": db.execute(
                delete(OtpCode).where(or_(
                    OtpCode.expira_en < ahora,
                    OtpCode.usado_en.is_not(None)))).rowcount,
        }
        db.commit()
        if any(conteos.values()):
            logger.info("Purgados tokens expirados: %s", conteos)
        return conteos
    finally:
        db.close()


async def loop_limpieza(stop: asyncio.Event) -> None:
    """Loop diario: primera purga al minuto de arrancar."""
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=60)
            break
        except asyncio.TimeoutError:
            pass
        try:
            await asyncio.to_thread(purgar_tokens_expirados)
        except Exception:
            logger.exception("Error en purga de tokens expirados")
        try:
            await asyncio.to_thread(purgar_tenants_baja)
        except Exception:
            logger.exception("Error en purga de tenants dados de baja")
        try:
            await asyncio.wait_for(stop.wait(), timeout=INTERVALO_SEG)
        except asyncio.TimeoutError:
            pass
