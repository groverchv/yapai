from app.models import AuditLog
from sqlalchemy.orm import Session


def registrar_audit(
    db: Session,
    actor_id: int | None,
    accion: str,
    entidad: str,
    entidad_id: int | None = None,
    detalle: dict | None = None,
) -> AuditLog:
    """Registra una acción sensible. No hace commit: lo realiza el caller dentro de su TX."""
    log = AuditLog(
        actor_id=actor_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=detalle,
    )
    db.add(log)
    return log
