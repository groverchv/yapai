"""Motor de puntos: ledger append-only + caches en cliente.

Reglas que garantiza:
- #7  Congelar saldo al generar un pase (en la misma TX)
- #8  Doble gasto imposible: disponible = saldo - congelado
- #9  Canje atómico (pase canjeado + movimiento + stock-1 + cajero)
- #10 Stock 0 → premio 'agotado'
- #15 Baja lógica de cliente con movimiento 'anulacion'
"""

import secrets
import string
from datetime import timedelta

from app.core.security import utcnow
from app.models import (
    Cliente,
    EstadoPase,
    EstadoPremio,
    EstadoTenant,
    MovimientoPuntos,
    PaseDigital,
    Premio,
    Tenant,
    TipoMovimiento,
)
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

PASE_TTL_HOURS = 24
_ALFABETO_PIN = "".join(c for c in string.ascii_uppercase + string.digits
                        if c not in "O0I1")  # sin caracteres ambiguos

# Tipos que otorgan puntos al cliente (congelar/liberar son bookkeeping interno;
# sumar 'compra' aquí cuando se implemente Fase 15)
TIPOS_GANANCIA = (
    TipoMovimiento.registro,
    TipoMovimiento.ruleta,
    TipoMovimiento.bonus_manual,
    TipoMovimiento.referido,
)


def saldo_disponible(cliente: Cliente) -> int:
    return cliente.saldo_puntos - cliente.puntos_congelados


def registrar_movimiento(
    db: Session, *, cliente_id: int, puntos: int, tipo: TipoMovimiento,
    tenant_id: int | None = None, sucursal_id: int | None = None,
    pase_id: int | None = None, premio_id: int | None = None,
    ejecutado_por: int | None = None, detalle: dict | None = None,
) -> MovimientoPuntos:
    mov = MovimientoPuntos(
        cliente_id=cliente_id, puntos=puntos, tipo=tipo, tenant_id=tenant_id,
        sucursal_id=sucursal_id, pase_id=pase_id, premio_id=premio_id,
        ejecutado_por=ejecutado_por, detalle=detalle,
    )
    db.add(mov)
    return mov


def otorgar(db: Session, cliente: Cliente, puntos: int, tipo: TipoMovimiento, **kw) -> MovimientoPuntos:
    """Suma puntos al saldo y registra el movimiento."""
    cliente.saldo_puntos += puntos
    return registrar_movimiento(db, cliente_id=cliente.id, puntos=puntos, tipo=tipo, **kw)


def _generar_pin_corto(db: Session) -> str:
    for _ in range(20):
        pin = "".join(secrets.choice(_ALFABETO_PIN) for _ in range(6))
        if not db.scalar(select(PaseDigital.id).where(PaseDigital.pin_corto == pin)):
            return pin
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "No se pudo generar el PIN del pase")


def generar_pase(db: Session, cliente: Cliente, premio: Premio) -> PaseDigital:
    """Regla #7-8: congela los puntos en la misma TX que crea el pase."""
    tenant = db.get(Tenant, premio.tenant_id)
    if not tenant or tenant.estado != EstadoTenant.activo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El comercio no está disponible")
    if premio.estado == EstadoPremio.agotado:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este premio está agotado")
    if premio.estado != EstadoPremio.activo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este premio no está disponible")
    if premio.stock_limitado and (premio.stock or 0) <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este premio está agotado")
    if premio.vigencia_hasta and _aware(premio.vigencia_hasta) <= utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta promoción ya venció")
    if saldo_disponible(cliente) < premio.costo_puntos:
        raise HTTPException(status.HTTP_409_CONFLICT, "Puntos insuficientes")

    pase = PaseDigital(
        cliente_id=cliente.id, premio_id=premio.id, tenant_id=premio.tenant_id,
        pin_corto=_generar_pin_corto(db), puntos=premio.costo_puntos,
        expira_en=utcnow() + timedelta(hours=PASE_TTL_HOURS),
    )
    db.add(pase)
    db.flush()

    cliente.puntos_congelados += premio.costo_puntos
    registrar_movimiento(
        db, cliente_id=cliente.id, puntos=premio.costo_puntos,
        tipo=TipoMovimiento.congelar, tenant_id=premio.tenant_id,
        pase_id=pase.id, premio_id=premio.id,
    )
    return pase


def _aware(dt):
    return dt if dt is None or dt.tzinfo is not None else dt.replace(tzinfo=utcnow().tzinfo)


def expirar_si_corresponde(pase: PaseDigital) -> bool:
    return pase.estado == EstadoPase.activo and pase.expira_en is not None and _aware(pase.expira_en) <= utcnow()


def _liberar(db: Session, cliente: Cliente, pase: PaseDigital, estado_final: EstadoPase) -> None:
    pase.estado = estado_final
    cliente.puntos_congelados = max(0, cliente.puntos_congelados - pase.puntos)
    registrar_movimiento(
        db, cliente_id=cliente.id, puntos=pase.puntos, tipo=TipoMovimiento.liberar,
        tenant_id=pase.tenant_id, pase_id=pase.id, premio_id=pase.premio_id,
    )


def cancelar_pase(db: Session, cliente: Cliente, pase: PaseDigital) -> None:
    """Cancelación manual por el cliente: libera los puntos de inmediato.
    Si el pase ya expiró, igual libera el saldo congelado (queda 'expirado')."""
    if pase.estado != EstadoPase.activo:
        raise HTTPException(status.HTTP_409_CONFLICT, "El pase no está activo")
    estado = EstadoPase.expirado if expirar_si_corresponde(pase) else EstadoPase.cancelado
    _liberar(db, cliente, pase, estado)


def expirar_pases_vencidos(db: Session) -> int:
    """Job periódico: libera el saldo congelado de todos los pases vencidos.
    Devuelve la cantidad de pases expirados."""
    vencidos = db.scalars(
        select(PaseDigital).where(
            PaseDigital.estado == EstadoPase.activo,
            PaseDigital.expira_en.is_not(None),
            PaseDigital.expira_en <= utcnow(),
        )
    ).all()
    for pase in vencidos:
        _liberar(db, db.get(Cliente, pase.cliente_id), pase, EstadoPase.expirado)
    if vencidos:
        db.commit()
    return len(vencidos)


def canjear_pase(db: Session, pase: PaseDigital, cajero_id: int, sucursal_id: int) -> None:
    """Regla #9-10: canje atómico — débito real, stock-1, auditoría del cajero."""
    if pase.estado != EstadoPase.activo:
        raise HTTPException(status.HTTP_409_CONFLICT, "El pase no está activo")
    if expirar_si_corresponde(pase):
        _liberar(db, db.get(Cliente, pase.cliente_id), pase, EstadoPase.expirado)
        db.flush()
        raise HTTPException(status.HTTP_409_CONFLICT, "El pase expiró; los puntos fueron liberados")

    cliente = db.get(Cliente, pase.cliente_id)
    premio = db.get(Premio, pase.premio_id)
    if not cliente or not premio:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Datos del pase no encontrados")

    # Débito real: sale del congelado y del saldo
    cliente.puntos_congelados = max(0, cliente.puntos_congelados - pase.puntos)
    cliente.saldo_puntos = max(0, cliente.saldo_puntos - pase.puntos)

    if premio.stock_limitado:
        premio.stock = (premio.stock or 0) - 1
        if premio.stock <= 0:
            premio.stock = 0
            premio.estado = EstadoPremio.agotado

    pase.estado = EstadoPase.canjeado
    pase.canjeado_en = utcnow()
    pase.canjeado_por = cajero_id
    pase.sucursal_canje_id = sucursal_id

    registrar_movimiento(
        db, cliente_id=cliente.id, puntos=-pase.puntos, tipo=TipoMovimiento.canje,
        tenant_id=pase.tenant_id, sucursal_id=sucursal_id, pase_id=pase.id,
        premio_id=pase.premio_id, ejecutado_por=cajero_id,
    )
