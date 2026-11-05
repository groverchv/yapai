from datetime import datetime

from app.schemas.admin import SerieDia
from pydantic import BaseModel, EmailStr, Field

# --- Perfil ---

class PerfilOut(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    tenant_id: int
    tenant_nombre: str
    logo_url: str | None = None
    telefono: str | None = None
    email_contacto: str | None = None


class PerfilUpdate(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    tenant_nombre: str | None = Field(default=None, max_length=200)
    logo_url: str | None = Field(default=None, max_length=500)
    telefono: str | None = Field(default=None, max_length=50)


class MediaUploadOut(BaseModel):
    url: str
    public_id: str | None = None


class CambiarPasswordIn(BaseModel):
    password_actual: str
    password_nuevo: str = Field(min_length=8, max_length=128)


# --- Empleados ---

class EmpleadoIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    email: EmailStr
    foto_url: str | None = None
    sucursal_ids: list[int] = []


class EmpleadoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=160)
    foto_url: str | None = None
    sucursal_ids: list[int] | None = None


class EmpleadoOut(BaseModel):
    id: int
    nombre: str
    email: str
    foto_url: str | None = None
    estado: str
    onboarding_pendiente: bool
    sucursales: list[str]
    ultimo_login: datetime | None


# --- Sucursales ---

class SucursalIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    direccion: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    encargado_nombre: str | None = None
    imagen_url: str | None = None


class SucursalUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=160)
    direccion: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    encargado_nombre: str | None = None
    imagen_url: str | None = None


class PantallaOut(BaseModel):
    id: int
    nombre: str
    device_token: str
    estado: str
    habilitada_hasta: datetime | None


class SucursalDetalleOut(BaseModel):
    id: int
    nombre: str
    direccion: str | None
    latitud: float | None = None
    longitud: float | None = None
    encargado_nombre: str | None
    imagen_url: str | None = None
    estado: str
    pin_set: bool
    pantallas: list[PantallaOut]


class PantallaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)


# --- PIN de caja ---

class PinConfigOut(BaseModel):
    modo: str
    sucursales: list[dict]  # [{id, nombre, pin_set}]
    cajeros: list[dict]     # [{id, nombre, pin_set}]


class PinModoIn(BaseModel):
    modo: str = Field(pattern="^(por_sucursal|por_cajero)$")


class PinSetIn(BaseModel):
    pin: str = Field(pattern=r"^\d{4}$")


# --- Premios ---

class PremioIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    descripcion: str | None = Field(default=None, max_length=500)
    costo_puntos: int = Field(ge=1)
    imagen_url: str | None = None
    stock_limitado: bool = False
    stock: int | None = Field(default=None, ge=0)
    vigencia_hasta: datetime | None = None


class PremioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=160)
    descripcion: str | None = None
    costo_puntos: int | None = Field(default=None, ge=1)
    imagen_url: str | None = None
    stock_limitado: bool | None = None
    stock: int | None = Field(default=None, ge=0)
    vigencia_hasta: datetime | None = None


class PremioOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    costo_puntos: int
    imagen_url: str | None
    stock_limitado: bool
    stock: int | None
    estado: str
    pases_activos: int
    vigencia_hasta: datetime | None


# --- Campañas ---

class CampanaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    multiplicador: int = Field(default=2, ge=2, le=10)
    inicio: datetime
    fin: datetime
    sucursal_id: int | None = None
    activa: bool = True


class CampanaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=160)
    multiplicador: int | None = Field(default=None, ge=2, le=10)
    inicio: datetime | None = None
    fin: datetime | None = None
    sucursal_id: int | None = None
    activa: bool | None = None


class CampanaOut(BaseModel):
    id: int
    nombre: str
    multiplicador: int
    inicio: datetime
    fin: datetime
    sucursal_id: int | None
    sucursal_nombre: str | None
    activa: bool
    vigente: bool


class InactivoOut(BaseModel):
    cliente_id: int
    nombre: str
    telefono: str
    ult_actividad: datetime
    dias_inactivo: int
    saldo: int


# --- Ruleta ---

class SegmentoIn(BaseModel):
    etiqueta: str = Field(min_length=1, max_length=80)
    puntos: int = Field(ge=0)
    peso: int = Field(default=1, ge=1)
    color: str | None = None
    activo: bool = True


class SegmentoUpdate(BaseModel):
    etiqueta: str | None = Field(default=None, min_length=1, max_length=80)
    puntos: int | None = Field(default=None, ge=0)
    peso: int | None = Field(default=None, ge=1)
    color: str | None = None
    activo: bool | None = None


class SegmentoOut(BaseModel):
    id: int
    etiqueta: str
    puntos: int
    peso: int
    color: str | None
    activo: bool


# --- Métricas ---


class PremioStockBajo(BaseModel):
    id: int
    nombre: str
    stock: int


class TopPremioSocio(BaseModel):
    id: int
    nombre: str
    costo_puntos: int
    stock: int | None = None
    imagen_url: str | None = None
    total_canjes: int = 0


class ResumenPrevio(BaseModel):
    """KPIs del período espejo anterior (solo cuando hay rango desde/hasta)."""
    clientes_nuevos: int
    puntos_otorgados: int
    puntos_consumidos: int
    canjes_exitosos: int


class ResumenSocio(BaseModel):
    clientes_nuevos: int
    puntos_otorgados: int
    puntos_consumidos: int
    canjes_exitosos: int
    stock_critico: list[PremioStockBajo]
    clientes_totales: int = 0
    tasa_redencion: float = 0.0
    transacciones_hoy: int = 0
    pases_activos: int = 0
    transacciones_30d: list[SerieDia] = []
    top_premios: list[TopPremioSocio] = []
    previos: ResumenPrevio | None = None


# --- Plan del socio ---

class PlanUsoOut(BaseModel):
    sucursales: int
    pantallas: int
    clientes: int
    empleados: int


class PlanLimitesOut(BaseModel):
    max_sucursales: int
    max_pantallas: int
    max_clientes: int
    max_empleados: int
    ruleta_habilitada: bool


class SocioPlanOut(BaseModel):
    plan_id: int | None
    plan_nombre: str | None
    plan_slug: str | None
    precio_mensual: float | None
    moneda: str
    limites: PlanLimitesOut | None
    uso: PlanUsoOut
    en_trial: bool
    dias_trial: int
    trial_fin: datetime | None


# --- Onboarding del socio ---

class PasoOnboarding(BaseModel):
    clave: str
    etiqueta: str
    hecho: bool
    href: str | None


class OnboardingOut(BaseModel):
    pasos: list[PasoOnboarding]
    completados: int
    total: int
    completado: bool


class FacturaSocioOut(BaseModel):
    id: int
    plan_nombre: str
    periodo: str
    monto: float
    moneda: str
    estado: str
    emitida_en: datetime
    vence_en: datetime
    pagada_en: datetime | None
    metodo: str | None


class EstadoCuentaOut(BaseModel):
    estado: str                      # al_dia | pendiente | vencida
    facturas: list[FacturaSocioOut]


class PantallaQrOut(BaseModel):
    svg: str
    url: str


# --- Comunicados (ofertas) ---

class ComunicadoIn(BaseModel):
    titulo: str = Field(min_length=3, max_length=160)
    descripcion: str | None = Field(default=None, max_length=2000)
    imagen_url: str = Field(max_length=500)
    imagen_public_id: str | None = Field(default=None, max_length=200)
    premio_id: int | None = None
    vigencia_hasta: datetime | None = None


class ComunicadoUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=3, max_length=160)
    descripcion: str | None = Field(default=None, max_length=2000)
    imagen_url: str | None = Field(default=None, max_length=500)
    imagen_public_id: str | None = Field(default=None, max_length=200)
    premio_id: int | None = None
    vigencia_hasta: datetime | None = None


class ComunicadoOut(BaseModel):
    id: int
    tenant_id: int
    titulo: str
    descripcion: str | None
    imagen_url: str
    imagen_public_id: str | None
    premio_id: int | None
    premio_nombre: str | None = None
    estado: str
    publicado_en: datetime | None
    vigencia_hasta: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class FirmaUploadOut(BaseModel):
    cloud_name: str
    api_key: str
    timestamp: int
    folder: str
    signature: str
