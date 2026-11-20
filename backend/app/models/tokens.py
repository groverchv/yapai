import enum
from datetime import datetime

from app.db.session import Base
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class SujetoTipo(str, enum.Enum):
    usuario = "usuario"
    cliente = "cliente"


class OnboardingToken(Base):
    """Link único de bienvenida para que el Owner establezca su contraseña."""
    __tablename__ = "onboarding_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"))
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RefreshToken(Base):
    """Refresh tokens persistidos (hash) para revocación y rotación."""
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    sujeto_tipo: Mapped[SujetoTipo] = mapped_column(
        Enum(SujetoTipo, native_enum=False, length=20, validate_strings=True)
    )
    sujeto_id: Mapped[int] = mapped_column(index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revocado: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OtpCode(Base):
    """Código OTP de un solo uso para login de cliente (teléfono + CI + código).

    Solo se guarda el hash del código. `intentos` limita la fuerza bruta;
    `usado_en` lo invalida tras consumirse.
    """
    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    # cliente_id nulo en OTP de REGISTRO (el cliente aún no existe): se liga
    # solo por `telefono`. En OTP de login ambos campos van llenos.
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), index=True, nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    codigo_hash: Mapped[str] = mapped_column(String(64), index=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    intentos: Mapped[int] = mapped_column(default=0)
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
