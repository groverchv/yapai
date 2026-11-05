from app.core.deps import require_owner
from app.core.security import hash_secret
from app.db.session import get_db
from app.models import (
    ConfigPin,
    ModoPin,
    PinCajero,
    PinSucursal,
    RolUsuario,
    Sucursal,
    Usuario,
)
from app.schemas.socio import PinConfigOut, PinModoIn, PinSetIn
from app.services.audit import registrar_audit
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_owner)])


@router.get("/config", response_model=PinConfigOut)
def obtener_config(usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    config = db.get(ConfigPin, usuario.tenant_id)
    sucursales = db.scalars(
        select(Sucursal).where(Sucursal.tenant_id == usuario.tenant_id).order_by(Sucursal.id)
    ).all()
    cajeros = db.scalars(
        select(Usuario).where(Usuario.tenant_id == usuario.tenant_id, Usuario.rol == RolUsuario.cajero)
    ).all()
    return PinConfigOut(
        modo=config.modo.value if config else ModoPin.por_sucursal.value,
        sucursales=[{
            "id": s.id, "nombre": s.nombre,
            "pin_set": db.scalar(select(PinSucursal.sucursal_id).where(PinSucursal.sucursal_id == s.id)) is not None,
        } for s in sucursales],
        cajeros=[{
            "id": c.id, "nombre": c.nombre,
            "pin_set": db.scalar(select(PinCajero.usuario_id).where(PinCajero.usuario_id == c.id)) is not None,
        } for c in cajeros],
    )


@router.put("/config", response_model=PinConfigOut)
def cambiar_modo(data: PinModoIn, usuario: Usuario = Depends(require_owner),
                 db: Session = Depends(get_db)):
    config = db.get(ConfigPin, usuario.tenant_id)
    if not config:
        config = ConfigPin(tenant_id=usuario.tenant_id)
        db.add(config)
    config.modo = ModoPin(data.modo)
    registrar_audit(db, usuario.id, "cambiar_modo_pin", "config_pin", usuario.tenant_id,
                    {"modo": data.modo})
    db.commit()
    return obtener_config(usuario, db)


@router.post("/sucursal/{sucursal_id}", response_model=dict)
def set_pin_sucursal(sucursal_id: int, data: PinSetIn,
                     usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    """Crea o rota el PIN de una sucursal (hash, nunca en plano — regla #14)."""
    s = db.scalar(
        select(Sucursal).where(Sucursal.id == sucursal_id, Sucursal.tenant_id == usuario.tenant_id)
    )
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada")
    row = db.get(PinSucursal, sucursal_id)
    if not row:
        row = PinSucursal(sucursal_id=sucursal_id, pin_hash="")
        db.add(row)
    row.pin_hash = hash_secret(data.pin)
    registrar_audit(db, usuario.id, "rotar_pin_sucursal", "sucursal", sucursal_id)
    db.commit()
    return {"detail": "PIN de sucursal actualizado", "pin_set": True}


@router.post("/cajero/{cajero_id}", response_model=dict)
def set_pin_cajero(cajero_id: int, data: PinSetIn,
                   usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    c = db.scalar(
        select(Usuario).where(
            Usuario.id == cajero_id, Usuario.tenant_id == usuario.tenant_id,
            Usuario.rol == RolUsuario.cajero,
        )
    )
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cajero no encontrado")
    row = db.get(PinCajero, cajero_id)
    if not row:
        row = PinCajero(usuario_id=cajero_id, pin_hash="")
        db.add(row)
    row.pin_hash = hash_secret(data.pin)
    registrar_audit(db, usuario.id, "rotar_pin_cajero", "usuario", cajero_id)
    db.commit()
    return {"detail": "PIN de cajero actualizado", "pin_set": True}
