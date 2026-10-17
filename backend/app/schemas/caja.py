from datetime import datetime

from pydantic import BaseModel, Field


class SucursalOpcion(BaseModel):
    id: int
    nombre: str


class CajeroOpcion(BaseModel):
    id: int
    nombre: str


class ContextoCajaOut(BaseModel):
    cajero_id: int
    cajero_nombre: str
    rol: str
    sucursales: list[SucursalOpcion]
    modo_pin: str
    max_puntos_tx: int
    max_puntos_dia_cajero: int
    bonus_hoy: int


class PasePreviewOut(BaseModel):
    pase_id: int
    estado: str
    cliente_nombre: str
    cliente_ci: str
    premio_nombre: str
    puntos: int
    comercio: str
    expira_en: datetime | None


class CanjearIn(BaseModel):
    sucursal_id: int


class CanjearOut(BaseModel):
    detail: str
    pase_id: int
    cliente_nombre: str
    premio_nombre: str
    puntos: int
    saldo_cliente: int
    stock_restante: int | None


class ClienteBusquedaOut(BaseModel):
    id: int
    nombre: str
    ci: str
    telefono: str
    saldo_puntos: int


class BonusIn(BaseModel):
    cliente_id: int
    sucursal_id: int
    puntos: int = Field(ge=1)
    motivo: str = Field(min_length=3, max_length=200)


class BonusOut(BaseModel):
    detail: str
    puntos: int
    saldo_cliente: int
    bonus_hoy: int
    limite_dia: int
