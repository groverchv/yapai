import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.deps import require_owner
from app.db.session import get_db
from app.models import (
    EstadoPantalla, EstadoSucursal, Pantalla, PinSucursal, Sucursal, Tenant, Usuario,
)
from app.core.config import settings
from app.schemas.auth import MessageResponse
from app.schemas.socio import (
    PantallaIn, PantallaOut, PantallaQrOut, SucursalDetalleOut, SucursalIn,
    SucursalUpdate,
)
from app.services.audit import registrar_audit
from app.services.planes import verificar_limite


def _tenant(db: Session, tenant_id: int) -> Tenant:
    t = db.get(Tenant, tenant_id)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant no encontrado")
    return t

router = APIRouter(dependencies=[Depends(require_owner)])


def _get_sucursal(db: Session, tenant_id: int, sucursal_id: int) -> Sucursal:
    s = db.scalar(
        select(Sucursal).where(Sucursal.id == sucursal_id, Sucursal.tenant_id == tenant_id)
    )
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada")
    return s


def _out(db: Session, s: Sucursal) -> SucursalDetalleOut:
    pantallas = db.scalars(select(Pantalla).where(Pantalla.sucursal_id == s.id)).all()
    pin_set = db.scalar(select(PinSucursal.sucursal_id).where(PinSucursal.sucursal_id == s.id)) is not None
    return SucursalDetalleOut(
        id=s.id, nombre=s.nombre, direccion=s.direccion,
        encargado_nombre=s.encargado_nombre, estado=s.estado.value, pin_set=pin_set,
        pantallas=[PantallaOut(
            id=p.id, nombre=p.nombre, device_token=p.device_token,
            estado=p.estado.value, habilitada_hasta=p.habilitada_hasta,
        ) for p in pantallas],
    )


@router.get("", response_model=list[SucursalDetalleOut])
def listar_sucursales(usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Sucursal).where(Sucursal.tenant_id == usuario.tenant_id).order_by(Sucursal.id)
    ).all()
    return [_out(db, s) for s in rows]


@router.post("", response_model=SucursalDetalleOut, status_code=status.HTTP_201_CREATED)
def crear_sucursal(data: SucursalIn, usuario: Usuario = Depends(require_owner),
                   db: Session = Depends(get_db)):
    verificar_limite(db, _tenant(db, usuario.tenant_id), "sucursales")
    s = Sucursal(tenant_id=usuario.tenant_id, **data.model_dump())
    db.add(s)
    db.flush()
    registrar_audit(db, usuario.id, "crear_sucursal", "sucursal", s.id)
    db.commit()
    return _out(db, s)


@router.patch("/{sucursal_id}", response_model=SucursalDetalleOut)
def editar_sucursal(sucursal_id: int, data: SucursalUpdate,
                    usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    s = _get_sucursal(db, usuario.tenant_id, sucursal_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(s, campo, valor)
    registrar_audit(db, usuario.id, "editar_sucursal", "sucursal", s.id)
    db.commit()
    return _out(db, s)


@router.post("/{sucursal_id}/suspender", response_model=SucursalDetalleOut)
def suspender_sucursal(sucursal_id: int, usuario: Usuario = Depends(require_owner),
                       db: Session = Depends(get_db)):
    """Regla #3: suspender la sucursal bloquea sus pantallas físicas."""
    s = _get_sucursal(db, usuario.tenant_id, sucursal_id)
    s.estado = EstadoSucursal.suspendida
    db.execute(
        update(Pantalla).where(Pantalla.sucursal_id == s.id)
        .values(estado=EstadoPantalla.bloqueada, habilitada_hasta=None)
    )
    registrar_audit(db, usuario.id, "suspender_sucursal", "sucursal", s.id)
    db.commit()
    return _out(db, s)


@router.post("/{sucursal_id}/reactivar", response_model=SucursalDetalleOut)
def reactivar_sucursal(sucursal_id: int, usuario: Usuario = Depends(require_owner),
                       db: Session = Depends(get_db)):
    s = _get_sucursal(db, usuario.tenant_id, sucursal_id)
    s.estado = EstadoSucursal.activa
    db.execute(
        update(Pantalla).where(Pantalla.sucursal_id == s.id)
        .values(estado=EstadoPantalla.activa, habilitada_hasta=None)
    )
    registrar_audit(db, usuario.id, "reactivar_sucursal", "sucursal", s.id)
    db.commit()
    return _out(db, s)


# --- Pantallas del kiosco ---

@router.post("/{sucursal_id}/pantallas", response_model=PantallaOut, status_code=status.HTTP_201_CREATED)
def crear_pantalla(sucursal_id: int, data: PantallaIn,
                   usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    _get_sucursal(db, usuario.tenant_id, sucursal_id)
    verificar_limite(db, _tenant(db, usuario.tenant_id), "pantallas")
    p = Pantalla(
        sucursal_id=sucursal_id, nombre=data.nombre,
        device_token=f"kiosco-{secrets.token_urlsafe(18)}",
    )
    db.add(p)
    db.flush()
    registrar_audit(db, usuario.id, "crear_pantalla", "pantalla", p.id)
    db.commit()
    return PantallaOut(id=p.id, nombre=p.nombre, device_token=p.device_token,
                       estado=p.estado.value, habilitada_hasta=p.habilitada_hasta)


@router.get("/pantallas/{pantalla_id}/qr", response_model=PantallaQrOut)
def qr_pantalla(pantalla_id: int, usuario: Usuario = Depends(require_owner),
                db: Session = Depends(get_db)):
    """QR imprimible que apunta al kiosco público de la pantalla."""
    import qrcode
    from qrcode.image.svg import SvgPathImage

    p = db.get(Pantalla, pantalla_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pantalla no encontrada")
    _get_sucursal(db, usuario.tenant_id, p.sucursal_id)  # valida pertenencia
    url = f"{settings.FRONTEND_SOCIO_URL}/kiosco/{p.device_token}"
    svg = qrcode.make(url, image_factory=SvgPathImage).to_string(encoding="unicode")
    return PantallaQrOut(svg=svg, url=url)


@router.post("/pantallas/{pantalla_id}/rotar-token", response_model=PantallaOut)
def rotar_token_pantalla(pantalla_id: int, usuario: Usuario = Depends(require_owner),
                         db: Session = Depends(get_db)):
    p = db.get(Pantalla, pantalla_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pantalla no encontrada")
    _get_sucursal(db, usuario.tenant_id, p.sucursal_id)  # valida pertenencia
    p.device_token = f"kiosco-{secrets.token_urlsafe(18)}"
    p.habilitada_hasta = None
    registrar_audit(db, usuario.id, "rotar_token_pantalla", "pantalla", p.id)
    db.commit()
    return PantallaOut(id=p.id, nombre=p.nombre, device_token=p.device_token,
                       estado=p.estado.value, habilitada_hasta=p.habilitada_hasta)
