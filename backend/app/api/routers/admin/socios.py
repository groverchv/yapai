from datetime import date, timedelta

from app.core.config import settings
from app.core.deps import require_superadmin
from app.core.security import generar_token_plano, sha256_hex, utcnow
from app.db.session import get_db
from app.models import (
    CategoriaNegocio,
    Cliente,
    ConfigPin,
    EsquemaComision,
    EstadoPremio,
    EstadoTenant,
    MovimientoPuntos,
    PasswordReset,
    Plan,
    Premio,
    RolUsuario,
    Sucursal,
    SujetoTipo,
    Tenant,
    Usuario,
)
from app.schemas.admin import (
    ClienteListItem,
    KpisSocio,
    OwnerOut,
    Pagina,
    SocioCreadoResponse,
    SocioCreate,
    SocioDetalle,
    SocioListItem,
    SocioPlanUpdate,
    SocioUpdate,
    SucursalListItem,
    UsuarioListItem,
)
from app.schemas.auth import MessageResponse
from app.schemas.socio import FirmaUploadOut
from app.services.audit import registrar_audit
from app.services.auth import crear_onboarding_token, revocar_todos_refresh
from app.services.billing import estado_cuenta
from app.services.email import email_service
from app.services.export import csv_response
from app.services.kpis import calcular_kpis_socio
from app.services.tenants import reactivar_tenant, suspender_tenant
from app.services.uploads import firma_disponible, generar_firma
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_superadmin)])


@router.post("/uploads/firma", response_model=FirmaUploadOut)
def firma_upload_socio(carpeta: str = Query("logos", max_length=40, pattern=r"^[a-z0-9_\-]+$"),
                       tenant_id: int | None = Query(None)):
    """Firma para subir el logo a Cloudinary directamente desde el frontend admin."""
    if not firma_disponible():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Almacenamiento de imágenes no configurado (Cloudinary)",
        )
    return FirmaUploadOut(**generar_firma(tenant_id=tenant_id, carpeta=carpeta))



def _detalle(db: Session, tenant: Tenant) -> SocioDetalle:
    owner = db.scalar(
        select(Usuario).where(Usuario.tenant_id == tenant.id, Usuario.rol == RolUsuario.owner)
    )
    categoria = db.get(CategoriaNegocio, tenant.categoria_id).nombre if tenant.categoria_id else None
    esquema = db.get(EsquemaComision, tenant.esquema_comision_id).nombre if tenant.esquema_comision_id else None
    total_sucursales = db.scalar(select(func.count(Sucursal.id)).where(Sucursal.tenant_id == tenant.id)) or 0
    total_empleados = db.scalar(select(func.count(Usuario.id)).where(Usuario.tenant_id == tenant.id)) or 0
    total_clientes = db.scalar(
        select(func.count(func.distinct(MovimientoPuntos.cliente_id)))
        .where(MovimientoPuntos.tenant_id == tenant.id)
    ) or 0
    total_premios = db.scalar(
        select(func.count(Premio.id)).where(Premio.tenant_id == tenant.id, Premio.estado == EstadoPremio.activo)
    ) or 0
    return SocioDetalle(
        id=tenant.id, nombre_comercial=tenant.nombre_comercial,
        razon_social=tenant.razon_social, nit_rut=tenant.nit_rut,
        email_contacto=tenant.email_contacto, telefono=tenant.telefono,
        logo_url=tenant.logo_url, categoria_id=tenant.categoria_id, categoria=categoria,
        esquema_comision_id=tenant.esquema_comision_id, esquema=esquema,
        estado=tenant.estado.value, created_at=tenant.created_at,
        suspendido_en=tenant.suspendido_en,
        owner=OwnerOut(
            id=owner.id, nombre=owner.nombre, email=owner.email,
            estado=owner.estado.value, onboarding_pendiente=owner.password_hash is None,
        ) if owner else None,
        total_sucursales=total_sucursales, total_empleados=total_empleados,
        total_clientes=total_clientes, total_premios_activos=total_premios,
        plan_id=tenant.plan_id,
        plan=db.get(Plan, tenant.plan_id).nombre if tenant.plan_id else None,
        trial_fin=tenant.trial_fin,
        facturacion_estado=estado_cuenta(db, tenant),
    )


def _filtros_socios(estado, q, nit):
    filtros = []
    if estado:
        filtros.append(Tenant.estado == estado)
    if q:
        like = f"%{q}%"
        filtros.append(or_(Tenant.nombre_comercial.ilike(like), Tenant.razon_social.ilike(like)))
    if nit:
        filtros.append(Tenant.nit_rut.ilike(f"%{nit}%"))
    return filtros


@router.get("", response_model=Pagina[SocioListItem])
def listar_socios(
    estado: EstadoTenant | None = None,
    q: str | None = None,
    nit: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    format: str | None = Query(None, pattern="^csv$"),
    db: Session = Depends(get_db),
):
    """Listado con paginación server-side, filtros y exportación CSV."""
    filtros = _filtros_socios(estado, q, nit)
    stmt = (
        select(Tenant, CategoriaNegocio.nombre.label("categoria"), EsquemaComision.nombre.label("esquema"))
        .outerjoin(CategoriaNegocio, Tenant.categoria_id == CategoriaNegocio.id)
        .outerjoin(EsquemaComision, Tenant.esquema_comision_id == EsquemaComision.id)
        .where(*filtros)
        .order_by(Tenant.created_at.desc())
    )
    if format == "csv":
        rows = db.execute(stmt).all()
        return csv_response(
            "socios.csv",
            ["id", "nombre_comercial", "nit_rut", "categoria", "esquema", "estado", "fecha_alta"],
            [(t.id, t.nombre_comercial, t.nit_rut, cat or "", esq or "", t.estado.value, t.created_at)
             for t, cat, esq in rows],
        )
    total = db.scalar(select(func.count(Tenant.id)).where(*filtros)) or 0
    rows = db.execute(stmt.offset((page - 1) * size).limit(size)).all()
    items = [
        SocioListItem(
            id=t.id, nombre_comercial=t.nombre_comercial, nit_rut=t.nit_rut,
            logo_url=t.logo_url, categoria=cat, esquema=esq, estado=t.estado.value,
            created_at=t.created_at,
        )
        for t, cat, esq in rows
    ]
    return Pagina(items=items, total=total, page=page, size=size)


@router.post("", response_model=SocioCreadoResponse, status_code=status.HTTP_201_CREATED)
def crear_socio(data: SocioCreate, db: Session = Depends(get_db), admin: Usuario = Depends(require_superadmin)):
    """Alta manual: crea tenant + owner + envía email de onboarding con link único."""
    if db.scalar(select(Tenant).where(Tenant.nit_rut == data.nit_rut)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un socio con ese NIT/RUT")
    if db.scalar(select(Usuario).where(Usuario.email == data.owner.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "El email del owner ya está registrado")
    if data.categoria_id and not db.get(CategoriaNegocio, data.categoria_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Categoría inválida")
    if data.esquema_comision_id and not db.get(EsquemaComision, data.esquema_comision_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esquema de comisión inválido")

    tenant = Tenant(
        nombre_comercial=data.nombre_comercial, razon_social=data.razon_social,
        nit_rut=data.nit_rut, email_contacto=data.email_contacto,
        telefono=data.telefono, logo_url=data.logo_url,
        categoria_id=data.categoria_id, esquema_comision_id=data.esquema_comision_id,
    )
    db.add(tenant)
    db.flush()
    db.add(Usuario(
        email=data.owner.email, nombre=data.owner.nombre,
        rol=RolUsuario.owner, tenant_id=tenant.id, password_hash=None,
    ))
    db.add(ConfigPin(tenant_id=tenant.id))
    token = crear_onboarding_token(db, data.owner.email, tenant.id)
    registrar_audit(db, admin.id, "alta_socio", "tenant", tenant.id,
                    {"owner_email": data.owner.email})
    db.commit()

    link = f"{settings.FRONTEND_SOCIO_URL}/onboarding?token={token}"
    email_service.send_onboarding(data.owner.email, tenant.nombre_comercial, link)
    return SocioCreadoResponse(socio=_detalle(db, tenant), onboarding_link=link)


def _get_tenant(db: Session, tenant_id: int) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Socio no encontrado")
    return tenant


@router.get("/{tenant_id}", response_model=SocioDetalle)
def detalle_socio(tenant_id: int, db: Session = Depends(get_db)):
    return _detalle(db, _get_tenant(db, tenant_id))


@router.patch("/{tenant_id}", response_model=SocioDetalle)
def editar_socio(tenant_id: int, data: SocioUpdate, db: Session = Depends(get_db),
                 admin: Usuario = Depends(require_superadmin)):
    tenant = _get_tenant(db, tenant_id)
    cambios = data.model_dump(exclude_unset=True)
    if "nit_rut" in cambios and cambios["nit_rut"] != tenant.nit_rut:
        if db.scalar(select(Tenant).where(Tenant.nit_rut == cambios["nit_rut"], Tenant.id != tenant.id)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un socio con ese NIT/RUT")
    for campo, valor in cambios.items():
        setattr(tenant, campo, valor)
    registrar_audit(db, admin.id, "editar_socio", "tenant", tenant.id, cambios)
    db.commit()
    return _detalle(db, tenant)


@router.patch("/{tenant_id}/plan", response_model=SocioDetalle)
def cambiar_plan(tenant_id: int, data: SocioPlanUpdate, db: Session = Depends(get_db),
                 admin: Usuario = Depends(require_superadmin)):
    """Asigna/cambia el plan comercial del socio (None = sin restricciones)."""
    tenant = _get_tenant(db, tenant_id)
    if data.plan_id is not None and not db.get(Plan, data.plan_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Plan inválido")
    tenant.plan_id = data.plan_id
    if data.trial_fin is not None:
        tenant.trial_fin = data.trial_fin
    registrar_audit(db, admin.id, "cambiar_plan", "tenant", tenant.id,
                    {"plan_id": data.plan_id})
    db.commit()
    return _detalle(db, tenant)


@router.post("/{tenant_id}/suspender", response_model=SocioDetalle)
def suspender_socio(tenant_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(require_superadmin)):
    tenant = _get_tenant(db, tenant_id)
    if tenant.estado == EstadoTenant.suspendido:
        raise HTTPException(status.HTTP_409_CONFLICT, "El socio ya está suspendido")
    suspender_tenant(db, tenant, admin.id)
    db.commit()
    return _detalle(db, tenant)


@router.post("/{tenant_id}/reactivar", response_model=SocioDetalle)
def reactivar_socio(tenant_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(require_superadmin)):
    tenant = _get_tenant(db, tenant_id)
    if tenant.estado == EstadoTenant.activo:
        raise HTTPException(status.HTTP_409_CONFLICT, "El socio ya está activo")
    reactivar_tenant(db, tenant, admin.id)
    db.commit()
    return _detalle(db, tenant)


def _owner_del_tenant(db: Session, tenant_id: int) -> Usuario:
    owner = db.scalar(
        select(Usuario).where(Usuario.tenant_id == tenant_id, Usuario.rol == RolUsuario.owner)
    )
    if not owner:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El socio no tiene owner asignado")
    return owner


@router.post("/{tenant_id}/forzar-reset", response_model=MessageResponse)
def forzar_reset(tenant_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(require_superadmin)):
    """Fuerza la recuperación de contraseña del Owner: revoca sesiones y envía link."""
    _get_tenant(db, tenant_id)
    owner = _owner_del_tenant(db, tenant_id)
    plano = generar_token_plano()
    db.add(PasswordReset(
        usuario_id=owner.id, token_hash=sha256_hex(plano),
        expira_en=utcnow() + timedelta(hours=settings.RESET_TOKEN_HOURS),
    ))
    revocar_todos_refresh(db, SujetoTipo.usuario, owner.id)
    registrar_audit(db, admin.id, "forzar_reset_owner", "usuario", owner.id, {"tenant_id": tenant_id})
    db.commit()
    link = f"{settings.FRONTEND_SOCIO_URL}/recuperar?token={plano}"
    email_service.send_password_reset(owner.email, link)
    return MessageResponse(detail=f"Se envió el enlace de recuperación a {owner.email}")


@router.post("/{tenant_id}/reenviar-onboarding", response_model=MessageResponse)
def reenviar_onboarding(tenant_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(require_superadmin)):
    """Reenvía el email de bienvenida. Solo aplica si el Owner aún no activó su cuenta."""
    _get_tenant(db, tenant_id)
    owner = _owner_del_tenant(db, tenant_id)
    if owner.password_hash:
        raise HTTPException(status.HTTP_409_CONFLICT, "El owner ya activó su cuenta; use forzar-reset")
    token = crear_onboarding_token(db, owner.email, tenant_id)
    registrar_audit(db, admin.id, "reenviar_onboarding", "usuario", owner.id)
    db.commit()
    link = f"{settings.FRONTEND_SOCIO_URL}/onboarding?token={token}"
    email_service.send_onboarding(owner.email, "tu comercio", link)
    return MessageResponse(detail=f"Se reenvió el enlace de onboarding a {owner.email}")


@router.get("/{tenant_id}/kpis", response_model=KpisSocio)
def kpis_socio(tenant_id: int, desde: date | None = None, hasta: date | None = None,
               db: Session = Depends(get_db)):
    _get_tenant(db, tenant_id)
    return calcular_kpis_socio(db, tenant_id, desde, hasta)


@router.get("/{tenant_id}/clientes", response_model=Pagina[ClienteListItem])
def clientes_del_socio(
    tenant_id: int,
    q: str | None = None,
    page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
):
    _get_tenant(db, tenant_id)
    ids = select(MovimientoPuntos.cliente_id).where(MovimientoPuntos.tenant_id == tenant_id).distinct()
    filtros = [Cliente.id.in_(ids)]
    if q:
        like = f"%{q}%"
        filtros.append(or_(Cliente.nombre.ilike(like), Cliente.ci.ilike(like), Cliente.telefono.ilike(like)))
    total = db.scalar(select(func.count(Cliente.id)).where(*filtros)) or 0
    rows = db.scalars(
        select(Cliente).where(*filtros).order_by(Cliente.created_at.desc())
        .offset((page - 1) * size).limit(size)
    ).all()
    return Pagina(
        items=[ClienteListItem(id=c.id, nombre=c.nombre, ci=c.ci, telefono=c.telefono,
                               estado=c.estado.value, created_at=c.created_at) for c in rows],
        total=total, page=page, size=size,
    )


@router.get("/{tenant_id}/usuarios", response_model=list[UsuarioListItem])
def usuarios_del_socio(tenant_id: int, db: Session = Depends(get_db)):
    _get_tenant(db, tenant_id)
    rows = db.scalars(select(Usuario).where(Usuario.tenant_id == tenant_id).order_by(Usuario.id)).all()
    return [UsuarioListItem(id=u.id, nombre=u.nombre, email=u.email, rol=u.rol.value,
                            estado=u.estado.value, ultimo_login=u.ultimo_login) for u in rows]


@router.get("/{tenant_id}/sucursales", response_model=list[SucursalListItem])
def sucursales_del_socio(tenant_id: int, db: Session = Depends(get_db)):
    _get_tenant(db, tenant_id)
    rows = db.scalars(select(Sucursal).where(Sucursal.tenant_id == tenant_id).order_by(Sucursal.id)).all()
    return [SucursalListItem(id=s.id, nombre=s.nombre, direccion=s.direccion,
                           encargado_nombre=s.encargado_nombre, estado=s.estado.value) for s in rows]
