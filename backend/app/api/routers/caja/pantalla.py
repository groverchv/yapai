"""Habilitación de pantalla física por PIN (flujo 9.2, regla #14).

Sin login: el cajero digita el PIN en la pantalla del local.
Según `config_pin.modo` se valida el PIN de la sucursal o el del cajero
(en modo por_cajero se requiere además `cajero_id` para saber quién habilitó).
"""

from datetime import datetime, timedelta, timezone

from app.core.ratelimit import pin_limiter
from app.core.security import verify_secret
from app.db.session import get_db
from app.models import (
    ConfigPin,
    EstadoPantalla,
    EstadoSucursal,
    EstadoTenant,
    EstadoUsuario,
    ModoPin,
    Pantalla,
    PinCajero,
    PinSucursal,
    RolUsuario,
    Sucursal,
    Tenant,
    Usuario,
)
from app.services.audit import registrar_audit
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()

HABILITACION_HORAS = 8  # un turno


class HabilitarIn(BaseModel):
    device_token: str
    pin: str = Field(pattern=r"^\d{4}$")
    cajero_id: int | None = None  # requerido si modo = por_cajero


class HabilitarOut(BaseModel):
    habilitada_hasta: datetime
    pantalla: str
    sucursal: str
    habilitada_por: str | None


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


@router.post("/pantalla/habilitar", response_model=HabilitarOut,
             dependencies=[Depends(pin_limiter)])
def habilitar(data: HabilitarIn, db: Session = Depends(get_db)):
    pantalla = db.scalar(select(Pantalla).where(Pantalla.device_token == data.device_token))
    if not pantalla:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pantalla no encontrada")
    if pantalla.estado == EstadoPantalla.bloqueada:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Pantalla bloqueada")

    sucursal = db.get(Sucursal, pantalla.sucursal_id)
    if not sucursal or sucursal.estado != EstadoSucursal.activa:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La sucursal está suspendida")
    tenant = db.get(Tenant, sucursal.tenant_id)
    if not tenant or tenant.estado != EstadoTenant.activo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El comercio está suspendido")

    config = db.get(ConfigPin, tenant.id)
    modo = config.modo if config else ModoPin.por_sucursal
    habilitada_por: str | None = None
    cajero: Usuario | None = None

    if modo == ModoPin.por_sucursal:
        row = db.get(PinSucursal, sucursal.id)
        if not row or not verify_secret(data.pin, row.pin_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "PIN incorrecto")
        habilitada_por = f"PIN sucursal {sucursal.nombre}"
    else:
        if data.cajero_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Debes indicar qué cajero eres")
        cajero = db.scalar(
            select(Usuario).where(
                Usuario.id == data.cajero_id,
                Usuario.tenant_id == tenant.id,
                Usuario.rol == RolUsuario.cajero,
                Usuario.estado == EstadoUsuario.activo,
            )
        )
        if not cajero:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cajero no encontrado")
        row = db.get(PinCajero, cajero.id)
        if not row or not verify_secret(data.pin, row.pin_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "PIN incorrecto")
        habilitada_por = cajero.nombre

    pantalla.habilitada_hasta = datetime.now(timezone.utc) + timedelta(hours=HABILITACION_HORAS)
    pantalla.habilitada_por = cajero.id if cajero else None
    if cajero:
        registrar_audit(db, cajero.id, "habilitar_pantalla", "pantalla", pantalla.id)
    db.commit()
    return HabilitarOut(
        habilitada_hasta=pantalla.habilitada_hasta,
        pantalla=pantalla.nombre, sucursal=sucursal.nombre,
        habilitada_por=habilitada_por,
    )
