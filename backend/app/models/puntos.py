import enum
import uuid
from datetime import datetime

from app.db.session import Base
from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

_JSONB = JSON().with_variant(postgresql.JSONB, "postgresql")


class TipoMovimiento(str, enum.Enum):
    registro = "registro"
    ruleta = "ruleta"
    referido = "referido"
    bonus_manual = "bonus_manual"
    canje = "canje"
    congelar = "congelar"
    liberar = "liberar"
    anulacion = "anulacion"


class EstadoPase(str, enum.Enum):
    activo = "activo"
    canjeado = "canjeado"
    cancelado = "cancelado"
    expirado = "expirado"


class MovimientoPuntos(Base):
    """Ledger append-only de puntos. Nunca se edita ni se borra (regla #1)."""
    __tablename__ = "movimientos_puntos"
    __table_args__ = (
        Index("ix_mov_tenant_created", "tenant_id", "created_at"),
        Index("ix_mov_cliente_created", "cliente_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)
    sucursal_id: Mapped[int | None] = mapped_column(ForeignKey("sucursales.id"), nullable=True)
    tipo: Mapped[TipoMovimiento] = mapped_column(
        Enum(TipoMovimiento, native_enum=False, length=20, validate_strings=True), index=True
    )
    puntos: Mapped[int] = mapped_column(Integer)
    pase_id: Mapped[int | None] = mapped_column(ForeignKey("pases_digitales.id"), nullable=True)
    premio_id: Mapped[int | None] = mapped_column(ForeignKey("premios.id"), nullable=True)
    ejecutado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    detalle: Mapped[dict | None] = mapped_column("metadata", _JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class PaseDigital(Base):
    """Pase de canje generado por el cliente (QR + PIN corto). Congela puntos."""
    __tablename__ = "pases_digitales"
    __table_args__ = (Index("ix_pases_estado_expira", "estado", "expira_en"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)
    premio_id: Mapped[int] = mapped_column(ForeignKey("premios.id"))
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    codigo_qr: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: uuid.uuid4().hex)
    pin_corto: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    puntos: Mapped[int] = mapped_column(Integer)
    estado: Mapped[EstadoPase] = mapped_column(
        Enum(EstadoPase, native_enum=False, length=20, validate_strings=True),
        default=EstadoPase.activo, index=True,
    )
    expira_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canjeado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canjeado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    sucursal_canje_id: Mapped[int | None] = mapped_column(ForeignKey("sucursales.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
