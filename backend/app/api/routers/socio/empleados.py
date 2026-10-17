from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import require_owner
from app.core.security import generar_token_plano, sha256_hex, utcnow
from app.db.session import get_db
from app.models import (
    EmpleadoSucursal, EstadoUsuario, PasswordReset, RolUsuario,
    Sucursal, SujetoTipo, Tenant, Usuario,
)
from app.schemas.admin import Pagina
from app.schemas.auth import MessageResponse
from app.schemas.socio import EmpleadoIn, EmpleadoOut, EmpleadoUpdate
from app.services.audit import registrar_audit
from app.services.auth import crear_onboarding_token, revocar_todos_refresh
from app.services.email import email_service
from app.services.planes import verificar_limite

router = APIRouter(dependencies=[Depends(require_owner)])


def _empleado_out(db: Session, u: Usuario) -> EmpleadoOut:
    sucursales = db.scalars(
        select(Sucursal.nombre)
        .join(EmpleadoSucursal, EmpleadoSucursal.sucursal_id == Sucursal.id)
        .where(EmpleadoSucursal.usuario_id == u.id)
    ).all()
    return EmpleadoOut(
        id=u.id, nombre=u.nombre, email=u.email, estado=u.estado.value,
        onboarding_pendiente=u.password_hash is None,
        sucursales=list(sucursales), ultimo_login=u.ultimo_login,
    )


def _get_empleado(db: Session, tenant_id: int, empleado_id: int) -> Usuario:
    u = db.scalar(
        select(Usuario).where(
            Usuario.id == empleado_id, Usuario.tenant_id == tenant_id,
            Usuario.rol == RolUsuario.cajero,
        )
    )
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empleado no encontrado")
    return u


def _validar_sucursales(db: Session, tenant_id: int, ids: list[int]) -> None:
    if not ids:
        return
    validas = db.scalar(
        select(func.count(Sucursal.id)).where(Sucursal.id.in_(ids), Sucursal.tenant_id == tenant_id)
    ) or 0
    if validas != len(set(ids)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Alguna sucursal no pertenece a tu comercio")


@router.get("", response_model=Pagina[EmpleadoOut])
def listar_empleados(
    q: str | None = None, estado: EstadoUsuario | None = None,
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=200),
    usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db),
):
    filtros = [Usuario.tenant_id == usuario.tenant_id, Usuario.rol == RolUsuario.cajero]
    if estado:
        filtros.append(Usuario.estado == estado)
    if q:
        like = f"%{q}%"
        filtros.append((Usuario.nombre.ilike(like)) | (Usuario.email.ilike(like)))
    total = db.scalar(select(func.count(Usuario.id)).where(*filtros)) or 0
    rows = db.scalars(
        select(Usuario).where(*filtros).order_by(Usuario.id)
        .offset((page - 1) * size).limit(size)
    ).all()
    return Pagina(items=[_empleado_out(db, u) for u in rows], total=total, page=page, size=size)


@router.post("", response_model=EmpleadoOut, status_code=status.HTTP_201_CREATED)
def crear_empleado(data: EmpleadoIn, usuario: Usuario = Depends(require_owner),
                   db: Session = Depends(get_db)):
    """Alta de cajero: crea la cuenta y envía credenciales por email (onboarding)."""
    if db.scalar(select(Usuario).where(Usuario.email == data.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado")
    verificar_limite(db, db.get(Tenant, usuario.tenant_id), "empleados")
    _validar_sucursales(db, usuario.tenant_id, data.sucursal_ids)

    empleado = Usuario(
        email=data.email, nombre=data.nombre, rol=RolUsuario.cajero,
        tenant_id=usuario.tenant_id, password_hash=None,
    )
    db.add(empleado)
    db.flush()
    for sid in set(data.sucursal_ids):
        db.add(EmpleadoSucursal(usuario_id=empleado.id, sucursal_id=sid))
    token = crear_onboarding_token(db, data.email, usuario.tenant_id)
    registrar_audit(db, usuario.id, "alta_empleado", "usuario", empleado.id)
    db.commit()

    link = f"{settings.FRONTEND_SOCIO_URL}/onboarding?token={token}"
    email_service.send_onboarding(data.email, "tu comercio", link)
    return _empleado_out(db, empleado)


@router.patch("/{empleado_id}", response_model=EmpleadoOut)
def editar_empleado(empleado_id: int, data: EmpleadoUpdate,
                    usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    emp = _get_empleado(db, usuario.tenant_id, empleado_id)
    cambios = data.model_dump(exclude_unset=True)
    if "nombre" in cambios:
        emp.nombre = cambios["nombre"]
    if "sucursal_ids" in cambios and cambios["sucursal_ids"] is not None:
        _validar_sucursales(db, usuario.tenant_id, cambios["sucursal_ids"])
        db.query(EmpleadoSucursal).filter(EmpleadoSucursal.usuario_id == emp.id).delete()
        for sid in set(cambios["sucursal_ids"]):
            db.add(EmpleadoSucursal(usuario_id=emp.id, sucursal_id=sid))
    registrar_audit(db, usuario.id, "editar_empleado", "usuario", emp.id, cambios)
    db.commit()
    return _empleado_out(db, emp)


@router.post("/{empleado_id}/suspender", response_model=EmpleadoOut)
def suspender_empleado(empleado_id: int, usuario: Usuario = Depends(require_owner),
                       db: Session = Depends(get_db)):
    emp = _get_empleado(db, usuario.tenant_id, empleado_id)
    emp.estado = EstadoUsuario.suspendido
    revocar_todos_refresh(db, SujetoTipo.usuario, emp.id)
    registrar_audit(db, usuario.id, "suspender_empleado", "usuario", emp.id)
    db.commit()
    return _empleado_out(db, emp)


@router.post("/{empleado_id}/reactivar", response_model=EmpleadoOut)
def reactivar_empleado(empleado_id: int, usuario: Usuario = Depends(require_owner),
                       db: Session = Depends(get_db)):
    emp = _get_empleado(db, usuario.tenant_id, empleado_id)
    emp.estado = EstadoUsuario.activo
    registrar_audit(db, usuario.id, "reactivar_empleado", "usuario", emp.id)
    db.commit()
    return _empleado_out(db, emp)


@router.post("/{empleado_id}/reenviar", response_model=MessageResponse)
def reenviar_credenciales(empleado_id: int, usuario: Usuario = Depends(require_owner),
                          db: Session = Depends(get_db)):
    """Reenvía credenciales: onboarding si nunca activó, reset de clave si ya la tiene."""
    emp = _get_empleado(db, usuario.tenant_id, empleado_id)
    if emp.password_hash is None:
        token = crear_onboarding_token(db, emp.email, usuario.tenant_id)
        link = f"{settings.FRONTEND_SOCIO_URL}/onboarding?token={token}"
        email_service.send_onboarding(emp.email, "tu comercio", link)
        accion = "reenviar_onboarding_empleado"
    else:
        plano = generar_token_plano()
        db.add(PasswordReset(
            usuario_id=emp.id, token_hash=sha256_hex(plano),
            expira_en=utcnow() + timedelta(hours=settings.RESET_TOKEN_HOURS),
        ))
        revocar_todos_refresh(db, SujetoTipo.usuario, emp.id)
        link = f"{settings.FRONTEND_SOCIO_URL}/recuperar?token={plano}"
        email_service.send_password_reset(emp.email, link)
        accion = "reenviar_reset_empleado"
    registrar_audit(db, usuario.id, accion, "usuario", emp.id)
    db.commit()
    return MessageResponse(detail=f"Credenciales enviadas a {emp.email}")
