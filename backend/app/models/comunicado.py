import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.session import Base


class EstadoComunicado(str, enum.Enum):
    borrador = "borrador"
    publicado = "publicado"
    archivado = "archivado"


class Comunicado(Base):
    """Oferta/comunicado que un socio publica y aparece en el feed de la app.

    - `premio_id` opcional: el comunicado enlaza a un premio canjeable
      (deep-link desde la app al catálogo del comercio).
    - `imagen_public_id`: public_id de Cloudinary para borrarla al reemplazar.
    """
    __tablename__ = "comunicados"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    imagen_url: Mapped[str] = mapped_column(String(500))
    imagen_public_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    premio_id: Mapped[int | None] = mapped_column(ForeignKey("premios.id"), nullable=True)
    estado: Mapped[EstadoComunicado] = mapped_column(
        Enum(EstadoComunicado, native_enum=False, length=20, validate_strings=True),
        default=EstadoComunicado.borrador, index=True,
    )
    publicado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vigencia_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
