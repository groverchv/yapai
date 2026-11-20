"""Gestión de cuentas superadmin (equipo YAPAI).

Alta con email de activación vía enlace de "definir contraseña" (PasswordReset
reusado — el flujo de seteo inicial es el mismo que el de recuperación).
No se puede desactivar a uno mismo ni al último superadmin activo.
"""
from datetime import timedelta

from app.core.config import settings
from app.core.deps import require_superadmin_2fa
from app.core.security import generar_token_plano, sha256_hex, utcnow
from app.db.session import get_db
from app.models import (
    EstadoUsuario,
    PasswordReset,
    RolUsuario,
    SujetoTipo,
    Usuario,
)
from app.schemas.admin import UsuarioListItem
from app.schemas.auth import MessageResponse
from app.services.audit import registrar_audit
from app.services.auth import revocar_todos_refresh
from app.services.email import email_service
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_superadmin_2fa)])


class SuperadminCreate(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=2, max_length=120)


def _superadmins_activos(db: Session) -> int:
    return db.scalar(
        select(func.count(Usuario.id)).where(
            Usuario.rol == RolUsuario.superadmin,
            Usuario.estado == EstadoUsuario.activo,
        )
    ) or 0


@router.get("", response_model=list[UsuarioListItem])
def listar_superadmins(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Usuario).where(Usuario.rol == RolUsuario.superadmin)
        .order_by(Usuario.id)
    ).all()
    return [
        UsuarioListItem(id=u.id, nombre=u.nombre, email=u.email,
                        rol=u.rol.value, estado=u.estado.value,
                        ultimo_login=u.ultimo_login)
        for u in rows
    ]


@router.post("", response_model=UsuarioListItem, status_code=status.HTTP_201_CREATED)
def crear_superadmin(data: SuperadminCreate, db: Session = Depends(get_db),
                     admin: Usuario = Depends(require_superadmin_2fa)):
    if db.scalar(select(Usuario).where(Usuario.email == data.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado")
    u = Usuario(email=data.email, nombre=data.nombre,
                rol=RolUsuario.superadmin, tenant_id=None, password_hash=None)
    db.add(u)
    db.flush()
    plano = generar_token_plano()
    db.add(PasswordReset(
        usuario_id=u.id, token_hash=sha256_hex(plano),
        expira_en=utcnow() + timedelta(hours=settings.RESET_TOKEN_HOURS),
    ))
    registrar_audit(db, admin.id, "alta_superadmin", "usuario", u.id,
                    {"email": data.email})
    db.commit()
    link = f"{settings.FRONTEND_ADMIN_URL}/recuperar?token={plano}"
    email_service.send_password_reset(u.email, link)
    return UsuarioListItem(id=u.id, nombre=u.nombre, email=u.email,
                           rol=u.rol.value, estado=u.estado.value,
                           ultimo_login=u.ultimo_login)


@router.post("/{usuario_id}/desactivar", response_model=MessageResponse)
def desactivar_superadmin(usuario_id: int, db: Session = Depends(get_db),
                          admin: Usuario = Depends(require_superadmin_2fa)):
    u = db.get(Usuario, usuario_id)
    if not u or u.rol != RolUsuario.superadmin:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Superadmin no encontrado")
    if u.id == admin.id:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "No puedes desactivar tu propia cuenta")
    if u.estado == EstadoUsuario.suspendido:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya está desactivado")
    if _superadmins_activos(db) <= 1:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "No puedes desactivar al último superadmin activo")
    u.estado = EstadoUsuario.suspendido
    revocar_todos_refresh(db, SujetoTipo.usuario, u.id)
    registrar_audit(db, admin.id, "desactivar_superadmin", "usuario", u.id)
    db.commit()
    return MessageResponse(detail=f"Superadmin {u.email} desactivado")


@router.post("/{usuario_id}/reactivar", response_model=MessageResponse)
def reactivar_superadmin(usuario_id: int, db: Session = Depends(get_db),
                         admin: Usuario = Depends(require_superadmin_2fa)):
    u = db.get(Usuario, usuario_id)
    if not u or u.rol != RolUsuario.superadmin:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Superadmin no encontrado")
    if u.estado == EstadoUsuario.activo:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya está activo")
    u.estado = EstadoUsuario.activo
    registrar_audit(db, admin.id, "reactivar_superadmin", "usuario", u.id)
    db.commit()
    return MessageResponse(detail=f"Superadmin {u.email} reactivado")
