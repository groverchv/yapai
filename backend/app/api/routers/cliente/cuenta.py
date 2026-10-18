from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_cliente
from app.db.session import get_db
from app.models import (
    Cliente, EstadoCliente, EstadoPase, MovimientoPuntos, PaseDigital,
    Premio, Sucursal, SujetoTipo, Tenant, TipoMovimiento, Usuario,
)
from app.schemas.admin import Pagina
from app.schemas.auth import MessageResponse
from app.schemas.cliente import (
    ClienteUpdate, MovimientoClienteOut, PerfilClienteOut, WalletOut,
)
from app.schemas.socio import FirmaUploadOut
from app.services.auth import revocar_todos_refresh
from app.services.puntos import (
    cancelar_pase, registrar_movimiento, saldo_disponible,
)
from app.services.uploads import firma_disponible, generar_firma

router = APIRouter(dependencies=[Depends(get_current_cliente)])


@router.get("/me", response_model=PerfilClienteOut)
def mi_perfil(cliente: Cliente = Depends(get_current_cliente)):
    return PerfilClienteOut.model_validate(cliente)


@router.post("/uploads/firma", response_model=FirmaUploadOut)
def firma_foto(cliente: Cliente = Depends(get_current_cliente)):
    """Firma para subir la foto de perfil directo a Cloudinary."""
    if not firma_disponible():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Almacenamiento de imágenes no configurado",
        )
    return FirmaUploadOut(**generar_firma(None, f"clientes/{cliente.id}"))


@router.patch("/me", response_model=PerfilClienteOut)
def actualizar_perfil(data: ClienteUpdate, cliente: Cliente = Depends(get_current_cliente),
                      db: Session = Depends(get_db)):
    cambios = data.model_dump(exclude_unset=True)
    if "telefono" in cambios and cambios["telefono"] != cliente.telefono:
        existe = db.scalar(select(Cliente).where(Cliente.telefono == cambios["telefono"]))
        if existe:
            raise HTTPException(status.HTTP_409_CONFLICT, "El teléfono ya está registrado")
    for campo, valor in cambios.items():
        setattr(cliente, campo, valor)
    db.commit()
    return PerfilClienteOut.model_validate(cliente)


@router.delete("/me", response_model=MessageResponse)
def eliminar_cuenta(cliente: Cliente = Depends(get_current_cliente), db: Session = Depends(get_db)):
    """Regla #15: baja lógica con pérdida de puntos. Los pases activos se cancelan."""
    pases_activos = db.scalars(
        select(PaseDigital).where(
            PaseDigital.cliente_id == cliente.id, PaseDigital.estado == EstadoPase.activo
        )
    ).all()
    for pase in pases_activos:
        cancelar_pase(db, cliente, pase)

    if cliente.saldo_puntos > 0:
        registrar_movimiento(
            db, cliente_id=cliente.id, puntos=-cliente.saldo_puntos,
            tipo=TipoMovimiento.anulacion, detalle={"motivo": "eliminacion_cuenta"},
        )
    cliente.saldo_puntos = 0
    cliente.puntos_congelados = 0
    cliente.estado = EstadoCliente.eliminado
    cliente.eliminado_en = datetime.now(timezone.utc)
    revocar_todos_refresh(db, SujetoTipo.cliente, cliente.id)
    db.commit()
    return MessageResponse(detail="Cuenta eliminada. Tus puntos fueron anulados.")


@router.get("/wallet", response_model=WalletOut)
def wallet(cliente: Cliente = Depends(get_current_cliente)):
    return WalletOut(
        saldo=cliente.saldo_puntos,
        congelado=cliente.puntos_congelados,
        disponible=saldo_disponible(cliente),
    )


@router.get("/movimientos", response_model=Pagina[MovimientoClienteOut])
def movimientos(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                cliente: Cliente = Depends(get_current_cliente), db: Session = Depends(get_db)):
    filtros = [MovimientoPuntos.cliente_id == cliente.id]
    total = db.scalar(select(func.count(MovimientoPuntos.id)).where(*filtros)) or 0
    rows = db.execute(
        select(MovimientoPuntos, Tenant.nombre_comercial, Sucursal.nombre, Premio.nombre)
        .join(Tenant, MovimientoPuntos.tenant_id == Tenant.id, isouter=True)
        .join(Sucursal, MovimientoPuntos.sucursal_id == Sucursal.id, isouter=True)
        .join(Premio, MovimientoPuntos.premio_id == Premio.id, isouter=True)
        .where(*filtros)
        .order_by(MovimientoPuntos.id.desc())
        .offset((page - 1) * size).limit(size)
    ).all()
    return Pagina(
        items=[MovimientoClienteOut(
            id=m.id, created_at=m.created_at, tipo=m.tipo.value, puntos=m.puntos,
            comercio=comercio, sucursal=sucursal, premio=premio, detalle=m.detalle,
        ) for m, comercio, sucursal, premio in rows],
        total=total, page=page, size=size,
    )
