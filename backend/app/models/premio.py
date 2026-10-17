import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.session import Base


class EstadoPremio(str, enum.Enum):
    activo = "activo"
    agotado = "agotado"
    inactivo = "inactivo"


class Premio(Base):
    """Recompensa canjeable por puntos en un comercio."""
    __tablename__ = "premios"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    costo_puntos: Mapped[int] = mapped_column(Integer)
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    stock_limitado: Mapped[bool] = mapped_column(Boolean, default=False)
    stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[EstadoPremio] = mapped_column(
        Enum(EstadoPremio, native_enum=False, length=20, validate_strings=True),
        default=EstadoPremio.activo,
    )
    # Promoción temporal: tras esta fecha el premio no es canjeable ni visible al cliente
    vigencia_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RuletaSegmento(Base):
    """Configuración de la ruleta del kiosco por socio."""
    __tablename__ = "ruleta_segmentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    etiqueta: Mapped[str] = mapped_column(String(80))
    puntos: Mapped[int] = mapped_column(Integer, default=0)
    peso: Mapped[int] = mapped_column(Integer, default=1)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
