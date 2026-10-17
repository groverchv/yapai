import enum
from datetime import datetime
from sqlalchemy import Boolean, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.session import Base


class RolUsuario(str, enum.Enum):
    superadmin = "superadmin"
    owner = "owner"
    cajero = "cajero"


class EstadoUsuario(str, enum.Enum):
    activo = "activo"
    suspendido = "suspendido"


class Usuario(Base):
    """Usuarios del sistema: superadmin (YAPAI), owner y cajero (por tenant)."""
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nombre: Mapped[str] = mapped_column(String(255))
    rol: Mapped[RolUsuario] = mapped_column(Enum(RolUsuario, native_enum=False, length=20, validate_strings=True))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)
    estado: Mapped[EstadoUsuario] = mapped_column(
        Enum(EstadoUsuario, native_enum=False, length=20, validate_strings=True),
        default=EstadoUsuario.activo,
    )
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 2FA TOTP: secret queda guardado al hacer setup; habilitado tras verificar un código
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_habilitado: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
