import enum
from datetime import datetime

from app.db.session import Base
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class EstadoFactura(str, enum.Enum):
    pendiente = "pendiente"   # emitida, dentro del plazo
    pagada = "pagada"         # cobrada (manual o pasarela)
    vencida = "vencida"       # pasó vence_en sin pagar → cuenta en mora
    anulada = "anulada"       # cancelada por el admin


class FacturaPlan(Base):
    """Factura mensual del plan SaaS de un socio (cobro manual o pasarela).

    Snapshot del plan al emitir — cambios posteriores del plan no la alteran.
    """
    __tablename__ = "facturas_plan"
    __table_args__ = (
        UniqueConstraint("tenant_id", "periodo", name="uq_factura_tenant_periodo"),
        Index("ix_facturas_estado_vence", "estado", "vence_en"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("planes.id"), nullable=True)
    plan_nombre: Mapped[str] = mapped_column(String(80))
    periodo: Mapped[str] = mapped_column(String(7), index=True)  # 'YYYY-MM'
    monto: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    moneda: Mapped[str] = mapped_column(String(3), default="BOB")
    estado: Mapped[EstadoFactura] = mapped_column(
        Enum(EstadoFactura, native_enum=False, length=20, validate_strings=True),
        default=EstadoFactura.pendiente, index=True,
    )
    emitida_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    vence_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    pagada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metodo: Mapped[str | None] = mapped_column(String(40), nullable=True)  # qr|transferencia|stripe|otro
    referencia: Mapped[str | None] = mapped_column(String(120), nullable=True)
    aprobada_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
