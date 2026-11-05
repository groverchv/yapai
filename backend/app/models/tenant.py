import enum
from datetime import datetime

from app.db.session import Base
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class EstadoTenant(str, enum.Enum):
    activo = "activo"
    suspendido = "suspendido"


class EstadoSucursal(str, enum.Enum):
    activa = "activa"
    suspendida = "suspendida"


class EstadoPantalla(str, enum.Enum):
    activa = "activa"
    bloqueada = "bloqueada"


class ModoPin(str, enum.Enum):
    por_sucursal = "por_sucursal"
    por_cajero = "por_cajero"


class Tenant(Base):
    """Socio comercial afiliado a YAPAI."""
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_comercial: Mapped[str] = mapped_column(String(200), index=True)
    razon_social: Mapped[str | None] = mapped_column(String(200), nullable=True)
    nit_rut: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias_negocio.id"), nullable=True)
    esquema_comision_id: Mapped[int | None] = mapped_column(ForeignKey("esquemas_comision.id"), nullable=True)
    email_contacto: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estado: Mapped[EstadoTenant] = mapped_column(
        Enum(EstadoTenant, native_enum=False, length=20, validate_strings=True),
        default=EstadoTenant.activo,
    )
    # Configuración del programa de puntos (regla #11 y kiosco)
    puntos_registro: Mapped[int] = mapped_column(Integer, default=300)
    puntos_referido: Mapped[int] = mapped_column(Integer, default=100)
    max_puntos_tx: Mapped[int] = mapped_column(Integer, default=500)
    max_puntos_dia_cajero: Mapped[int] = mapped_column(Integer, default=2000)
    suspendido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspendido_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    # SaaS: plan comercial y fin del período de prueba
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("planes.id"), nullable=True)
    trial_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Sucursal(Base):
    __tablename__ = "sucursales"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(160))
    direccion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # Coordenadas para "cómo llegar" (deep-link a GPS/Maps desde la app del cliente)
    latitud: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitud: Mapped[float | None] = mapped_column(Float, nullable=True)
    encargado_nombre: Mapped[str | None] = mapped_column(String(160), nullable=True)
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estado: Mapped[EstadoSucursal] = mapped_column(
        Enum(EstadoSucursal, native_enum=False, length=20, validate_strings=True),
        default=EstadoSucursal.activa,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmpleadoSucursal(Base):
    """Asignación M:N de cajeros a sucursales."""
    __tablename__ = "empleado_sucursal"

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), primary_key=True)


class Pantalla(Base):
    """Kiosco físico del local. Se habilita con PIN de caja."""
    __tablename__ = "pantallas"

    id: Mapped[int] = mapped_column(primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    device_token: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    estado: Mapped[EstadoPantalla] = mapped_column(
        Enum(EstadoPantalla, native_enum=False, length=20, validate_strings=True),
        default=EstadoPantalla.activa,
    )
    habilitada_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    habilitada_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConfigPin(Base):
    """Modalidad del candado de caja por tenant."""
    __tablename__ = "config_pin"

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), primary_key=True)
    modo: Mapped[ModoPin] = mapped_column(
        Enum(ModoPin, native_enum=False, length=20, validate_strings=True),
        default=ModoPin.por_sucursal,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PinSucursal(Base):
    __tablename__ = "pin_sucursal"

    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), primary_key=True)
    pin_hash: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PinCajero(Base):
    __tablename__ = "pin_cajero"

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), primary_key=True)
    pin_hash: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
