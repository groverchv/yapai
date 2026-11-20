"""Webhook de Stripe: verificación de firma HMAC + procesamiento idempotente.

POST /api/v1/billing/stripe/webhook

- La firma `Stripe-Signature` se verifica con STRIPE_WEBHOOK_SECRET
  (HMAC-SHA256 de `t.{body}`, tolerancia 5 min) — sin SDK, implementación directa.
- Cada `event_id` se inserta en `eventos_stripe`; el UNIQUE lo hace idempotente.
- Eventos soportados:
    invoice.paid                  → factura del tenant → pagada (metodo=stripe)
    invoice.payment_failed        → factura pendiente → vencida + suspensión si aplica
    customer.subscription.deleted → tenant suspendido
"""
import hashlib
import hmac
import json
import logging
import time

from app.core.config import settings
from app.core.ratelimit import webhook_limiter
from app.core.security import utcnow
from app.db.session import get_db
from app.models import (
    EstadoFactura,
    EstadoTenant,
    EventoStripe,
    FacturaPlan,
    Tenant,
)
from app.services.audit import registrar_audit
from app.services.billing import suspender_por_impago
from app.services.email import email_service, emails_owner
from app.services.tenants import suspender_tenant
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger("yapai.stripe")

router = APIRouter()

_TOLERANCIA_SEG = 300


def _verificar_firma(payload: bytes, cabecera: str | None) -> None:
    """Valida Stripe-Signature (`t=ts,v1=sig,...`). Lanza 400 si no verifica."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Webhook de Stripe no configurado")
    if not cabecera:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Falta Stripe-Signature")
    partes = dict(
        kv.split("=", 1) for kv in cabecera.split(",") if "=" in kv
    )
    ts, firma = partes.get("t"), partes.get("v1")
    if not ts or not firma:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Stripe-Signature inválida")
    if abs(time.time() - int(ts)) > _TOLERANCIA_SEG:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Firma expirada (replay)")
    esperado = hmac.new(
        settings.STRIPE_WEBHOOK_SECRET.encode(),
        f"{ts}.".encode() + payload, hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(esperado, firma):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Firma inválida")


def _tenant_por_customer(db: Session, customer_id: str | None) -> Tenant | None:
    if not customer_id:
        return None
    return db.scalar(
        select(Tenant).where(Tenant.stripe_customer_id == customer_id))


def _pagar_factura(db: Session, tenant: Tenant, referencia: str,
                   factura_id: int | None = None) -> int:
    """Marca pagada la factura indicada (o la más antigua pendiente/vencida)."""
    q = select(FacturaPlan).where(
        FacturaPlan.tenant_id == tenant.id,
        FacturaPlan.estado.in_([EstadoFactura.pendiente, EstadoFactura.vencida]),
    )
    f = (db.scalar(q.where(FacturaPlan.id == factura_id)) if factura_id
         else db.scalar(q.order_by(FacturaPlan.vence_en).limit(1)))
    if not f:
        return 0
    f.estado = EstadoFactura.pagada
    f.pagada_en = utcnow()
    f.metodo = "stripe"
    f.referencia = referencia
    registrar_audit(db, None, "stripe_invoice_paid", "factura", f.id,
                    {"tenant_id": tenant.id, "ref": referencia})
    for mail in emails_owner(db, tenant.id):
        email_service.send_pago_recibido(
            mail, tenant.nombre_comercial, f.periodo, float(f.monto), f.moneda)
    # Reactivar si ya no quedan facturas vencidas (el pago curó la mora)
    from app.services.tenants import reactivar_tenant
    if tenant.estado == EstadoTenant.suspendido and not db.scalar(
            select(FacturaPlan.id).where(
                FacturaPlan.tenant_id == tenant.id,
                FacturaPlan.estado == EstadoFactura.vencida)):
        reactivar_tenant(db, tenant, None)
    return 1


def _tenant_por_factura(db: Session, factura_id: int | None) -> Tenant | None:
    if not factura_id:
        return None
    f = db.get(FacturaPlan, int(factura_id))
    return db.get(Tenant, f.tenant_id) if f else None


def _fallo_pago(db: Session, tenant: Tenant, referencia: str) -> None:
    """Marca vencida la pendiente y aplica la regla de suspensión por mora."""
    f = db.scalar(
        select(FacturaPlan).where(
            FacturaPlan.tenant_id == tenant.id,
            FacturaPlan.estado == EstadoFactura.pendiente,
        ).order_by(FacturaPlan.vence_en).limit(1)
    )
    if f:
        f.estado = EstadoFactura.vencida
        f.referencia = referencia
    suspender_por_impago(db)
    registrar_audit(db, None, "stripe_payment_failed", "tenant", tenant.id,
                    {"ref": referencia})


@router.post("/stripe/webhook", include_in_schema=False,
             dependencies=[Depends(webhook_limiter)])
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Recibe eventos de Stripe. Siempre 200 tras firma válida (aunque el
    evento ya se procesó) para detener reintentos; 400 solo si firma inválida."""
    payload = await request.body()
    _verificar_firma(payload, request.headers.get("stripe-signature"))
    try:
        evento = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "JSON inválido") from None

    event_id, tipo = evento.get("id"), evento.get("type")
    if not event_id or not tipo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Evento mal formado")

    # Idempotencia: el UNIQUE revienta en el INSERT si ya se procesó
    db.add(EventoStripe(event_id=event_id, tipo=tipo))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"status": "duplicado"}

    data = (evento.get("data") or {}).get("object") or {}
    customer = data.get("customer")
    metadata = data.get("metadata") or {}
    factura_meta = metadata.get("factura_id")
    try:
        factura_meta = int(factura_meta) if factura_meta else None
    except (TypeError, ValueError):
        factura_meta = None
    tenant = _tenant_por_customer(db, customer) or _tenant_por_factura(db, factura_meta)

    if tipo == "checkout.session.completed":
        # El checkout del portal de facturación: liga el customer y liquida
        if tenant:
            if customer and not tenant.stripe_customer_id:
                tenant.stripe_customer_id = customer
            _pagar_factura(db, tenant, data.get("id", ""), factura_meta)
    elif tipo == "invoice.paid" and tenant:
        _pagar_factura(db, tenant, data.get("id", ""))
    elif tipo == "invoice.payment_failed" and tenant:
        _fallo_pago(db, tenant, data.get("id", ""))
    elif tipo == "customer.subscription.deleted" and tenant:
        if tenant.estado == EstadoTenant.activo:
            suspender_tenant(db, tenant, None)
    else:
        # Tipo no manejado o customer desconocido: se registra y se descarta
        registrar_audit(db, None, "stripe_evento_ignorado", "stripe", 0,
                        {"tipo": tipo, "event": event_id})
    db.commit()
    return {"status": "procesado"}
