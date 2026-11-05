from app.core.deps import require_owner
from app.db.session import get_db
from app.models import EstadoFactura, FacturaPlan, Tenant, Usuario
from app.schemas.socio import EstadoCuentaOut, FacturaSocioOut
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
        facturas=[
            FacturaSocioOut(
                id=f.id, plan_nombre=f.plan_nombre, periodo=f.periodo,
                monto=float(f.monto), moneda=f.moneda, estado=f.estado.value,
                emitida_en=f.emitida_en, vence_en=f.vence_en,
                pagada_en=f.pagada_en, metodo=f.metodo,
            )
            for f in facturas
        ],
    )
