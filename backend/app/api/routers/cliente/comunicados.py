"""Feed de comunicados/ofertas para la app del cliente.

Muestra los comunicados publicados y vigentes de TODOS los tenants activos —
el descubrimiento es el valor del marketplace. Orden: más reciente primero.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_cliente
from app.core.security import utcnow
from app.db.session import get_db
from app.models import (
    Cliente, Comunicado, EstadoComunicado, EstadoTenant, Tenant,
)
from app.schemas.admin import Pagina
from app.schemas.cliente import ComunicadoClienteOut

router = APIRouter()


@router.get("/comunicados", response_model=Pagina[ComunicadoClienteOut])
def feed(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
         cliente: Cliente = Depends(get_current_cliente),
         db: Session = Depends(get_db)):
    ahora = utcnow()
    filtros = [
        Comunicado.estado == EstadoComunicado.publicado,
        Tenant.estado == EstadoTenant.activo,
        or_(Comunicado.vigencia_hasta.is_(None),
            Comunicado.vigencia_hasta > ahora),
    ]
    total = db.scalar(
        select(func.count(Comunicado.id))
        .join(Tenant, Tenant.id == Comunicado.tenant_id)
        .where(*filtros)
    ) or 0
    rows = db.execute(
        select(Comunicado, Tenant)
        .join(Tenant, Tenant.id == Comunicado.tenant_id)
        .where(*filtros)
        .order_by(Comunicado.publicado_en.desc())
        .offset((page - 1) * size).limit(size)
    ).all()
    items = [
        ComunicadoClienteOut(
            id=c.id, titulo=c.titulo, descripcion=c.descripcion,
            imagen_url=c.imagen_url, premio_id=c.premio_id,
            publicado_en=c.publicado_en, vigencia_hasta=c.vigencia_hasta,
            tenant_id=t.id, comercio=t.nombre_comercial, logo_url=t.logo_url,
        )
        for c, t in rows
    ]
    return Pagina(items=items, total=total, page=page, size=size)
