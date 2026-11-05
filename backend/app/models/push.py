from datetime import datetime

from app.db.session import Base
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class PushSuscripcion(Base):
    """Suscripción Web Push de un cliente (un device/navegador por fila).

    `endpoint` es único — la URL de push la genera el navegador y sirve
    como clave natural para upserts (re-suscripciones comparten endpoint).
    """
    __tablename__ = "push_suscripciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)
    endpoint: Mapped[str] = mapped_column(String(500), unique=True)
    p256dh: Mapped[str] = mapped_column(String(200))
    auth: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
