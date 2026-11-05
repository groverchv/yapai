"""Terminal de Caja: canje de pases + bonus manual (reglas #9, #11).

Acceso: require_caja (owner o cajero). El cajero solo opera en sucursales
asignadas (si tiene asignaciones); el owner en cualquiera del tenant.
"""

from datetime import datetime, timedelta, timezone

from app.core.deps import require_caja
from app.db.session import get_db
from app.models import (
    Cliente,
    ConfigPin,
    EmpleadoSucursal,
    EstadoCliente,
    EstadoSucursal,
    ModoPin,
    MovimientoPuntos,
    PaseDigital,
    Premio,
    RolUsuario,
    Sucursal,
    Tenant,
    TipoMovimiento,
    Usuario,
)
from app.schemas.caja import (
    BonusIn,
    BonusOut,
    CanjearIn,
    CanjearOut,
    ClienteBusquedaOut,
    ContextoCajaOut,
    PasePreviewOut,
    SucursalOpcion,
)
from app.services.puntos import canjear_pase, expirar_si_corresponde, otorgar
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_caja)])


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _sucursales_cajero(db: Session, usuario: Usuario) -> list[Sucursal]:
    """Sucursales operables: asignadas al cajero o todas las activas del tenant."""
    base = select(Sucursal).where(
        Sucursal.tenant_id == usuario.tenant_id, Sucursal.estado == EstadoSucursal.activa
    )
    if usuario.rol == RolUsuario.cajero:
        asignadas = db.scalars(
            select(EmpleadoSucursal.sucursal_id).where(
                EmpleadoSucursal.usuario_id == usuario.id
            )
        ).all()
        if asignadas:
            base = base.where(Sucursal.id.in_(asignadas))
    return db.scalars(base.order_by(Sucursal.nombre)).all()


def _validar_sucursal(db: Session, usuario: Usuario, sucursal_id: int) -> Sucursal:
    validas = {s.id for s in _sucursales_cajero(db, usuario)}
    s = db.get(Sucursal, sucursal_id)
    if not s or s.id not in validas:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sucursal no válida para este usuario")
    return s


def _bonus_hoy(db: Session, usuario: Usuario) -> int:
    return db.scalar(
        select(func.coalesce(func.sum(MovimientoPuntos.puntos), 0)).where(
            MovimientoPuntos.tipo == TipoMovimiento.bonus_manual,
            MovimientoPuntos.ejecutado_por == usuario.id,
            MovimientoPuntos.created_at >= datetime.now(timezone.utc) - timedelta(hours=24),
        )
    ) or 0


@router.get("/contexto", response_model=ContextoCajaOut)
def contexto(usuario: Usuario = Depends(require_caja), db: Session = Depends(get_db)):
    tenant = db.get(Tenant, usuario.tenant_id)
    config = db.get(ConfigPin, usuario.tenant_id)
    return ContextoCajaOut(
        cajero_id=usuario.id, cajero_nombre=usuario.nombre, rol=usuario.rol.value,
        sucursales=[SucursalOpcion(id=s.id, nombre=s.nombre)
                    for s in _sucursales_cajero(db, usuario)],
        modo_pin=config.modo.value if config else ModoPin.por_sucursal.value,
        max_puntos_tx=tenant.max_puntos_tx if tenant else 0,
        max_puntos_dia_cajero=tenant.max_puntos_dia_cajero if tenant else 0,
        bonus_hoy=_bonus_hoy(db, usuario),
    )


def _buscar_pase(db: Session, tenant_id: int, codigo: str) -> PaseDigital:
    pase = db.scalar(
        select(PaseDigital).where(
            PaseDigital.tenant_id == tenant_id,
            (PaseDigital.codigo_qr == codigo) | (PaseDigital.pin_corto == codigo.upper()),
        )
    )
    if not pase:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pase no encontrado en este comercio")
    return pase


def _preview(db: Session, pase: PaseDigital) -> PasePreviewOut:
    cliente = db.get(Cliente, pase.cliente_id)
    premio = db.get(Premio, pase.premio_id)
    tenant = db.get(Tenant, pase.tenant_id)
    estado = "expirado" if expirar_si_corresponde(pase) else pase.estado.value
    return PasePreviewOut(
        pase_id=pase.id, estado=estado,
        cliente_nombre=cliente.nombre if cliente else "—",
        cliente_ci=cliente.ci if cliente else "—",
        premio_nombre=premio.nombre if premio else "—",
        puntos=pase.puntos, comercio=tenant.nombre_comercial if tenant else "",
        expira_en=pase.expira_en,
    )


@router.get("/pases/{codigo}", response_model=PasePreviewOut)
def preview_pase(codigo: str, usuario: Usuario = Depends(require_caja),
                 db: Session = Depends(get_db)):
    """Preview del pase por código QR o PIN corto (motor de canje)."""
    return _preview(db, _buscar_pase(db, usuario.tenant_id, codigo.strip()))


@router.post("/pases/{codigo}/canjear", response_model=CanjearOut)
def canjear(codigo: str, data: CanjearIn, usuario: Usuario = Depends(require_caja),
            db: Session = Depends(get_db)):
    """Regla #9-10: TX atómica — débito + stock-1 + auditoría del cajero."""
    sucursal = _validar_sucursal(db, usuario, data.sucursal_id)
    pase = _buscar_pase(db, usuario.tenant_id, codigo.strip())
    canjear_pase(db, pase, usuario.id, sucursal.id)
    db.commit()

    cliente = db.get(Cliente, pase.cliente_id)
    premio = db.get(Premio, pase.premio_id)
    return CanjearOut(
        detail="Canje realizado",
        pase_id=pase.id,
        cliente_nombre=cliente.nombre if cliente else "—",
        premio_nombre=premio.nombre if premio else "—",
        puntos=pase.puntos,
        saldo_cliente=cliente.saldo_puntos if cliente else 0,
        stock_restante=premio.stock if premio and premio.stock_limitado else None,
    )


@router.get("/clientes/buscar", response_model=list[ClienteBusquedaOut])
def buscar_clientes(q: str, usuario: Usuario = Depends(require_caja),
                    db: Session = Depends(get_db)):
    """Búsqueda por CI o teléfono para el bonus manual."""
    like = f"%{q.strip()}%"
    rows = db.scalars(
        select(Cliente).where(
            Cliente.estado == EstadoCliente.activo,
            (Cliente.ci.ilike(like)) | (Cliente.telefono.ilike(like)),
        ).order_by(Cliente.nombre).limit(10)
    ).all()
    return [
        ClienteBusquedaOut(id=c.id, nombre=c.nombre, ci=c.ci,
                         telefono=c.telefono, saldo_puntos=c.saldo_puntos)
        for c in rows
    ]


@router.post("/bonus", response_model=BonusOut)
def otorgar_bonus(data: BonusIn, usuario: Usuario = Depends(require_caja),
                  db: Session = Depends(get_db)):
    """Regla #11: límites por transacción y por día por cajero."""
    tenant = db.get(Tenant, usuario.tenant_id)
    sucursal = _validar_sucursal(db, usuario, data.sucursal_id)

    if data.puntos > (tenant.max_puntos_tx or 0):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Supera el máximo por transacción ({tenant.max_puntos_tx} pts)",
        )
    bonus_hoy = _bonus_hoy(db, usuario)
    if bonus_hoy + data.puntos > (tenant.max_puntos_dia_cajero or 0):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Supera tu límite diario de bonus ({tenant.max_puntos_dia_cajero} pts; "
            f"llevas {bonus_hoy})",
        )

    cliente = db.get(Cliente, data.cliente_id)
    if not cliente or cliente.estado != EstadoCliente.activo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")

    otorgar(
        db, cliente, data.puntos, TipoMovimiento.bonus_manual,
        tenant_id=tenant.id, sucursal_id=sucursal.id,
        ejecutado_por=usuario.id, detalle={"motivo": data.motivo},
    )
    db.commit()
    return BonusOut(
        detail=f"+{data.puntos} pts otorgados a {cliente.nombre}",
        puntos=data.puntos, saldo_cliente=cliente.saldo_puntos,
        bonus_hoy=bonus_hoy + data.puntos, limite_dia=tenant.max_puntos_dia_cajero,
    )
