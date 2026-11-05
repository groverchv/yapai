
from app.core.deps import require_owner
from app.core.security import utcnow
from app.db.session import get_db
from app.models import Campana, Sucursal, Usuario
from app.schemas.socio import CampanaIn, CampanaOut, CampanaUpdate, InactivoOut
from app.services.campanas import inactivos as servicio_inactivos
from app.services.export import csv_response
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_owner)])


def _aware(dt):
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=utcnow().tzinfo)


def _out(db: Session, c: Campana) -> CampanaOut:
    ahora = utcnow()
    return CampanaOut(
        id=c.id, nombre=c.nombre, multiplicador=c.multiplicador,
        inicio=c.inicio, fin=c.fin, sucursal_id=c.sucursal_id,
        sucursal_nombre=db.get(Sucursal, c.sucursal_id).nombre if c.sucursal_id else None,
        activa=c.activa, vigente=_aware(c.inicio) <= ahora <= _aware(c.fin),
    )


@router.get("", response_model=list[CampanaOut])
def listar(usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Campana).where(Campana.tenant_id == usuario.tenant_id)
        .order_by(Campana.id.desc())
    ).all()
    return [_out(db, c) for c in rows]


@router.post("", response_model=CampanaOut, status_code=status.HTTP_201_CREATED)
def crear(data: CampanaIn, usuario: Usuario = Depends(require_owner),
          db: Session = Depends(get_db)):
    if data.sucursal_id:
        suc = db.get(Sucursal, data.sucursal_id)
        if not suc or suc.tenant_id != usuario.tenant_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada")
    if data.fin <= data.inicio:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El fin debe ser posterior al inicio")
    c = Campana(tenant_id=usuario.tenant_id, **data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return _out(db, c)


@router.patch("/{campana_id}", response_model=CampanaOut)
def editar(campana_id: int, data: CampanaUpdate,
           usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    c = db.get(Campana, campana_id)
    if not c or c.tenant_id != usuario.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaña no encontrada")
    cambios = data.model_dump(exclude_unset=True)
    if "sucursal_id" in cambios and cambios["sucursal_id"]:
        suc = db.get(Sucursal, cambios["sucursal_id"])
        if not suc or suc.tenant_id != usuario.tenant_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Sucursal no encontrada")
    for k, v in cambios.items():
        setattr(c, k, v)
    if c.fin <= c.inicio:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El fin debe ser posterior al inicio")
    db.commit()
    return _out(db, c)


@router.delete("/{campana_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(campana_id: int, usuario: Usuario = Depends(require_owner),
             db: Session = Depends(get_db)):
    c = db.get(Campana, campana_id)
    if not c or c.tenant_id != usuario.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaña no encontrada")
    db.delete(c)
    db.commit()


def _inactivos_out(db: Session, tenant_id: int, dias: int) -> list[InactivoOut]:
    ahora = utcnow()
    return [
        InactivoOut(
            cliente_id=c.id, nombre=c.nombre, telefono=c.telefono,
            ult_actividad=ult, dias_inactivo=(ahora - ult).days,
            saldo=c.saldo_puntos - c.puntos_congelados,
        )
        for c, ult in servicio_inactivos(db, tenant_id, dias)
    ]


@router.get("/inactivos", response_model=list[InactivoOut])
def listar_inactivos(dias: int = Query(30, ge=1, le=365),
                     usuario: Usuario = Depends(require_owner),
                     db: Session = Depends(get_db)):
    """Segmento de clientes sin actividad en el tenant hace más de `dias` días —
    para reactivarlos por WhatsApp/llamada (los clientes no tienen email)."""
    return _inactivos_out(db, usuario.tenant_id, dias)


@router.get("/inactivos.csv")
def inactivos_csv(dias: int = Query(30, ge=1, le=365),
                  usuario: Usuario = Depends(require_owner),
                  db: Session = Depends(get_db)):
    rows = _inactivos_out(db, usuario.tenant_id, dias)
    return csv_response(
        f"inactivos_{dias}d.csv",
        ["cliente_id", "nombre", "telefono", "ult_actividad", "dias_inactivo", "saldo"],
        ([r.cliente_id, r.nombre, r.telefono, r.ult_actividad.isoformat(),
          r.dias_inactivo, r.saldo] for r in rows),
    )
