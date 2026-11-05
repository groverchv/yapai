from app.core.deps import require_owner
from app.core.security import hash_secret, verify_secret
from app.db.session import get_db
from app.models import SujetoTipo, Tenant, Usuario
from app.schemas.auth import MessageResponse
from app.schemas.socio import CambiarPasswordIn, PerfilOut, PerfilUpdate
from app.services.auth import revocar_todos_refresh
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_owner)])


@router.get("", response_model=PerfilOut)
def mi_perfil(usuario: Usuario = Depends(require_owner), db: Session = Depends(get_db)):
    tenant = db.get(Tenant, usuario.tenant_id)
    return PerfilOut(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        rol=usuario.rol.value,
        tenant_id=usuario.tenant_id,
        tenant_nombre=tenant.nombre_comercial if tenant else "",
        logo_url=tenant.logo_url if tenant else None,
        telefono=tenant.telefono if tenant else None,
        email_contacto=tenant.email_contacto if tenant else None,
    )


@router.patch("", response_model=PerfilOut)
def actualizar_perfil(data: PerfilUpdate, usuario: Usuario = Depends(require_owner),
                      db: Session = Depends(get_db)):
    usuario.nombre = data.nombre
    tenant = db.get(Tenant, usuario.tenant_id)
    if tenant:
        if data.tenant_nombre is not None:
            tenant.nombre_comercial = data.tenant_nombre
        if data.logo_url is not None:
            tenant.logo_url = data.logo_url
        if data.telefono is not None:
            tenant.telefono = data.telefono
    db.commit()
    return mi_perfil(usuario, db)


@router.post("/cambiar-password", response_model=MessageResponse)
def cambiar_password(data: CambiarPasswordIn, usuario: Usuario = Depends(require_owner),
                     db: Session = Depends(get_db)):
    if not usuario.password_hash or not verify_secret(data.password_actual, usuario.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La contraseña actual es incorrecta")
    usuario.password_hash = hash_secret(data.password_nuevo)
    revocar_todos_refresh(db, SujetoTipo.usuario, usuario.id)
    db.commit()
    return MessageResponse(detail="Contraseña actualizada; inicia sesión nuevamente")
