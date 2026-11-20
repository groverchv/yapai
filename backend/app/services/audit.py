import hashlib
import json

from app.models import AuditLog
from sqlalchemy import select
from sqlalchemy.orm import Session


def _hash_registro(
    prev_hash: str | None,
    actor_id: int | None,
    accion: str,
    entidad: str,
    entidad_id: int | None,
    detalle: dict | None,
) -> str:
    """Hash determinista del registro encadenado al anterior (estilo blockchain-lite)."""
    payload = json.dumps(
        {
            "actor_id": actor_id,
            "accion": accion,
            "entidad": entidad,
            "entidad_id": entidad_id,
            "detalle": detalle,
        },
        sort_keys=True, separators=(",", ":"), default=str,
    )
    return hashlib.sha256(f"{prev_hash or 'genesis'}|{payload}".encode()).hexdigest()


def _ultimo_hash(db: Session) -> str | None:
    return db.scalar(
        select(AuditLog.registro_hash)
        .where(AuditLog.registro_hash.is_not(None))
        .order_by(AuditLog.id.desc())
        .limit(1)
    )


def registrar_audit(
    db: Session,
    actor_id: int | None,
    accion: str,
    entidad: str,
    entidad_id: int | None = None,
    detalle: dict | None = None,
) -> AuditLog:
    """Registra una acción sensible encadenada al registro previo.
    No hace commit: lo realiza el caller dentro de su TX."""
    prev = _ultimo_hash(db)
    log = AuditLog(
        actor_id=actor_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=detalle,
        prev_hash=prev,
        registro_hash=_hash_registro(prev, actor_id, accion, entidad, entidad_id, detalle),
    )
    db.add(log)
    return log
