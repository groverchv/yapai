from datetime import datetime

from pydantic import BaseModel, Field


# --- Cuenta ---

class PerfilClienteOut(BaseModel):
    id: int
    nombre: str
    ci: str
    telefono: str
    saldo_puntos: int
    puntos_congelados: int
    foto_url: str | None = None
    codigo_referido: str | None = None
    created_at: datetime


class ClienteUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=160)
    telefono: str | None = Field(default=None, min_length=4, max_length=30)
    foto_url: str | None = Field(default=None, max_length=500)


class WalletOut(BaseModel):
    saldo: int
    congelado: int
    disponible: int


class MovimientoClienteOut(BaseModel):
    id: int
    created_at: datetime
    tipo: str
    puntos: int
    comercio: str | None
    sucursal: str | None
    premio: str | None
    detalle: dict | None


# --- Explorador ---

class ComercioListOut(BaseModel):
    id: int
    nombre_comercial: str
    logo_url: str | None
    categoria: str | None
    total_premios: int


class SucursalClienteOut(BaseModel):
    id: int
    nombre: str
    direccion: str | None


class ComercioDetalleOut(BaseModel):
    id: int
    nombre_comercial: str
    logo_url: str | None
    categoria: str | None
    sucursales: list[SucursalClienteOut]


class PremioClienteOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    costo_puntos: int
    imagen_url: str | None
    alcanzable: bool
    vigencia_hasta: datetime | None = None


# --- Pases ---

class PaseCreateIn(BaseModel):
    premio_id: int


class PaseOut(BaseModel):
    id: int
    codigo_qr: str
    pin_corto: str
    puntos: int
    estado: str
    expira_en: datetime | None
    premio_nombre: str
    comercio: str
    created_at: datetime


# --- Comunicados (feed de ofertas) ---

class ComunicadoClienteOut(BaseModel):
    id: int
    titulo: str
    descripcion: str | None
    imagen_url: str
    premio_id: int | None
    publicado_en: datetime | None
    vigencia_hasta: datetime | None
    tenant_id: int
    comercio: str
    logo_url: str | None
