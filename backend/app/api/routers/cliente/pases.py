from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_cliente
from app.db.session import get_db
from app.models import Cliente, EstadoPase, PaseDigital, Premio, Tenant
from app.schemas.cliente import PaseCreateIn, PaseOut
from app.services.puntos import cancelar_pase, expirar_si_corresponde, generar_pase

router = APIRouter(dependencies=[Depends(get_current_cliente)])


def _out(db: Session, p: PaseDigital) -> PaseOut:
    premio = db.get(Premio, p.premio_id)
    tenant = db.get(Tenant, p.tenant_id)
    estado = "expirado" if expirar_si_corresponde(p) else p.estado.value
    return PaseOut(
        id=p.id, codigo_qr=p.codigo_qr, pin_corto=p.pin_corto, puntos=p.puntos,
        estado=estado, expira_en=p.expira_en,
        premio_nombre=premio.nombre if premio else "",
        comercio=tenant.nombre_comercial if tenant else "",
        created_at=p.created_at,
    )


@router.post("/pases", response_model=PaseOut, status_code=status.HTTP_201_CREATED)
def crear_pase(data: PaseCreateIn, cliente: Cliente = Depends(get_current_cliente),
               db: Session = Depends(get_db)):
    premio = db.get(Premio, data.premio_id)
    if not premio:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Premio no encontrado")
    pase = generar_pase(db, cliente, premio)
    db.commit()
    return _out(db, pase)


@router.get("/pases", response_model=list[PaseOut])
def mis_pases(estado: str | None = None, cliente: Cliente = Depends(get_current_cliente),
              db: Session = Depends(get_db)):
    stmt = (
        select(PaseDigital).where(PaseDigital.cliente_id == cliente.id)
        .order_by(PaseDigital.id.desc())
    )
    pases = db.scalars(stmt).all()
    out = [_out(db, p) for p in pases]
    if estado:
        out = [p for p in out if p.estado == estado]
    return out


@router.post("/pases/{pase_id}/cancelar", response_model=PaseOut)
def cancelar(pase_id: int, cliente: Cliente = Depends(get_current_cliente),
             db: Session = Depends(get_db)):
    pase = db.scalar(
        select(PaseDigital).where(
            PaseDigital.id == pase_id, PaseDigital.cliente_id == cliente.id
        )
    )
    if not pase:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pase no encontrado")
    cancelar_pase(db, cliente, pase)
    db.commit()
    return _out(db, pase)
