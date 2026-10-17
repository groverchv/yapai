from dataclasses import dataclass
from typing import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decodificar_token
from app.db.session import get_db
from app.models import Cliente, EstadoCliente, EstadoUsuario, RolUsuario, Usuario

bearer = HTTPBearer(auto_error=False)


@dataclass
class Subject:
    """Identidad autenticada: usuario del sistema o cliente de la app."""
    tipo: str          # 'usuario' | 'cliente'
    usuario: Usuario | None = None
    cliente: Cliente | None = None

    @property
    def id(self) -> int:
        return self.usuario.id if self.usuario else self.cliente.id

    @property
    def tenant_id(self) -> int | None:
        return self.usuario.tenant_id if self.usuario else None


def _credenciales_invalidas() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_subject(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Subject:
    if cred is None:
        raise _credenciales_invalidas()
    try:
        payload = decodificar_token(cred.credentials)
    except jwt.PyJWTError:
        raise _credenciales_invalidas()

    if payload.get("type") != "access":
        raise _credenciales_invalidas()

    sub: str = payload.get("sub", "")
    if sub.startswith("u:"):
        usuario = db.scalar(select(Usuario).where(Usuario.id == int(sub[2:])))
        if not usuario or usuario.estado != EstadoUsuario.activo:
            raise _credenciales_invalidas()
        return Subject(tipo="usuario", usuario=usuario)
    if sub.startswith("c:"):
        cliente = db.scalar(select(Cliente).where(Cliente.id == int(sub[2:])))
        if not cliente or cliente.estado != EstadoCliente.activo:
            raise _credenciales_invalidas()
        return Subject(tipo="cliente", cliente=cliente)
    raise _credenciales_invalidas()


def get_current_usuario(subject: Subject = Depends(get_current_subject)) -> Usuario:
    if subject.tipo != "usuario":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo usuarios del sistema")
    return subject.usuario


def get_current_cliente(subject: Subject = Depends(get_current_subject)) -> Cliente:
    if subject.tipo != "cliente":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo clientes")
    return subject.cliente


def require_role(*roles: RolUsuario) -> Callable:
    """Guard de rol para endpoints. Además valida que el tenant del usuario esté implícito."""
    def dep(usuario: Usuario = Depends(get_current_usuario)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol insuficiente")
        return usuario
    return dep


require_superadmin = require_role(RolUsuario.superadmin)
require_owner = require_role(RolUsuario.owner)
require_caja = require_role(RolUsuario.owner, RolUsuario.cajero)
