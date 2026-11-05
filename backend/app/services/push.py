"""Web Push (VAPID) — notificaciones al cliente.

- `enviar_push_a_cliente`: envía un payload JSON a todas las suscripciones
  activas del cliente. Las suscripciones muertas (404/410) se eliminan.
- `push_async`: lo mismo en un hilo daemon con sesión propia — seguro de
  llamar desde routers después del commit sin bloquear la respuesta.
- Sin claves VAPID configuradas todo es no-op silencioso.
"""

import json
import logging
import threading

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.push import PushSuscripcion
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def push_disponible() -> bool:
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def _webpush(sub: PushSuscripcion, payload: dict) -> int | None:
    """Envía una notificación; devuelve status de error si falla."""
    from pywebpush import WebPushException, webpush  # import perezoso (dep opcional)

    try:
        webpush(
            subscription_info={
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
        )
        return None
    except WebPushException as e:
        return e.response.status_code if e.response is not None else 0
    except Exception:
        logger.exception("webpush falló")
        return -1


def enviar_push_a_cliente(db: Session, cliente_id: int, payload: dict) -> int:
    """Envía a todas las suscripciones del cliente. Devuelve # enviadas."""
    if not push_disponible():
        return 0
    subs = db.scalars(
        select(PushSuscripcion).where(PushSuscripcion.cliente_id == cliente_id)
    ).all()
    enviados = 0
    for sub in subs:
        status = _webpush(sub, payload)
        if status is None:
            enviados += 1
        elif status in (404, 410):
            db.delete(sub)  # suscripción muerta: el navegador la revocó
    if enviados or subs:
        db.commit()
    return enviados


def push_async(cliente_id: int, titulo: str, cuerpo: str, url: str = "/") -> None:
    """Fire-and-forget tras commit: hilo con sesión propia (la del request se cierra)."""
    if not push_disponible():
        return

    def _run() -> None:
        try:
            with SessionLocal() as db:
                enviar_push_a_cliente(db, cliente_id,
                                      {"titulo": titulo, "cuerpo": cuerpo, "url": url})
        except Exception:
            logger.exception("push_async falló para cliente %s", cliente_id)

    threading.Thread(target=_run, daemon=True).start()
