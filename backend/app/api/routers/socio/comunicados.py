"""Comunicados del socio: ofertas/novedades que aparecen en el feed de la app."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_owner
from app.core.security import utcnow
from app.db.session import get_db
from app.models import Comunicado, EstadoComunicado, EstadoPremio, Premio, Usuario
from app.schemas.auth import MessageResponse
from app.schemas.socio import (
    ComunicadoIn, ComunicadoOut, ComunicadoUpdate, FirmaUploadOut,
)
from app.services.audit import registrar_audit
from app.services.uploads import firma_disponible, generar_firma

router = APIRouter(dependencies=[Depends(require_owner)])


def _out(db: Session, c: Comunicado) -> ComunicadoOut:
    premio = db.get(Premio, c.premio_id) if c.premio_id else None
    return ComunicadoOut(
        id=c.id, tenant_id=c.tenant_id, titulo=c.titulo, descripcion=c.descripcion,
        imagen_url=c.imagen_url, imagen_public_id=c.imagen_public_id,
        premio_id=c.premio_id, premio_nombre=premio.nombre if premio else None,
        estado=c.estado.value, publicado_en=c.publicado_en,
        vigencia_hasta=c.vigencia_hasta, created_at=c.created_at,
    )


def _propio(db: Session, comunicado_id: int, tenant_id: int) -> Comunicado:
    c = db.get(Comunicado, comunicado_id)
    if not c or c.tenant_id != tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comunicado no encontrado")
    return c


def _validar_premio(db: Session, premio_id: int | None, tenant_id: int) -> None:
    if premio_id is None:
        return
    p = db.get(Premio, premio_id)
    if not p or p.tenant_id != tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El premio no pertenece a tu comercio")
    if p.estado != EstadoPremio.activo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El premio no está activo")


@router.post("/uploads/firma", response_model=FirmaUploadOut)
def firma_upload(carpeta: str = Query("comunicados", max_length=40,
                                      pattern=r"^[a-z0-9_\-]+$"),
                 usuario: Usuario = Depends(require_owner)):
    """Firma para subir la imagen directo a Cloudinary desde el navegador."""
    if not firma_disponible():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Almacenamiento de imágenes no configurado (Cloudinary)",
        )
    return FirmaUploadOut(**generar_firma(usuario.tenant_id, carpeta))


@router.get("", response_model=list[ComunicadoOut])
def listar(usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Comunicado).where(Comunicado.tenant_id == usuario.tenant_id)
        .order_by(Comunicado.created_at.desc())
    ).all()
    return [_out(db, c) for c in rows]


@router.post("", response_model=ComunicadoOut, status_code=status.HTTP_201_CREATED)
def crear(data: ComunicadoIn, usuario: Usuario = Depends(require_owner),
          db: Session = Depends(get_db)):
    _validar_premio(db, data.premio_id, usuario.tenant_id)
    c = Comunicado(tenant_id=usuario.tenant_id, **data.model_dump())
    db.add(c)
    db.flush()
    registrar_audit(db, usuario.id, "crear_comunicado", "comunicado", c.id,
                    {"titulo": c.titulo})
    db.commit()
    return _out(db, c)


@router.patch("/{comunicado_id}", response_model=ComunicadoOut)
def editar(comunicado_id: int, data: ComunicadoUpdate,
           usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    c = _propio(db, comunicado_id, usuario.tenant_id)
    cambios = data.model_dump(exclude_unset=True)
    if "premio_id" in cambios:
        _validar_premio(db, cambios["premio_id"], usuario.tenant_id)
    for k, v in cambios.items():
        setattr(c, k, v)
    registrar_audit(db, usuario.id, "editar_comunicado", "comunicado", c.id,
                    {"cambios": list(cambios.keys())})
    db.commit()
    return _out(db, c)


@router.post("/{comunicado_id}/publicar", response_model=ComunicadoOut)
def publicar(comunicado_id: int, usuario: Usuario = Depends(require_owner),
             db: Session = Depends(get_db)):
    c = _propio(db, comunicado_id, usuario.tenant_id)
    c.estado = EstadoComunicado.publicado
    if c.publicado_en is None:
        c.publicado_en = utcnow()
    registrar_audit(db, usuario.id, "publicar_comunicado", "comunicado", c.id)
    db.commit()
    return _out(db, c)


@router.post("/{comunicado_id}/archivar", response_model=ComunicadoOut)
def archivar(comunicado_id: int, usuario: Usuario = Depends(require_owner),
             db: Session = Depends(get_db)):
    c = _propio(db, comunicado_id, usuario.tenant_id)
    c.estado = EstadoComunicado.archivado
    registrar_audit(db, usuario.id, "archivar_comunicado", "comunicado", c.id)
    db.commit()
    return _out(db, c)


@router.delete("/{comunicado_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(comunicado_id: int, usuario: Usuario = Depends(require_owner),
             db: Session = Depends(get_db)):
    c = _propio(db, comunicado_id, usuario.tenant_id)
    registrar_audit(db, usuario.id, "eliminar_comunicado", "comunicado", c.id,
                    {"titulo": c.titulo})
    db.delete(c)
    db.commit()
    return MessageResponse(detail="Comunicado eliminado")
