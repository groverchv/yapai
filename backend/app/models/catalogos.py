from datetime import datetime

from app.db.session import Base
from sqlalchemy import Boolean, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class CategoriaNegocio(Base):
    """Rubros comerciales que alimentan el filtro de la app móvil."""
    __tablename__ = "categorias_negocio"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    icono_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EsquemaComision(Base):
    """Tarifas de facturación a socios. Los montos quedan inmutables si tiene uso."""
    __tablename__ = "esquemas_comision"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    costo_registro: Mapped[float] = mapped_column(Numeric(12, 2))
    costo_canje: Mapped[float] = mapped_column(Numeric(12, 2))
    moneda: Mapped[str] = mapped_column(String(8), default="BOB")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
