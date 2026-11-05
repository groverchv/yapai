from datetime import datetime, timezone

from app.core.deps import get_current_cliente
from app.core.security import utcnow
from app.db.session import get_db
from app.models import (
    Cliente,
    EstadoCliente,
    EstadoPase,
    EstadoPremio,
    EstadoTenant,
    MovimientoPuntos,
    PaseDigital,
    Premio,
    Sucursal,
    SujetoTipo,
    Tenant,
    TipoMovimiento,
)
from app.schemas.admin import Pagina
from app.schemas.auth import MessageResponse
from app.schemas.cliente import (
    ClienteUpdate,
    MovimientoClienteOut,
    PerfilClienteOut,
    ProximoPremioOut,
    WalletOut,
)
from app.schemas.socio import FirmaUploadOut
from app.services.auth import revocar_todos_refresh
from app.services.puntos import (
    TIPOS_GANANCIA,
    cancelar_pase,
    registrar_movimiento,
    saldo_disponible,
)
from app.services.uploads import firma_disponible, generar_firma
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

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


@router.get("/proximo-premio", response_model=ProximoPremioOut)
def proximo_premio(cliente: Cliente = Depends(get_current_cliente),
                  db: Session = Depends(get_db)):
    """La meta de puntos más cercana del cliente.

    Prioriza el premio más barato no alcanzable en el comercio donde más puntos
    ganó; sin actividad previa, usa el catálogo global. Si ya le alcanza para
    algo, devuelve el premio más caro que puede pagar (alcanzable=true).
    """
    disponible = saldo_disponible(cliente)
    ahora = utcnow()
    filtros = [
        Premio.estado == EstadoPremio.activo,
        Tenant.estado == EstadoTenant.activo,
        or_(Premio.vigencia_hasta.is_(None), Premio.vigencia_hasta > ahora),
    ]
    tenant_ids = [
        tid for (tid, _pts) in db.execute(
            select(MovimientoPuntos.tenant_id, func.sum(MovimientoPuntos.puntos))
            .where(MovimientoPuntos.cliente_id == cliente.id,
                   MovimientoPuntos.tenant_id.is_not(None),
                   MovimientoPuntos.tipo.in_(TIPOS_GANANCIA))
            .group_by(MovimientoPuntos.tenant_id)
            .order_by(func.sum(MovimientoPuntos.puntos).desc())
        ).all()
    ]

    def _candidato(*, inalcanzable: bool, tids: list[int] | None):
        cond = (Premio.costo_puntos > disponible if inalcanzable
                else Premio.costo_puntos <= disponible)
        q = (select(Premio, Tenant)
             .join(Tenant, Tenant.id == Premio.tenant_id)
             .where(*filtros, cond))
        if tids:
            q = q.where(Premio.tenant_id.in_(tids))
        return db.execute(
            q.order_by(Premio.costo_puntos.asc() if inalcanzable
                       else Premio.costo_puntos.desc())
            .limit(1)).first()

    row = None
    if tenant_ids:
        row = (_candidato(inalcanzable=True, tids=tenant_ids)
               or _candidato(inalcanzable=False, tids=tenant_ids))
    if row is None:
        row = (_candidato(inalcanzable=True, tids=None)
               or _candidato(inalcanzable=False, tids=None))
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            "Aún no hay premios disponibles")
    p, t = row
    return ProximoPremioOut(
        premio_id=p.id, tenant_id=t.id, nombre=p.nombre,
        imagen_url=p.imagen_url,
        costo_puntos=p.costo_puntos, comercio=t.nombre_comercial,
        logo_url=t.logo_url, saldo=disponible,
        faltante=max(0, p.costo_puntos - disponible),
        alcanzable=p.costo_puntos <= disponible,
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
