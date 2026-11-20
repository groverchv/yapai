"""Cuenta del socio: exportación de datos (portabilidad) y baja voluntaria.

- GET  /socio/cuenta/exportar → JSON con todos los datos del tenant.
- POST /socio/cuenta/baja     → solicita la baja: suspende el tenant, revoca
  sesiones y programa la purga a BAJA_RETENCION_DIAS (job limpieza).
"""
from app.core.config import settings
from app.core.deps import get_current_usuario, require_owner
from app.core.security import utcnow, verify_secret
from app.db.session import get_db
from app.models import (
    Campana,
    Cliente,
    Comunicado,
    EstadoTenant,
    FacturaPlan,
    MovimientoPuntos,
    Pantalla,
    Premio,
    Sucursal,
    SujetoTipo,
    Tenant,
    Usuario,
)
from app.schemas.auth import MessageResponse
from app.services.audit import registrar_audit
from app.services.auth import revocar_todos_refresh
from app.services.email import email_service, emails_owner
from app.services.tenants import suspender_tenant
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_owner)])

BAJA_RETENCION_DIAS = settings.BAJA_RETENCION_DIAS


class BajaIn(BaseModel):
    password: str


@router.get("/exportar")
def exportar_datos(usuario: Usuario = Depends(require_owner),
                   db: Session = Depends(get_db)):
    """Portabilidad: volcado JSON de todos los datos del tenant."""
    tid = usuario.tenant_id
    tenant = db.get(Tenant, tid)
    # Clientes del tenant = registrados ahí O con movimientos en él
    # (los clientes son globales — no hay cliente.tenant_id).
    ids_cliente = select(Cliente.id).where(
        Cliente.tenant_registro_id == tid
    ).union(
        select(MovimientoPuntos.cliente_id).where(MovimientoPuntos.tenant_id == tid)
    )
    clientes = db.scalars(select(Cliente).where(Cliente.id.in_(ids_cliente))).all()
    movs = db.scalars(
        select(MovimientoPuntos).where(MovimientoPuntos.tenant_id == tid)
        .order_by(MovimientoPuntos.id)
    ).all()
    return {
        "tenant": {
            "nombre_comercial": tenant.nombre_comercial,
            "razon_social": tenant.razon_social, "nit_rut": tenant.nit_rut,
            "email_contacto": tenant.email_contacto, "telefono": tenant.telefono,
            "estado": tenant.estado.value, "created_at": str(tenant.created_at),
        },
        "usuarios": [
            {"nombre": u.nombre, "email": u.email, "rol": u.rol.value}
            for u in db.scalars(
                select(Usuario).where(Usuario.tenant_id == tid)).all()
        ],
        "sucursales": [
            {"nombre": s.nombre, "direccion": s.direccion}
            for s in db.scalars(
                select(Sucursal).where(Sucursal.tenant_id == tid)).all()
        ],
        "pantallas": [
            {"nombre": p.nombre, "estado": p.estado.value}
            for p in db.scalars(select(Pantalla).join(
                Sucursal, Pantalla.sucursal_id == Sucursal.id
            ).where(Sucursal.tenant_id == tid)).all()
        ],
        "premios": [
            {"nombre": p.nombre, "costo_puntos": p.costo_puntos,
             "estado": p.estado.value}
            for p in db.scalars(
                select(Premio).where(Premio.tenant_id == tid)).all()
        ],
        "campanas": [
            {"nombre": c.nombre, "multiplicador": c.multiplicador,
             "activa": c.activa, "inicio": str(c.inicio), "fin": str(c.fin)}
            for c in db.scalars(
                select(Campana).where(Campana.tenant_id == tid)).all()
        ],
        "comunicados": [
            {"titulo": c.titulo, "estado": c.estado.value,
             "publicado_en": str(c.publicado_en) if c.publicado_en else None}
            for c in db.scalars(
                select(Comunicado).where(Comunicado.tenant_id == tid)).all()
        ],
        "clientes": [
            {"nombre": c.nombre, "ci": c.ci, "telefono": c.telefono,
             "saldo_puntos": c.saldo_puntos,
             "estado": c.estado.value, "created_at": str(c.created_at)}
            for c in clientes
        ],
        "movimientos_puntos": [
            {"cliente_id": m.cliente_id, "tipo": m.tipo.value,
             "puntos": m.puntos, "created_at": str(m.created_at)}
            for m in movs
        ],
        "facturas": [
            {"periodo": f.periodo, "monto": f.monto, "moneda": f.moneda,
             "estado": f.estado.value}
            for f in db.scalars(
                select(FacturaPlan).where(FacturaPlan.tenant_id == tid)).all()
        ],
    }


@router.post("/baja", response_model=MessageResponse)
def solicitar_baja(data: BajaIn, usuario: Usuario = Depends(get_current_usuario),
                   db: Session = Depends(get_db)):
    """Baja voluntaria con confirmación de contraseña.

    Suspende el tenant de inmediato y agenda la purga de datos a
    BAJA_RETENCION_DIAS días (job de limpieza). El admin puede cancelarla
    reactivando el tenant dentro del plazo.
    """
    if not usuario.password_hash or not verify_secret(data.password, usuario.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Contraseña incorrecta")
    tenant = db.get(Tenant, usuario.tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant no encontrado")
    if tenant.baja_solicitada_en is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "La baja ya fue solicitada")

    tenant.baja_solicitada_en = utcnow()
    if tenant.estado != EstadoTenant.suspendido:
        suspender_tenant(db, tenant, usuario.id,
                         motivo="baja voluntaria solicitada por el socio")
    registrar_audit(db, usuario.id, "baja_socio", "tenant", tenant.id,
                    {"retencion_dias": BAJA_RETENCION_DIAS})
    db.commit()
    revocar_todos_refresh(db, SujetoTipo.usuario, usuario.id)
    db.commit()

    for mail in emails_owner(db, tenant.id):
        email_service.send_baja_solicitada(mail, tenant.nombre_comercial,
                                           BAJA_RETENCION_DIAS)
    return MessageResponse(
        detail=f"Baja solicitada. Tus datos se conservan {BAJA_RETENCION_DIAS} "
               "días y luego se eliminan de forma definitiva."
    )
