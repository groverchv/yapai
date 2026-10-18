from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# --- Requests ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ClienteLoginRequest(BaseModel):
    telefono: str = Field(min_length=4, max_length=30)
    ci: str = Field(min_length=3, max_length=50)


class ClienteRegistroRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    telefono: str = Field(min_length=4, max_length=30)
    ci: str = Field(min_length=3, max_length=50)
    codigo_referido: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class OnboardingRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class SignupRequest(BaseModel):
    """Registro self-serve de un socio comercial."""
    negocio_nombre: str = Field(min_length=2, max_length=200)
    owner_nombre: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    telefono: str | None = Field(default=None, max_length=50)
    categoria_id: int | None = None


# --- Responses ---

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos del access token


class UsuarioMe(BaseModel):
    id: int
    email: str
    nombre: str
    rol: str
    tenant_id: int | None
    totp_habilitado: bool = False

    class Config:
        from_attributes = True


class ClienteMe(BaseModel):
    id: int
    nombre: str
    ci: str
    telefono: str
    saldo_puntos: int
    puntos_congelados: int
    codigo_referido: str | None = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    tokens: TokenPair | None = None
    usuario: UsuarioMe | None = None
    cliente: ClienteMe | None = None
    # 2FA: cuando el usuario tiene TOTP, el login devuelve pre_token en vez de tokens
    requires_2fa: bool = False
    pre_token: str | None = None


class TotpSetupOut(BaseModel):
    secret: str
    provisioning_uri: str
    qr_svg: str


class TotpCodigoIn(BaseModel):
    codigo: str = Field(min_length=6, max_length=8)


class TotpLoginIn(BaseModel):
    pre_token: str
    codigo: str = Field(min_length=6, max_length=8)


class TotpDesactivarIn(BaseModel):
    password: str


class PlanPublico(BaseModel):
    """Plan visible en la landing pública."""
    id: int
    slug: str
    nombre: str
    descripcion: str | None
    precio_mensual: float
    moneda: str
    max_sucursales: int
    max_pantallas: int
    max_clientes: int
    max_empleados: int
    ruleta_habilitada: bool


class SignupResponse(BaseModel):
    """auto → tokens listos para entrar; manual → pendiente de aprobación."""
    aprobado: bool
    tokens: TokenPair | None = None
    usuario: UsuarioMe | None = None


class MessageResponse(BaseModel):
    detail: str


class MeResponse(BaseModel):
    tipo: str  # 'usuario' | 'cliente'
    usuario: UsuarioMe | None = None
    cliente: ClienteMe | None = None
