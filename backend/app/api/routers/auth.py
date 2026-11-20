from datetime import timedelta

import jwt
from app.core.config import settings
from app.core.cookies import clear_auth_cookies, refresh_desde_request, set_auth_cookies
from app.core.deps import Subject, get_current_subject, get_current_usuario
from app.core.ratelimit import (
    cliente_login_limiter,
    cliente_otp_limiter,
    login_limiter,
    recovery_limiter,
    signup_limiter,
    token_limiter,
    totp_limiter,
)
from app.core.security import (
    decodificar_token,
    generar_token_plano,
    hash_secret,
    sha256_hex,
    utcnow,
    verify_secret,
    verify_secret_timing_safe,
)
from app.db.session import get_db
from app.models import (
    CategoriaNegocio,
    Cliente,
    ConfigPin,
    EstadoCliente,
    EstadoPantalla,
    EstadoTenant,
    EstadoUsuario,
    OnboardingToken,
    Pantalla,
    PasswordReset,
    Plan,
    RolUsuario,
    Sucursal,
    SujetoTipo,
    Tenant,
    TipoMovimiento,
    Usuario,
)
from app.schemas.auth import (
    ClienteLoginRequest,
    ClienteMe,
    ClienteOtpVerifyRequest,
    ClienteRegistroRequest,
    DemoInfo,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MeResponse,
    MessageResponse,
    OnboardingRequest,
    PlanPublico,
    RefreshRequest,
    ResetPasswordRequest,
    SignupRequest,
    SignupResponse,
    TokenPair,
    TotpCodigoIn,
    TotpDesactivarIn,
    TotpLoginIn,
    TotpSetupOut,
    UsuarioMe,
    VerificarEmailRequest,
)
from app.services import otp as otp_service
from app.services.audit import registrar_audit
from app.services.auth import (
    crear_onboarding_token,
    emitir_par_tokens,
    revocar_refresh,
    revocar_todos_refresh,
    rotar_refresh,
)
from app.services.campanas import asegurar_codigo_referido, generar_codigo_referido
from app.services.email import email_service
from app.services.planes import plan_inicial
from app.services.puntos import otorgar
from app.services.push import push_async
from app.services.totp import (
    nuevo_secret as totp_nuevo_secret,
)
from app.services.totp import (
    provisioning_uri as totp_uri,
)
from app.services.totp import (
    qr_svg as totp_qr_svg,
)
from app.services.totp import (
    verificar as totp_verificar,
)
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()


def _front_por_rol(rol: RolUsuario) -> str:
    return settings.FRONTEND_ADMIN_URL if rol == RolUsuario.superadmin else settings.FRONTEND_SOCIO_URL


def _crear_usuario_me(db: Session, usuario: Usuario) -> UsuarioMe:
    u = UsuarioMe.model_validate(usuario)
    u.email_verificado = usuario.email_verificado_en is not None
    if usuario.tenant_id:
        t = db.get(Tenant, usuario.tenant_id)
        if t:
            u.tenant_nombre = t.nombre_comercial
            u.tenant_logo = t.logo_url
    return u


@router.post("/login", response_model=LoginResponse,
             dependencies=[Depends(login_limiter)])
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Login de usuarios del sistema (superadmin, owner, cajero)."""
    usuario = db.scalar(select(Usuario).where(Usuario.email == data.email))
    if not usuario or not verify_secret_timing_safe(data.password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if usuario.estado != EstadoUsuario.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario suspendido")
    if usuario.totp_habilitado and usuario.totp_secret:
        # Paso 2: el cliente debe completar /login/2fa con su código TOTP
        pre = jwt.encode(
            {"sub": f"u:{usuario.id}", "type": "pre_2fa",
             "exp": utcnow() + timedelta(minutes=5)},
            settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM,
        )
        db.commit()
        return LoginResponse(requires_2fa=True, pre_token=pre)
    usuario.ultimo_login = utcnow()
    tokens = emitir_par_tokens(db, SujetoTipo.usuario, usuario.id, usuario.rol.value, usuario.tenant_id)
    db.commit()
    set_auth_cookies(response, tokens)
    return LoginResponse(tokens=tokens, usuario=_crear_usuario_me(db, usuario))


@router.post("/login/2fa", response_model=LoginResponse,
             dependencies=[Depends(totp_limiter)])
def login_2fa(data: TotpLoginIn, response: Response, db: Session = Depends(get_db)):
    """Segundo paso del login con 2FA: pre_token + código TOTP → tokens."""
    try:
        payload = decodificar_token(data.pre_token)
    except PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesión de verificación expirada — vuelve a iniciar sesión") from None
    if payload.get("type") != "pre_2fa":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
    usuario = db.get(Usuario, int(payload["sub"].split(":")[1]))
    if not usuario or not usuario.totp_habilitado or not usuario.totp_secret:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "2FA no configurado")
    if not totp_verificar(usuario.totp_secret, data.codigo):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Código incorrecto")
    usuario.ultimo_login = utcnow()
    tokens = emitir_par_tokens(db, SujetoTipo.usuario, usuario.id, usuario.rol.value, usuario.tenant_id)
    registrar_audit(db, usuario.id, "login_2fa", "usuario", usuario.id)
    db.commit()
    set_auth_cookies(response, tokens)
    return LoginResponse(tokens=tokens, usuario=_crear_usuario_me(db, usuario))


@router.post("/2fa/setup", response_model=TotpSetupOut)
def totp_setup(subject: Subject = Depends(get_current_subject),
               db: Session = Depends(get_db)):
    """Genera el secret TOTP (queda inactivo hasta verificar el primer código)."""
    usuario = subject.usuario
    if not usuario:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo usuarios del sistema")
    if usuario.totp_habilitado:
        raise HTTPException(status.HTTP_409_CONFLICT, "El 2FA ya está activo — desactívalo primero")
    usuario.totp_secret = totp_nuevo_secret()
    db.commit()
    uri = totp_uri(usuario.totp_secret, usuario.email)
    return TotpSetupOut(secret=usuario.totp_secret, provisioning_uri=uri, qr_svg=totp_qr_svg(uri))


@router.post("/2fa/habilitar", response_model=MessageResponse,
             dependencies=[Depends(totp_limiter)])
def totp_habilitar(data: TotpCodigoIn, subject: Subject = Depends(get_current_subject),
                   db: Session = Depends(get_db)):
    usuario = subject.usuario
    if not usuario or not usuario.totp_secret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Primero ejecuta /2fa/setup")
    if usuario.totp_habilitado:
        return MessageResponse(detail="El 2FA ya está activo")
    if not totp_verificar(usuario.totp_secret, data.codigo):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Código incorrecto — revisa que la hora del dispositivo sea automática")
    usuario.totp_habilitado = True
    registrar_audit(db, usuario.id, "habilitar_2fa", "usuario", usuario.id)
    db.commit()
    return MessageResponse(detail="2FA activado. Desde tu próximo login te pediremos el código.")


@router.post("/2fa/deshabilitar", response_model=MessageResponse,
             dependencies=[Depends(totp_limiter)])
def totp_deshabilitar(data: TotpDesactivarIn,
                      subject: Subject = Depends(get_current_subject),
                      db: Session = Depends(get_db)):
    usuario = subject.usuario
    if not usuario:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo usuarios del sistema")
    if not usuario.password_hash or not verify_secret(data.password, usuario.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Contraseña incorrecta")
    usuario.totp_secret = None
    usuario.totp_habilitado = False
    registrar_audit(db, usuario.id, "deshabilitar_2fa", "usuario", usuario.id)
    db.commit()
    return MessageResponse(detail="2FA desactivado")


@router.post("/cliente/login", response_model=LoginResponse,
             dependencies=[Depends(cliente_login_limiter)])
def login_cliente(data: ClienteLoginRequest, response: Response, db: Session = Depends(get_db)):
    """Login del cliente: teléfono + CI. Con CLIENTE_OTP_ENABLED devuelve un
    reto OTP que se verifica en /cliente/otp/verificar."""
    cliente = db.scalar(
        select(Cliente).where(Cliente.telefono == data.telefono, Cliente.ci == data.ci)
    )
    if not cliente or cliente.estado != EstadoCliente.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if settings.CLIENTE_OTP_ENABLED:
        otp_service.crear_otp(db, cliente)
        db.commit()
        return LoginResponse(otp_requerido=True, otp_ttl_minutos=settings.OTP_TTL_MINUTES)
    asegurar_codigo_referido(db, cliente)  # backfill para clientes anteriores a referidos
    tokens = emitir_par_tokens(db, SujetoTipo.cliente, cliente.id, "cliente")
    db.commit()
    set_auth_cookies(response, tokens)
    return LoginResponse(tokens=tokens, cliente=ClienteMe.model_validate(cliente))


@router.post("/cliente/otp/verificar", response_model=LoginResponse,
             dependencies=[Depends(cliente_otp_limiter)])
def verificar_otp_cliente(data: ClienteOtpVerifyRequest, response: Response, db: Session = Depends(get_db)):
    """Segundo paso del login: valida el código OTP y emite los tokens."""
    cliente = db.scalar(
        select(Cliente).where(Cliente.telefono == data.telefono, Cliente.ci == data.ci)
    )
    if not cliente or cliente.estado != EstadoCliente.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if not otp_service.verificar_otp(db, cliente, data.codigo):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Código incorrecto o expirado")
    asegurar_codigo_referido(db, cliente)
    tokens = emitir_par_tokens(db, SujetoTipo.cliente, cliente.id, "cliente")
    registrar_audit(db, None, "login_cliente_otp", "cliente", cliente.id)
    db.commit()
    set_auth_cookies(response, tokens)
    return LoginResponse(tokens=tokens, cliente=ClienteMe.model_validate(cliente))


@router.post("/cliente/registro", response_model=LoginResponse,
             dependencies=[Depends(signup_limiter)])
def registro_cliente(data: ClienteRegistroRequest, response: Response, db: Session = Depends(get_db)):
    """Registro del cliente desde la app. Con OTP habilitado son DOS fases:

    1. Sin `codigo`: valida unicidad y envía OTP al teléfono → `otp_requerido`.
    2. Con `codigo`: verifica que el registrante posee el número → crea la
       cuenta y emite tokens. Sin esto cualquiera podría registrar el
       CI+teléfono de otra persona.
    """
    tel = data.telefono.strip().replace(" ", "").replace("-", "")
    ci = data.ci.strip().replace(" ", "").replace("-", "")
    if db.scalar(select(Cliente).where(Cliente.ci == ci)):
        raise HTTPException(status.HTTP_409_CONFLICT, "La cédula de identidad ya está registrada")
    if db.scalar(select(Cliente).where(Cliente.telefono == tel)):
        raise HTTPException(status.HTTP_409_CONFLICT, "El teléfono ya está registrado")

    if settings.CLIENTE_OTP_ENABLED:
        if not data.codigo:
            otp_service.crear_otp_telefono(db, tel)
            db.commit()
            return LoginResponse(otp_requerido=True,
                                 otp_ttl_minutos=settings.OTP_TTL_MINUTES)
        if not otp_service.verificar_otp_telefono(db, tel, data.codigo):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                                "Código inválido o expirado. Solicita uno nuevo.")

    referidor = None
    if data.codigo_referido and data.codigo_referido.strip():
        referidor = db.scalar(
            select(Cliente).where(
                Cliente.codigo_referido == data.codigo_referido.strip().upper(),
                Cliente.estado == EstadoCliente.activo,
            )
        )

    cliente = Cliente(
        nombre=data.nombre.strip(),
        ci=ci,
        telefono=tel,
        estado=EstadoCliente.activo,
        codigo_referido=generar_codigo_referido(db),
        referido_por_id=referidor.id if referidor else None,
        saldo_puntos=0,
    )
    db.add(cliente)
    db.flush()

    # Puntos de bienvenida por registro desde la app
    otorgar(
        db, cliente, 500, TipoMovimiento.registro,
        detalle={"origen": "app_bienvenida"},
    )

    # Bonus de referido (consistente con el kiosco): lo paga el tenant donde
    # se registró el referidor — si es una cuenta global sin tenant, no hay
    # patrocinador y no se emite bonus.
    tenant_ref = (
        db.get(Tenant, referidor.tenant_registro_id)
        if referidor and referidor.tenant_registro_id else None
    )
    if referidor and tenant_ref:
        otorgar(
            db, referidor, tenant_ref.puntos_referido, TipoMovimiento.referido,
            tenant_id=tenant_ref.id,
            detalle={"referido_cliente_id": cliente.id, "origen": "app"},
        )

    tokens = emitir_par_tokens(db, SujetoTipo.cliente, cliente.id, "cliente")
    db.commit()
    set_auth_cookies(response, tokens)
    if referidor and tenant_ref:
        push_async(referidor.id, f"+{tenant_ref.puntos_referido} pts por tu referido",
                   f"{cliente.nombre} se registró con tu código", "/billetera")
    return LoginResponse(tokens=tokens, cliente=ClienteMe.model_validate(cliente))


@router.get("/planes", response_model=list[PlanPublico])
def planes_publicos(db: Session = Depends(get_db)):
    """Planes activos para la landing pública (sin auth)."""
    rows = db.scalars(
        select(Plan).where(Plan.activo == True).order_by(Plan.orden, Plan.id)  # noqa: E712
    ).all()
    return [PlanPublico(
        id=p.id, slug=p.slug, nombre=p.nombre, descripcion=p.descripcion,
        precio_mensual=float(p.precio_mensual), moneda=p.moneda,
        max_sucursales=p.max_sucursales, max_pantallas=p.max_pantallas,
        max_clientes=p.max_clientes, max_empleados=p.max_empleados,
        ruleta_habilitada=p.ruleta_habilitada,
    ) for p in rows]


@router.get("/demo", response_model=DemoInfo)
def demo_publico(db: Session = Depends(get_db)):
    """Info del kiosco demo público para la landing (sin auth).

    Solo expone el device_token si el demo está configurado y su tenant activo.
    """
    if not settings.DEMO_DEVICE_TOKEN:
        return DemoInfo(disponible=False)
    pantalla = db.scalar(
        select(Pantalla).where(Pantalla.device_token == settings.DEMO_DEVICE_TOKEN))
    if not pantalla or pantalla.estado == EstadoPantalla.bloqueada:
        return DemoInfo(disponible=False)
    sucursal = db.get(Sucursal, pantalla.sucursal_id)
    tenant = db.get(Tenant, sucursal.tenant_id) if sucursal else None
    if not tenant or tenant.estado != EstadoTenant.activo:
        return DemoInfo(disponible=False)
    return DemoInfo(disponible=True, device_token=pantalla.device_token,
                    comercio=tenant.nombre_comercial)


@router.post("/signup", response_model=SignupResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(signup_limiter)])
def signup(data: SignupRequest, response: Response, db: Session = Depends(get_db)):
    """Registro self-serve: crea tenant en trial + owner con su propia clave.

    SIGNUP_MODE=auto → activo al instante (devuelve tokens).
    SIGNUP_MODE=manual → tenant suspendido hasta aprobación del admin.
    """
    if db.scalar(select(Usuario).where(Usuario.email == data.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado")
    if data.categoria_id and not db.get(CategoriaNegocio, data.categoria_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Categoría inválida")

    aprobado = settings.SIGNUP_MODE == "auto"
    plan = plan_inicial(db)
    tenant = Tenant(
        nombre_comercial=data.negocio_nombre,
        nit_rut=f"SB-{generar_token_plano()[:12]}",
        email_contacto=data.email, telefono=data.telefono,
        categoria_id=data.categoria_id,
        plan_id=plan.id if plan else None,
        trial_fin=utcnow() + timedelta(days=settings.TRIAL_DIAS),
        estado=EstadoTenant.activo if aprobado else EstadoTenant.suspendido,
    )
    db.add(tenant)
    db.flush()
    owner = Usuario(
        email=data.email, nombre=data.owner_nombre, rol=RolUsuario.owner,
        tenant_id=tenant.id, password_hash=hash_secret(data.password),
    )
    db.add(owner)
    db.add(ConfigPin(tenant_id=tenant.id))
    registrar_audit(db, None, "signup_socio", "tenant", tenant.id,
                    {"modo": settings.SIGNUP_MODE, "plan": plan.slug if plan else None})
    db.commit()

    email_service.send_welcome(data.email, data.negocio_nombre,
                               settings.TRIAL_DIAS, pendiente=not aprobado)
    if not aprobado:
        return SignupResponse(aprobado=False)
    # Verificación de correo (no bloquea el primer acceso — banner en el portal)
    token_verif = crear_onboarding_token(db, data.email, tenant.id)
    db.commit()
    email_service.send_verificacion_email(
        data.email, f"{settings.FRONTEND_SOCIO_URL}/verificar?token={token_verif}")
    tokens = emitir_par_tokens(db, SujetoTipo.usuario, owner.id, owner.rol.value, tenant.id)
    db.commit()
    set_auth_cookies(response, tokens)
    return SignupResponse(aprobado=True, tokens=tokens, usuario=_crear_usuario_me(db, owner))


@router.post("/refresh", response_model=TokenPair,
             dependencies=[Depends(token_limiter)])
def refresh(request: Request, response: Response, data: RefreshRequest | None = None,
            db: Session = Depends(get_db)):
    """Rota el refresh token. Bearer clients lo mandan en el body; los
    navegadores lo llevan en la cookie HttpOnly (body vacío)."""
    token = (data.refresh_token if data else None) or refresh_desde_request(request)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token requerido")
    tokens, _, _ = rotar_refresh(db, token)
    db.commit()
    set_auth_cookies(response, tokens)
    return tokens


@router.post("/logout", response_model=MessageResponse,
             dependencies=[Depends(token_limiter)])
def logout(request: Request, response: Response, data: LogoutRequest | None = None,
           db: Session = Depends(get_db)):
    token = (data.refresh_token if data else None) or refresh_desde_request(request)
    if token:
        revocar_refresh(db, token)
    clear_auth_cookies(response)
    db.commit()
    return MessageResponse(detail="Sesión terminada")


@router.get("/me", response_model=MeResponse)
def me(subject: Subject = Depends(get_current_subject), db: Session = Depends(get_db)):
    if subject.tipo == "usuario":
        return MeResponse(tipo="usuario", usuario=_crear_usuario_me(db, subject.usuario))
    return MeResponse(tipo="cliente", cliente=ClienteMe.model_validate(subject.cliente))


@router.post("/forgot-password", response_model=MessageResponse,
             dependencies=[Depends(recovery_limiter)])
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Siempre responde igual para no revelar si el email existe."""
    usuario = db.scalar(select(Usuario).where(Usuario.email == data.email))
    if usuario:
        plano = generar_token_plano()
        db.add(PasswordReset(
            usuario_id=usuario.id,
            token_hash=sha256_hex(plano),
            expira_en=utcnow() + timedelta(hours=settings.RESET_TOKEN_HOURS),
        ))
        registrar_audit(db, None, "solicitud_reset_password", "usuario", usuario.id)
        db.commit()
        link = f"{_front_por_rol(usuario.rol)}/recuperar?token={plano}"
        email_service.send_password_reset(usuario.email, link)
    return MessageResponse(detail="Si el correo existe, recibirás un enlace de recuperación")


@router.post("/reset-password", response_model=MessageResponse,
             dependencies=[Depends(recovery_limiter)])
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    row = db.scalar(select(PasswordReset).where(PasswordReset.token_hash == sha256_hex(data.token)))
    if not row or row.usado_en or row.expira_en.replace(tzinfo=row.expira_en.tzinfo or utcnow().tzinfo) < utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")
    usuario = db.get(Usuario, row.usuario_id)
    usuario.password_hash = hash_secret(data.password)
    row.usado_en = utcnow()
    revocar_todos_refresh(db, SujetoTipo.usuario, usuario.id)
    registrar_audit(db, usuario.id, "reset_password", "usuario", usuario.id)
    db.commit()
    return MessageResponse(detail="Contraseña actualizada")


@router.post("/onboarding", response_model=MessageResponse,
             dependencies=[Depends(recovery_limiter)])
def onboarding(data: OnboardingRequest, db: Session = Depends(get_db)):
    """El Owner establece su contraseña con el link único recibido por email."""
    row = db.scalar(select(OnboardingToken).where(OnboardingToken.token_hash == sha256_hex(data.token)))
    if not row or row.usado_en or row.expira_en.replace(tzinfo=row.expira_en.tzinfo or utcnow().tzinfo) < utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")
    usuario = db.scalar(
        select(Usuario).where(Usuario.email == row.email, Usuario.tenant_id == row.tenant_id)
    )
    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")
    usuario.password_hash = hash_secret(data.password)
    usuario.estado = EstadoUsuario.activo
    # El link llegó al correo → el email queda verificado de paso
    usuario.email_verificado_en = utcnow()
    row.usado_en = utcnow()
    registrar_audit(db, usuario.id, "onboarding_completado", "tenant", row.tenant_id)
    db.commit()
    return MessageResponse(detail="Cuenta activada. Ya puedes iniciar sesión")


@router.post("/verificar-email", response_model=MessageResponse,
             dependencies=[Depends(recovery_limiter)])
def verificar_email(data: VerificarEmailRequest, db: Session = Depends(get_db)):
    """Confirma la titularidad del correo con el link enviado al signup.
    Reusa OnboardingToken (mismo mecanismo de token de un solo uso)."""
    row = db.scalar(
        select(OnboardingToken).where(OnboardingToken.token_hash == sha256_hex(data.token)))
    if not row or row.usado_en or row.expira_en.replace(
            tzinfo=row.expira_en.tzinfo or utcnow().tzinfo) < utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Token inválido o expirado")
    usuario = db.scalar(
        select(Usuario).where(Usuario.email == row.email,
                              Usuario.tenant_id == row.tenant_id))
    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Token inválido o expirado")
    usuario.email_verificado_en = utcnow()
    row.usado_en = utcnow()
    registrar_audit(db, usuario.id, "email_verificado", "usuario", usuario.id)
    db.commit()
    return MessageResponse(detail="Correo verificado correctamente")


@router.post("/reenviar-verificacion", response_model=MessageResponse,
             dependencies=[Depends(recovery_limiter)])
def reenviar_verificacion(usuario: Usuario = Depends(get_current_usuario),
                          db: Session = Depends(get_db)):
    """Reenvía el link de verificación al correo del usuario autenticado."""
    if usuario.email_verificado_en:
        return MessageResponse(detail="Tu correo ya está verificado")
    token = crear_onboarding_token(db, usuario.email, usuario.tenant_id)
    db.commit()
    front = _front_por_rol(usuario.rol)
    email_service.send_verificacion_email(
        usuario.email, f"{front}/verificar?token={token}")
    return MessageResponse(detail="Si el correo es válido recibirás un nuevo enlace")
