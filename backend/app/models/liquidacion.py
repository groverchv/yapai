import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum, ForeignKey, Integer, Numeric, UniqueConstraint, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.session import Base

_JSONB = JSON().with_variant(postgresql.JSONB, "postgresql")


class EstadoLiquidacion(str, enum.Enum):
    pendiente = "pendiente"
    pagada = "pagada"


class Liquidacion(Base):
    """Cobro mensual de comisiones a un socio. Guarda snapshot de tarifas (regla #12)."""
    __tablename__ = "liquidaciones"
    __table_args__ = (UniqueConstraint("tenant_id", "periodo", name="uq_liquidacion_tenant_periodo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    periodo: Mapped[str] = mapped_column(String(7), index=True)  # 'YYYY-MM'
    clientes_nuevos: Mapped[int] = mapped_column(Integer, default=0)
    canjes_validados: Mapped[int] = mapped_column(Integer, default=0)
    costo_registro_unit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    costo_canje_unit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    monto_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    moneda: Mapped[str] = mapped_column(String(3), default="BOB")  # snapshot del esquema
    estado: Mapped[EstadoLiquidacion] = mapped_column(
        Enum(EstadoLiquidacion, native_enum=False, length=20, validate_strings=True),
        default=EstadoLiquidacion.pendiente, index=True,
    )
    pagada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    aprobada_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    """Auditoría de acciones sensibles (regla #13)."""
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True, index=True)
    accion: Mapped[str] = mapped_column(String(80), index=True)
    entidad: Mapped[str] = mapped_column(String(80))
    entidad_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detalle: Mapped[dict | None] = mapped_column(_JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
