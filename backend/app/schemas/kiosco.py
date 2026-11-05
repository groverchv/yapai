from datetime import datetime

from pydantic import BaseModel, Field


class SegmentoPublico(BaseModel):
    etiqueta: str
    puntos: int
    peso: int
    color: str | None


class KioscoConfigOut(BaseModel):
    comercio: str
    logo_url: str | None
    sucursal: str
    pantalla: str
    habilitada_hasta: datetime
    puntos_registro: int
    segmentos: list[SegmentoPublico]


class RegistroKioscoIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    ci: str = Field(min_length=3, max_length=50)
    telefono: str = Field(min_length=4, max_length=30)
    codigo_referido: str | None = Field(default=None, max_length=12)
    acepto_terminos: bool = False


class RegistroKioscoOut(BaseModel):
    cliente_id: int
    nombre: str
    nuevo: bool
    puntos_otorgados: int
    saldo: int
    multiplicador: int = 1
    campana: str | None = None
    referido_bonus: int = 0


class GirarIn(BaseModel):
    cliente_id: int


class GirarOut(BaseModel):
    etiqueta: str
    puntos: int
    color: str | None
    saldo: int
    indice: int  # posición en la lista de segmentos activos (para animar la rueda)
    multiplicador: int = 1
    campana: str | None = None
