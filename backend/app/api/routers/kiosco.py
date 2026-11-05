"""Kiosco público: registro de clientes + ruleta.

Autenticación: device_token opaco de la pantalla (no hay login de usuario).
La pantalla debe estar habilitada por PIN (flujo 9.2) — regla implícita:
kiosco inoperativo si pantalla/sucursal/tenant están suspendidos o la
habilitación venció.
"""

import random
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.models import (
    Cliente,
    ConfigPin,
    EstadoCliente,
    EstadoPantalla,
    EstadoSucursal,
    EstadoTenant,
    EstadoUsuario,
    ModoPin,
    MovimientoPuntos,
    Pantalla,
    RolUsuario,
    RuletaSegmento,
    Sucursal,
    Tenant,
    TipoMovimiento,
    Usuario,
)
from app.schemas.kiosco import (
    GirarIn,
    GirarOut,
    KioscoConfigOut,
    RegistroKioscoIn,
    RegistroKioscoOut,
    SegmentoPublico,
)
from app.services.campanas import generar_codigo_referido, multiplicador_activo
from app.services.planes import verificar_limite, verificar_ruleta
from app.services.puntos import otorgar, registrar_movimiento
from app.services.push import push_async
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter()

MAX_GIROS_DIA = 1  # por cliente y pantalla


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _contexto(db: Session, device_token: str) -> tuple[Pantalla, Sucursal, Tenant]:
    """Valida la cadena pantalla → sucursal → tenant. Devuelve 404/403 con detalle."""
    pantalla = db.scalar(select(Pantalla).where(Pantalla.device_token == device_token))
    if not pantalla:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pantalla no encontrada")
    if pantalla.estado == EstadoPantalla.bloqueada:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Pantalla bloqueada")
    if not pantalla.habilitada_hasta or _aware(pantalla.habilitada_hasta) <= datetime.now(timezone.utc):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Pantalla no habilitada: el cajero debe ingresar el PIN de caja",
        )
    sucursal = db.get(Sucursal, pantalla.sucursal_id)
    if not sucursal or sucursal.estado != EstadoSucursal.activa:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La sucursal está suspendida")
    tenant = db.get(Tenant, sucursal.tenant_id)
    if not tenant or tenant.estado != EstadoTenant.activo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El comercio está suspendido")
    return pantalla, sucursal, tenant


@router.get("/{device_token}/pin-info")
def pin_info(device_token: str, db: Session = Depends(get_db)):
    """Info mínima para la pantalla de desbloqueo por PIN (antes de habilitar).
    No requiere que la pantalla esté habilitada."""
    pantalla = db.scalar(select(Pantalla).where(Pantalla.device_token == device_token))
    if not pantalla:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pantalla no encontrada")
    sucursal = db.get(Sucursal, pantalla.sucursal_id)
    tenant = db.get(Tenant, sucursal.tenant_id) if sucursal else None
    config = db.get(ConfigPin, tenant.id) if tenant else None
    modo = config.modo if config else ModoPin.por_sucursal
    cajeros = []
    if modo == ModoPin.por_cajero and tenant:
        cajeros = db.scalars(
            select(Usuario).where(
                Usuario.tenant_id == tenant.id, Usuario.rol == RolUsuario.cajero,
                Usuario.estado == EstadoUsuario.activo,
            ).order_by(Usuario.nombre)
        ).all()
    return {
        "comercio": tenant.nombre_comercial if tenant else "",
        "sucursal": sucursal.nombre if sucursal else "",
        "pantalla": pantalla.nombre,
        "modo_pin": modo.value,
        "cajeros": [{"id": c.id, "nombre": c.nombre} for c in cajeros],
        "estado": pantalla.estado.value,
    }


@router.get("/{device_token}/config", response_model=KioscoConfigOut)
def config(device_token: str, db: Session = Depends(get_db)):
    pantalla, sucursal, tenant = _contexto(db, device_token)
    segmentos = db.scalars(
        select(RuletaSegmento).where(
            RuletaSegmento.tenant_id == tenant.id, RuletaSegmento.activo == True  # noqa: E712
        ).order_by(RuletaSegmento.id)
    ).all()
    return KioscoConfigOut(
        comercio=tenant.nombre_comercial, logo_url=tenant.logo_url,
        sucursal=sucursal.nombre, pantalla=pantalla.nombre,
        habilitada_hasta=pantalla.habilitada_hasta,
        puntos_registro=tenant.puntos_registro,
        segmentos=[SegmentoPublico(etiqueta=s.etiqueta, puntos=s.puntos,
                                 peso=s.peso, color=s.color) for s in segmentos],
    )


@router.post("/{device_token}/registro", response_model=RegistroKioscoOut,
             status_code=status.HTTP_201_CREATED)
def registro(device_token: str, data: RegistroKioscoIn, db: Session = Depends(get_db)):
    pantalla, sucursal, tenant = _contexto(db, device_token)

    existente = db.scalar(select(Cliente).where(Cliente.ci == data.ci))
    if existente:
        return RegistroKioscoOut(
            cliente_id=existente.id, nombre=existente.nombre,
            nuevo=False, puntos_otorgados=0, saldo=existente.saldo_puntos,
        )

    if db.scalar(select(Cliente).where(Cliente.telefono == data.telefono)):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El teléfono ya está registrado con otra cédula. Acércate a caja.",
        )

    if not data.acepto_terminos:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Debes aceptar los términos y la política de privacidad para registrarte.",
        )

    verificar_limite(db, tenant, "clientes")

    # Referido: código opcional de un cliente existente → bonus al que refirió
    referidor = None
    if data.codigo_referido:
        referidor = db.scalar(
            select(Cliente).where(
                Cliente.codigo_referido == data.codigo_referido.strip().upper(),
                Cliente.estado == EstadoCliente.activo,
            )
        )

    mult, campana = multiplicador_activo(db, tenant.id, sucursal.id)

    cliente = Cliente(
        nombre=data.nombre, ci=data.ci, telefono=data.telefono,
        tenant_registro_id=tenant.id,
        codigo_referido=generar_codigo_referido(db),
        referido_por_id=referidor.id if referidor else None,
    )
    db.add(cliente)
    db.flush()

    puntos = tenant.puntos_registro * mult
    cliente.saldo_puntos = puntos
    registrar_movimiento(
        db, cliente_id=cliente.id, puntos=puntos, tipo=TipoMovimiento.registro,
        tenant_id=tenant.id, sucursal_id=sucursal.id,
        detalle={"origen": "kiosco", "pantalla_id": pantalla.id,
                 "consentido_terminos": True,
                 **({"campana_id": campana.id, "multiplicador": mult} if campana else {})},
    )

    if referidor:
        otorgar(
            db, referidor, tenant.puntos_referido, TipoMovimiento.referido,
            tenant_id=tenant.id, sucursal_id=sucursal.id,
            detalle={"referido_cliente_id": cliente.id},
        )

    db.commit()
    if referidor:
        push_async(referidor.id, f"+{tenant.puntos_referido} pts por tu referido",
                   f"{cliente.nombre} se registró con tu código", "/billetera")
    return RegistroKioscoOut(
        cliente_id=cliente.id, nombre=cliente.nombre, nuevo=True,
        puntos_otorgados=puntos, saldo=cliente.saldo_puntos,
        multiplicador=mult, campana=campana.nombre if campana else None,
        referido_bonus=tenant.puntos_referido if referidor else 0,
    )


@router.post("/{device_token}/ruleta/girar", response_model=GirarOut)
def girar(device_token: str, data: GirarIn, db: Session = Depends(get_db)):
    pantalla, sucursal, tenant = _contexto(db, device_token)
    verificar_ruleta(db, tenant)

    cliente = db.get(Cliente, data.cliente_id)
    if not cliente or cliente.estado != EstadoCliente.activo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")

    # Anti-abuso: un giro por cliente por pantalla por día
    giros_hoy = db.scalar(
        select(func.count(MovimientoPuntos.id)).where(
            MovimientoPuntos.cliente_id == cliente.id,
            MovimientoPuntos.tipo == TipoMovimiento.ruleta,
            MovimientoPuntos.sucursal_id == sucursal.id,
            MovimientoPuntos.created_at >= datetime.now(timezone.utc) - timedelta(hours=24),
        )
    ) or 0
    if giros_hoy >= MAX_GIROS_DIA:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Ya giraste la ruleta hoy en este local. ¡Vuelve mañana!",
        )

    segmentos = db.scalars(
        select(RuletaSegmento).where(
            RuletaSegmento.tenant_id == tenant.id, RuletaSegmento.activo == True  # noqa: E712
        )
    ).all()
    if not segmentos:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La ruleta no tiene segmentos activos")

    elegido = random.choices(segmentos, weights=[s.peso for s in segmentos], k=1)[0]
    indice = segmentos.index(elegido)
    mult, campana = multiplicador_activo(db, tenant.id, sucursal.id)
    puntos = elegido.puntos * mult
    # Toda interacción queda en el ledger (monitor global), incluso con 0 puntos
    cliente.saldo_puntos += puntos
    registrar_movimiento(
        db, cliente_id=cliente.id, puntos=puntos, tipo=TipoMovimiento.ruleta,
        tenant_id=tenant.id, sucursal_id=sucursal.id,
        detalle={"segmento_id": elegido.id, "pantalla_id": pantalla.id,
                 **({"campana_id": campana.id, "multiplicador": mult} if campana else {})},
    )
    db.commit()
    if puntos > 0:
        push_async(cliente.id, f"+{puntos} pts en la ruleta",
                   f"Ganaste en {tenant.nombre_comercial}", "/billetera")
    return GirarOut(
        etiqueta=elegido.etiqueta, puntos=puntos,
        color=elegido.color, saldo=cliente.saldo_puntos, indice=indice,
        multiplicador=mult, campana=campana.nombre if campana else None,
    )
