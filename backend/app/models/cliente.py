import enum
from datetime import datetime

from app.db.session import Base
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class EstadoCliente(str, enum.Enum):
    activo = "activo"
    eliminado = "eliminado"


class Cliente(Base):
    """Cliente final (app móvil). Se registra en el kiosco con CI + teléfono."""
    __tablename__ = "clientes"
    __table_args__ = (Index("ix_clientes_tenant_registro", "tenant_registro_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(160))
    ci: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    telefono: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    estado: Mapped[EstadoCliente] = mapped_column(
        Enum(EstadoCliente, native_enum=False, length=20, validate_strings=True),
        default=EstadoCliente.activo,
    )
    # Caches mantenidos por el ledger (ver services/wallet en fases siguientes)
    saldo_puntos: Mapped[int] = mapped_column(Integer, default=0)
    puntos_congelados: Mapped[int] = mapped_column(Integer, default=0)
    tenant_registro_id: Mapped[int | None] = mapped_column(nullable=True)  # tenant donde se registró
    # Referidos: código propio para compartir + quién lo refirió al registrarse
    codigo_referido: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    referido_por_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    eliminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
