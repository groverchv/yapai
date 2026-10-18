from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_superadmin
from app.db.session import get_db
from app.models import EstadoFactura, FacturaPlan, Tenant, Usuario
from app.schemas.admin import FacturaOut, FacturaPagarIn, Pagina
from app.services.audit import registrar_audit
from app.services.billing import generar_facturas, pagar_factura, periodo_de

router = APIRouter(dependencies=[Depends(require_superadmin)])


def _out(db: Session, f: FacturaPlan) -> FacturaOut:
    tenant = db.get(Tenant, f.tenant_id)
    return FacturaOut(
        id=f.id, tenant_id=f.tenant_id,
        socio_nombre=tenant.nombre_comercial if tenant else f"#{f.tenant_id}",
        plan_nombre=f.plan_nombre, periodo=f.periodo,
        monto=float(f.monto), moneda=f.moneda, estado=f.estado.value,
        emitida_en=f.emitida_en, vence_en=f.vence_en, pagada_en=f.pagada_en,
        metodo=f.metodo, referencia=f.referencia,
    )


@router.get("", response_model=Pagina[FacturaOut])
def listar_facturas(
    estado: EstadoFactura | None = Query(None),
    tenant_id: int | None = Query(None),
    periodo: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
):
    filtros = []
    if estado:
        filtros.append(FacturaPlan.estado == estado)
    if tenant_id:
        filtros.append(FacturaPlan.tenant_id == tenant_id)
    if periodo:
        filtros.append(FacturaPlan.periodo == periodo)

    total = db.scalar(select(func.count(FacturaPlan.id)).where(*filtros)) or 0
    q = (
        select(FacturaPlan)
        .where(*filtros)
        .order_by(FacturaPlan.periodo.desc(), FacturaPlan.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = db.scalars(q).all()
    return Pagina(items=[_out(db, f) for f in rows], total=total, page=page, size=size)


@router.post("/generar", status_code=status.HTTP_201_CREATED)
def generar_periodo(
    periodo: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_superadmin),
):
    """Emite facturas del período (default el actual) para todos los tenants que
    corresponde. Idempotente: no duplica las ya emitidas."""
    creadas = generar_facturas(db, periodo)
    registrar_audit(db, admin.id, "facturas_generar",
                    "factura_plan", None, {"periodo": periodo or periodo_de(),
                                           "emitidas": len(creadas)})
    db.commit()
    return {"periodo": periodo or periodo_de(), "emitidas": len(creadas),
            "facturas": [_out(db, f) for f in creadas]}


@router.post("/{factura_id}/pagar", response_model=FacturaOut)
def marcar_pagada(factura_id: int, data: FacturaPagarIn,
                  db: Session = Depends(get_db),
                  admin: Usuario = Depends(require_superadmin)):
    f = db.get(FacturaPlan, factura_id)
    if not f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Factura no encontrada")
    if f.estado == EstadoFactura.pagada:
        return _out(db, f)
    if f.estado == EstadoFactura.anulada:
        raise HTTPException(status.HTTP_409_CONFLICT, "La factura está anulada")
    pagar_factura(db, f, admin, data.metodo, data.referencia)
    registrar_audit(db, admin.id, "factura_pagada",
                    "factura_plan", f.id, {"metodo": data.metodo,
                                           "referencia": data.referencia})
    db.commit()
    return _out(db, f)


@router.post("/{factura_id}/anular", response_model=FacturaOut)
def anular_factura(factura_id: int, db: Session = Depends(get_db),
                   admin: Usuario = Depends(require_superadmin)):
    f = db.get(FacturaPlan, factura_id)
    if not f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Factura no encontrada")
    if f.estado == EstadoFactura.pagada:
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede anular una factura pagada")
    f.estado = EstadoFactura.anulada
    registrar_audit(db, admin.id, "factura_anulada", "factura_plan", f.id, None)
    db.commit()
    return _out(db, f)
