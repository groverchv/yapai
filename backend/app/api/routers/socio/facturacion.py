from app.core.config import settings
from app.core.deps import require_owner
from app.core.security import utcnow
from app.db.session import get_db
from app.models import EstadoFactura, FacturaPlan, Tenant, Usuario
from app.schemas.auth import MessageResponse
from app.schemas.socio import ComprobanteIn, EstadoCuentaOut, FacturaSocioOut
from app.services.audit import registrar_audit
from app.services.billing import estado_cuenta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_owner)])


@router.get("", response_model=EstadoCuentaOut)
def mi_facturacion(usuario: Usuario = Depends(require_owner),
                   db: Session = Depends(get_db)):
    """Estado de cuenta del socio + historial de facturas del plan."""
    tenant = db.get(Tenant, usuario.tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant no encontrado")
    facturas = db.scalars(
        select(FacturaPlan)
        .where(FacturaPlan.tenant_id == tenant.id,
               FacturaPlan.estado != EstadoFactura.anulada)
        .order_by(FacturaPlan.periodo.desc(), FacturaPlan.id.desc())
    ).all()
    return EstadoCuentaOut(
        estado=estado_cuenta(db, tenant),
        pago_online=bool(settings.STRIPE_SECRET_KEY),
        facturas=[
            FacturaSocioOut(
                id=f.id, plan_nombre=f.plan_nombre, periodo=f.periodo,
                monto=float(f.monto), moneda=f.moneda, estado=f.estado.value,
                emitida_en=f.emitida_en, vence_en=f.vence_en,
                pagada_en=f.pagada_en, metodo=f.metodo,
                comprobante_url=f.comprobante_url,
            )
            for f in facturas
        ],
    )


@router.post("/{factura_id}/comprobante", response_model=MessageResponse)
def subir_comprobante(factura_id: int, data: ComprobanteIn,
                      usuario: Usuario = Depends(require_owner),
                      db: Session = Depends(get_db)):
    """Registra el comprobante de un pago manual (transferencia/QR).

    La imagen ya subió a Cloudinary vía /socio/media/upload; aquí solo se
    persiste la URL. El admin confirma el pago desde su panel.
    """
    if not data.url.startswith("https://"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "URL de comprobante inválida")
    f = db.scalar(
        select(FacturaPlan).where(
            FacturaPlan.id == factura_id,
            FacturaPlan.tenant_id == usuario.tenant_id,
        )
    )
    if not f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Factura no encontrada")
    if f.estado not in (EstadoFactura.pendiente, EstadoFactura.vencida):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Solo las facturas pendientes o vencidas admiten comprobante")
    f.comprobante_url = data.url
    f.comprobante_en = utcnow()
    registrar_audit(db, usuario.id, "comprobante_subido", "factura", f.id,
                    {"periodo": f.periodo})
    db.commit()
    return MessageResponse(
        detail="Comprobante registrado. Confirmaremos tu pago en un máximo de 24 h hábiles.")


@router.post("/checkout")
def checkout_stripe(factura_id: int | None = None,
                    usuario: Usuario = Depends(require_owner),
                    db: Session = Depends(get_db)):
    """Crea una Stripe Checkout Session para pagar la factura pendiente del
    socio. Devuelve la URL hosted de Stripe — el frontend redirige ahí.

    Sin SDK: POST directo a api.stripe.com con STRIPE_SECRET_KEY.
    El webhook `checkout.session.completed` liquida la factura.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Pago en línea no configurado")
    q = select(FacturaPlan).where(
        FacturaPlan.tenant_id == usuario.tenant_id,
        FacturaPlan.estado.in_([EstadoFactura.pendiente, EstadoFactura.vencida]),
    ).order_by(FacturaPlan.vence_en)
    f = db.scalar(q.where(FacturaPlan.id == factura_id)) if factura_id else db.scalar(q.limit(1))
    if not f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay factura pendiente de pago")
    tenant = db.get(Tenant, usuario.tenant_id)

    import httpx
    base = settings.FRONTEND_SOCIO_URL.rstrip("/")
    try:
        r = httpx.post(
            "https://api.stripe.com/v1/checkout/sessions",
            auth=(settings.STRIPE_SECRET_KEY, ""),
            data={
                "mode": "payment",
                "success_url": f"{base}/facturacion?pago=ok",
                "cancel_url": f"{base}/facturacion",
                "client_reference_id": str(f.id),
                "customer_email": usuario.email,
                "line_items[0][price_data][currency]": f.moneda.lower(),
                "line_items[0][price_data][unit_amount]": int(float(f.monto) * 100),
                "line_items[0][price_data][product_data][name]":
                    f"YAPAI {f.plan_nombre} — {f.periodo}",
                "line_items[0][quantity]": "1",
                "metadata[factura_id]": str(f.id),
                "metadata[tenant_id]": str(tenant.id if tenant else ""),
            },
            timeout=15.0,
        )
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            "La pasarela de pagos rechazó la operación") from e
    except httpx.RequestError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            "No se pudo contactar la pasarela de pagos") from e
    return {"url": r.json()["url"]}
