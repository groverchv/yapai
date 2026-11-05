from datetime import datetime

from app.db.session import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class Campana(Base):
    """Campaña multiplicadora de puntos de un socio (ej. 'x2 puntos este finde').

    - `sucursal_id` NULL = aplica a todas las sucursales del tenant.
    - Ventana [inicio, fin] — el multiplicador se aplica a puntos por registro
      y ruleta (no al bonus manual del cajero, que ya decide el monto).
    """
    __tablename__ = "campanas"
    __table_args__ = (Index("ix_campanas_tenant_activa", "tenant_id", "activa"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(160))
    multiplicador: Mapped[int] = mapped_column(Integer, default=2)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sucursal_id: Mapped[int | None] = mapped_column(ForeignKey("sucursales.id"), nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
