from app.core.config import settings
from app.core.deps import get_current_cliente
from app.db.session import get_db
from app.models import Cliente, PushSuscripcion
from app.services.push import push_disponible
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(get_current_cliente)])


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class SuscripcionIn(BaseModel):
    endpoint: str
    keys: PushKeys


@router.get("/push/vapid")
def vapid_public_key() -> dict:
    """Clave pública VAPID para applicationServerKey en el navegador.
    public_key null = push no configurado en el servidor."""
    return {"public_key": settings.VAPID_PUBLIC_KEY or None}


@router.post("/push/suscripcion", status_code=status.HTTP_201_CREATED)
def suscribir(data: SuscripcionIn, cliente: Cliente = Depends(get_current_cliente),
              db: Session = Depends(get_db)):
    """Alta/refresh de suscripción push. Upsert por endpoint (único por navegador)."""
    if not push_disponible():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Notificaciones push no configuradas en el servidor")
    sub = db.scalar(select(PushSuscripcion).where(PushSuscripcion.endpoint == data.endpoint))
    if sub:
        sub.cliente_id = cliente.id
        sub.p256dh = data.keys.p256dh
        sub.auth = data.keys.auth
    else:
        db.add(PushSuscripcion(
            cliente_id=cliente.id, endpoint=data.endpoint,
            p256dh=data.keys.p256dh, auth=data.keys.auth,
        ))
    db.commit()
    return {"detail": "Suscripción registrada"}


@router.delete("/push/suscripcion", status_code=status.HTTP_204_NO_CONTENT)
def desuscribir(endpoint: str, cliente: Cliente = Depends(get_current_cliente),
                db: Session = Depends(get_db)):
    """Baja de la suscripción del navegador actual (?endpoint=<url push>)."""
    db.execute(delete(PushSuscripcion).where(
        PushSuscripcion.endpoint == endpoint,
        PushSuscripcion.cliente_id == cliente.id,
    ))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
