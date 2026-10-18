from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, EmailStr, Field

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


# --- Socios ---

class OwnerCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    email: EmailStr


class SocioCreate(BaseModel):
    nombre_comercial: str = Field(min_length=2, max_length=200)
    razon_social: str | None = None
    nit_rut: str = Field(min_length=4, max_length=50)
    email_contacto: EmailStr | None = None
    telefono: str | None = None
    logo_url: str | None = None
    categoria_id: int | None = None
    esquema_comision_id: int | None = None
    owner: OwnerCreate


class SocioUpdate(BaseModel):
    nombre_comercial: str | None = Field(default=None, min_length=2, max_length=200)
    razon_social: str | None = None
    nit_rut: str | None = Field(default=None, min_length=4, max_length=50)
    email_contacto: EmailStr | None = None
    telefono: str | None = None
    logo_url: str | None = None
    categoria_id: int | None = None
    esquema_comision_id: int | None = None


class SocioListItem(BaseModel):
    id: int
    nombre_comercial: str
    nit_rut: str
    logo_url: str | None = None
    categoria: str | None
    esquema: str | None
    estado: str
    created_at: datetime


class OwnerOut(BaseModel):
    id: int
    nombre: str
    email: str
    estado: str
    onboarding_pendiente: bool


class SocioDetalle(BaseModel):
    id: int
    nombre_comercial: str
    razon_social: str | None
    nit_rut: str
    email_contacto: str | None
    telefono: str | None
    logo_url: str | None
    categoria_id: int | None
    categoria: str | None
    esquema_comision_id: int | None
    esquema: str | None
    estado: str
    created_at: datetime
    suspendido_en: datetime | None
    owner: OwnerOut | None
    total_sucursales: int
    total_empleados: int
    total_clientes: int
    total_premios_activos: int
    plan_id: int | None
    plan: str | None
    trial_fin: datetime | None
    facturacion_estado: str = "al_dia"


class SocioCreadoResponse(BaseModel):
    socio: SocioDetalle
    onboarding_link: str  # link enviado por email (visible para el admin que lo creó)


class KpisSocio(BaseModel):
    clientes_nuevos: int
    puntos_emitidos: int
    puntos_consumidos: int
    canjes_exitosos: int
    horas_a_primer_giro: float | None = None
    transacciones_totales: int = 0
    total_clientes_unicos: int = 0
    serie_diaria: list[dict] = []


class UsuarioListItem(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    estado: str
    ultimo_login: datetime | None


class SucursalListItem(BaseModel):
    id: int
    nombre: str
    direccion: str | None
    encargado_nombre: str | None
    estado: str


class ClienteListItem(BaseModel):
    id: int
    nombre: str
    ci: str
    telefono: str
    estado: str
    created_at: datetime


# --- Catálogos ---

class CategoriaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    icono_url: str | None = None
    activa: bool = True


class CategoriaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    icono_url: str | None = None
    activa: bool | None = None


class CategoriaOut(BaseModel):
    id: int
    nombre: str
    slug: str
    icono_url: str | None
    activa: bool
    socios_vinculados: int


class EsquemaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    costo_registro: float = Field(ge=0)
    costo_canje: float = Field(ge=0)
    moneda: str = Field(default="BOB", max_length=8)
    activo: bool = True


class EsquemaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    costo_registro: float | None = Field(default=None, ge=0)
    costo_canje: float | None = Field(default=None, ge=0)
    moneda: str | None = Field(default=None, max_length=8)
    activo: bool | None = None


class EsquemaOut(BaseModel):
    id: int
    nombre: str
    costo_registro: float
    costo_canje: float
    moneda: str
    activo: bool
    has_usage: bool  # si tiene uso, los montos son inmutables (regla #5)


# --- Transacciones ---

class TransaccionOut(BaseModel):
    id: int
    created_at: datetime
    tenant_id: int | None
    socio: str | None
    sucursal: str | None
    cliente_id: int
    cliente_nombre: str
    cliente_ci: str
    tipo: str
    puntos: int
    ejecutado_por: str | None
    premio: str | None
    detalle: dict | None


# --- Liquidaciones ---

class GenerarLiquidacionesIn(BaseModel):
    periodo: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")  # 'YYYY-MM'


class LiquidacionOut(BaseModel):
    id: int
    tenant_id: int
    socio: str
    periodo: str
    clientes_nuevos: int
    canjes_validados: int
    costo_registro_unit: float
    costo_canje_unit: float
    monto_total: float
    moneda: str = "BOB"
    estado: str
    pagada_en: datetime | None
    aprobada_por: str | None
    created_at: datetime


class LiquidacionGenerada(BaseModel):
    periodo: str
    generadas: int
    actualizadas: int
    omitidas_pagadas: int


# --- Dashboard ---

class KpisGlobales(BaseModel):
    socios_activos: int
    socios_suspendidos: int
    transacciones_hoy: int
    liquidaciones_pendientes: int
    monto_pendiente: float
    clientes_totales: int
    ttfs_medio_h: float | None = None  # tiempo medio hasta el primer giro (activación)
    facturas_pendientes: int = 0
    monto_facturacion_pendiente: float = 0.0


class SerieDia(BaseModel):
    fecha: str
    total: int


class TopSocioItem(BaseModel):
    id: int
    nombre: str
    logo_url: str | None = None
    transacciones: int
    clientes: int


class DistribucionTipoItem(BaseModel):
    tipo: str
    cantidad: int
    porcentaje: float


class DashboardOut(BaseModel):
    kpis: KpisGlobales
    transacciones_30d: list[SerieDia]
    ultimas_transacciones: list[TransaccionOut]
    top_socios: list[TopSocioItem] = []
    distribucion_tipos: list[DistribucionTipoItem] = []



# --- Planes SaaS ---

class PlanIn(BaseModel):
    slug: str = Field(min_length=2, max_length=40, pattern=r"^[a-z0-9-]+$")
    nombre: str = Field(min_length=2, max_length=80)
    descripcion: str | None = Field(default=None, max_length=300)
    precio_mensual: float = Field(default=0, ge=0)
    moneda: str = Field(default="BOB", min_length=3, max_length=3)
    max_sucursales: int = Field(default=0, ge=0)
    max_pantallas: int = Field(default=0, ge=0)
    max_clientes: int = Field(default=0, ge=0)
    max_empleados: int = Field(default=0, ge=0)
    ruleta_habilitada: bool = True
    orden: int = 0
    activo: bool = True


class PlanUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=80)
    descripcion: str | None = None
    precio_mensual: float | None = Field(default=None, ge=0)
    moneda: str | None = Field(default=None, min_length=3, max_length=3)
    max_sucursales: int | None = Field(default=None, ge=0)
    max_pantallas: int | None = Field(default=None, ge=0)
    max_clientes: int | None = Field(default=None, ge=0)
    max_empleados: int | None = Field(default=None, ge=0)
    ruleta_habilitada: bool | None = None
    orden: int | None = None
    activo: bool | None = None


class PlanOut(BaseModel):
    id: int
    slug: str
    nombre: str
    descripcion: str | None
    precio_mensual: float
    moneda: str
    max_sucursales: int
    max_pantallas: int
    max_clientes: int
    max_empleados: int
    ruleta_habilitada: bool
    orden: int
    activo: bool
    tenants_asignados: int = 0


class SocioPlanUpdate(BaseModel):
    plan_id: int | None = None
    trial_fin: datetime | None = None


class FacturaOut(BaseModel):
    id: int
    tenant_id: int
    socio_nombre: str
    plan_nombre: str
    periodo: str
    monto: float
    moneda: str
    estado: str
    emitida_en: datetime
    vence_en: datetime
    pagada_en: datetime | None
    metodo: str | None
    referencia: str | None


class FacturaPagarIn(BaseModel):
    metodo: str = "transferencia"
    referencia: str | None = None
