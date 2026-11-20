"""Antifraude de emisión de puntos (insider abuse).

Los puntos son pasivo financiero del comercio: un cajero u owner deshonesto
puede otorgarse puntos a sí mismo. La defensa por diseño es *detectar*, no
bloquear (la emisión legítima intensa existe: campañas, aperturas):

- Si un emisor otorga más de FRAUDE_PUNTOS_EMISOR_HORA en 1h → alerta.
- Si un cliente recibe más de FRAUDE_PUNTOS_CLIENTE_DIA en 24h → alerta.

Cada alerta: fila en audit_log (accion='alerta_fraude', visible en el panel),
métrica Prometheus `yapai_fraude_alertas_total` y warning en el log —
Alertmanager/Sentry pueden notificar a partir de ahí.
"""
import logging
from datetime import timedelta

from app.core.config import settings
from app.core.observability import FRAUDE_ALERTAS
from app.core.security import utcnow
from app.models import MovimientoPuntos, TipoMovimiento
from sqlalchemy import func, select
from sqlalchemy.orm import Session

logger = logging.getLogger("yapai.fraude")

# Solo los tipos que inyectan puntos nuevos al sistema (canje/congelar/liberar
# son bookkeeping interno; anulacion resta).
_TIPOS_EMISION = (
    TipoMovimiento.registro,
    TipoMovimiento.ruleta,
    TipoMovimiento.bonus_manual,
    TipoMovimiento.referido,
)


def _alertar(db: Session, tipo: str, detalle: dict) -> None:
    from app.services.audit import registrar_audit
    FRAUDE_ALERTAS.labels(tipo).inc()
    logger.warning("ALERTA FRAUDE [%s] %s", tipo, detalle)
    registrar_audit(db, None, "alerta_fraude", "seguridad", None,
                    {"tipo": tipo, **detalle})
    db.flush()  # autoflush=False: hacer visible la alerta a consultas de esta TX
    # Email al owner: solo la PRIMERA alerta del tenant en 24h (evita inundar
    # el correo si el umbral se sigue superando — el resto queda en audit/metrics)
    tenant_id = detalle.get("tenant_id")
    if not tenant_id:
        return
    try:
        from app.models import AuditLog, Tenant
        from app.services.email import email_service, emails_owner
        previas = db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.accion == "alerta_fraude",
                AuditLog.created_at >= utcnow() - timedelta(hours=24),
                AuditLog.detalle["tenant_id"].as_integer() == tenant_id,
            )
        ) or 0
        if previas > 1:  # la que acabamos de insertar + alguna anterior
            return
        tenant = db.get(Tenant, tenant_id)
        for mail in emails_owner(db, tenant_id):
            email_service.send_alerta_fraude(
                mail, tenant.nombre_comercial if tenant else "tu comercio",
                tipo, str(detalle))
    except Exception:
        logger.exception("Email de alerta de fraude falló (no bloquea)")


def verificar_emision(
    db: Session, *, cliente_id: int, puntos: int,
    ejecutado_por: int | None, tenant_id: int | None,
) -> None:
    """Evalúa umbrales de velocidad tras registrar una emisión de puntos.
    Nunca lanza excepción: la alerta no debe romper la operación."""
    try:
        db.flush()  # SessionLocal usa autoflush=False: contar la TX en curso
        hace_1h = utcnow() - timedelta(hours=1)
        if ejecutado_por is not None:
            total_emisor = db.scalar(
                select(func.coalesce(func.sum(MovimientoPuntos.puntos), 0)).where(
                    MovimientoPuntos.ejecutado_por == ejecutado_por,
                    MovimientoPuntos.tipo.in_(_TIPOS_EMISION),
                    MovimientoPuntos.created_at >= hace_1h,
                )
            ) or 0
            if total_emisor > settings.FRAUDE_PUNTOS_EMISOR_HORA:
                _alertar(db, "emisor_velocidad", {
                    "usuario_id": ejecutado_por, "tenant_id": tenant_id,
                    "puntos_ultima_hora": int(total_emisor),
                    "umbral": settings.FRAUDE_PUNTOS_EMISOR_HORA,
                })

        hace_24h = utcnow() - timedelta(hours=24)
        total_cliente = db.scalar(
            select(func.coalesce(func.sum(MovimientoPuntos.puntos), 0)).where(
                MovimientoPuntos.cliente_id == cliente_id,
                MovimientoPuntos.tipo.in_(_TIPOS_EMISION),
                MovimientoPuntos.created_at >= hace_24h,
            )
        ) or 0
        if total_cliente > settings.FRAUDE_PUNTOS_CLIENTE_DIA:
            _alertar(db, "cliente_velocidad", {
                "cliente_id": cliente_id, "tenant_id": tenant_id,
                "puntos_ultimas_24h": int(total_cliente),
                "umbral": settings.FRAUDE_PUNTOS_CLIENTE_DIA,
            })
    except Exception:
        logger.exception("verificar_emision falló (no bloquea la operación)")
