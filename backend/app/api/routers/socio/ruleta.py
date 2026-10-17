from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_owner
from app.db.session import get_db
from app.models import RuletaSegmento, Tenant, Usuario
from app.schemas.socio import SegmentoIn, SegmentoOut, SegmentoUpdate
from app.services.audit import registrar_audit
from app.services.planes import verificar_ruleta

router = APIRouter(dependencies=[Depends(require_owner)])


def _get_segmento(db: Session, tenant_id: int, seg_id: int) -> RuletaSegmento:
    s = db.scalar(
        select(RuletaSegmento).where(
            RuletaSegmento.id == seg_id, RuletaSegmento.tenant_id == tenant_id
        )
    )
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Segmento no encontrado")
    return s


def _out(s: RuletaSegmento) -> SegmentoOut:
    return SegmentoOut(id=s.id, etiqueta=s.etiqueta, puntos=s.puntos,
                       peso=s.peso, color=s.color, activo=s.activo)


@router.get("/segmentos", response_model=list[SegmentoOut])
def listar_segmentos(usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(RuletaSegmento).where(RuletaSegmento.tenant_id == usuario.tenant_id)
        .order_by(RuletaSegmento.id)
    ).all()
    return [_out(s) for s in rows]


@router.post("/segmentos", response_model=SegmentoOut, status_code=status.HTTP_201_CREATED)
def crear_segmento(data: SegmentoIn, usuario: Usuario = Depends(require_owner),
                   db: Session = Depends(get_db)):
    verificar_ruleta(db, db.get(Tenant, usuario.tenant_id))
    s = RuletaSegmento(tenant_id=usuario.tenant_id, **data.model_dump())
    db.add(s)
    db.flush()
    registrar_audit(db, usuario.id, "crear_segmento", "ruleta_segmento", s.id)
    db.commit()
    return _out(s)


@router.patch("/segmentos/{seg_id}", response_model=SegmentoOut)
def editar_segmento(seg_id: int, data: SegmentoUpdate,
                    usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    s = _get_segmento(db, usuario.tenant_id, seg_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(s, campo, valor)
    registrar_audit(db, usuario.id, "editar_segmento", "ruleta_segmento", s.id)
    db.commit()
    return _out(s)


@router.delete("/segmentos/{seg_id}")
def eliminar_segmento(seg_id: int, usuario: Usuario = Depends(require_owner),
                      db: Session = Depends(get_db)):
    s = _get_segmento(db, usuario.tenant_id, seg_id)
    registrar_audit(db, usuario.id, "eliminar_segmento", "ruleta_segmento", s.id,
                    {"etiqueta": s.etiqueta})
    db.delete(s)
    db.commit()
    return {"detail": "Segmento eliminado"}
