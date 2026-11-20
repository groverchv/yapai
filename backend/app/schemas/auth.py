from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _password_fuerte(v: str) -> str:
    """Política de contraseñas para usuarios del sistema (owner/cajero/admin):
    >=12 caracteres, al menos una letra y un dígito."""
    if len(v) < 12:
        raise ValueError("La contraseña debe tener al menos 12 caracteres")
    if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
        raise ValueError("La contraseña debe incluir letras y dígitos")
    return v


# --- Requests ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ClienteLoginRequest(BaseModel):
    telefono: str = Field(min_length=4, max_length=30)
    ci: str = Field(min_length=3, max_length=50)


class ClienteOtpVerifyRequest(BaseModel):
    telefono: str = Field(min_length=4, max_length=30)
    ci: str = Field(min_length=3, max_length=50)
    codigo: str = Field(min_length=6, max_length=6)


class ClienteRegistroRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=160)
    telefono: str = Field(min_length=4, max_length=30)
    ci: str = Field(min_length=3, max_length=50)
    codigo_referido: str | None = None
    # 2da fase: OTP del teléfono (vacío en la 1ra llamada → envía el código)
    codigo: str | None = Field(default=None, min_length=4, max_length=10)


class RefreshRequest(BaseModel):
    refresh_token: str | None = None  # cookie HttpOnly en navegadores


class LogoutRequest(BaseModel):
    refresh_token: str | None = None  # cookie HttpOnly en navegadores


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=12, max_length=128)

    _v = field_validator("password")(_password_fuerte)


class OnboardingRequest(BaseModel):
    token: str
    password: str = Field(min_length=12, max_length=128)

    _v = field_validator("password")(_password_fuerte)


class VerificarEmailRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class SignupRequest(BaseModel):
    """Registro self-serve de un socio comercial."""
    negocio_nombre: str = Field(min_length=2, max_length=200)
    owner_nombre: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    telefono: str | None = Field(default=None, max_length=50)
    categoria_id: int | None = None

    _v = field_validator("password")(_password_fuerte)


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
    email_verificado: bool = False
    tenant_nombre: str | None = None
    tenant_logo: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ClienteMe(BaseModel):
    id: int
    nombre: str
    ci: str
    telefono: str
    saldo_puntos: int
    puntos_congelados: int
    codigo_referido: str | None = None
    foto_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    tokens: TokenPair | None = None
    usuario: UsuarioMe | None = None
    cliente: ClienteMe | None = None
    # 2FA: cuando el usuario tiene TOTP, el login devuelve pre_token en vez de tokens
    requires_2fa: bool = False
    pre_token: str | None = None
    # OTP cliente: cuando CLIENTE_OTP_ENABLED, login devuelve esto en vez de tokens
    otp_requerido: bool = False
    otp_ttl_minutos: int | None = None


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


class DemoInfo(BaseModel):
    disponible: bool
    device_token: str | None = None
    comercio: str | None = None


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
