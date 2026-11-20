from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_JWT_SECRET_DEV = "yapai-dev-secret-cambiar-en-produccion"
_SEED_PASSWORD_DEV = "Admin123!"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Yapai API"
    ENV: str = "development"
    PORT: int = 8000
    DEBUG: bool = True

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "yapai_db"

    # Override directo de la URL de conexión (ej. sqlite:///./yapai_dev.db para dev sin Docker)
    DATABASE_URL: str | None = None

    # JWT
    JWT_SECRET: str = _JWT_SECRET_DEV
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 30

    # Tokens de un solo uso
    ONBOARDING_TOKEN_HOURS: int = 72
    RESET_TOKEN_HOURS: int = 2

    # Email (si EMAIL_ENABLED=false se loguea el contenido en consola)
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@yapai.com"
    SMTP_TLS: bool = True

    # URLs de los frontends para armar links de correo
    FRONTEND_ADMIN_URL: str = "http://localhost:5173"
    FRONTEND_SOCIO_URL: str = "http://localhost:5174"
    FRONTEND_CLIENTE_URL: str = "http://localhost:5176"

    # CORS: orígenes permitidos separados por coma. Con cookies de sesión se
    # requieren orígenes explícitos (credentials + "*" están prohibidos por CORS).
    # En producción: dominios reales (nunca *).
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176"

    # Documentación OpenAPI: por defecto visible solo fuera de producción.
    # True/False explícito pisa el comportamiento por entorno.
    DOCS_ENABLED: bool | None = None

    # Proxies de confianza para X-Forwarded-For (coma-separados o "*").
    # "*" es seguro SOLO si el puerto de la app no se publica fuera de la red docker.
    TRUSTED_PROXIES: str = "127.0.0.1"

    # Observabilidad
    SENTRY_DSN: str = ""           # vacío = Sentry desactivado
    SENTRY_TRACES_SAMPLE: float = 0.1
    LOG_JSON: bool = False         # true en producción (access log JSON)

    # Semilla inicial
    SEED_ADMIN_EMAIL: str = "admin@yapai.com"
    SEED_ADMIN_PASSWORD: str = _SEED_PASSWORD_DEV
    # Datos de demostración (tenant demo, owner/cajero/cliente demo, kiosco demo).
    # NUNCA en producción — el validador lo bloquea.
    SEED_DEMO: bool = True
    # Kiosco demo público: device_token de una pantalla siempre habilitada para
    # demostración comercial (sin PIN). Vacío = deshabilitado. Debe pertenecer a
    # un tenant exclusivo de demo — sus datos son públicos y mutables.
    DEMO_DEVICE_TOKEN: str = ""

    # SaaS: registro público de socios — "auto" (activo al instante) | "manual" (requiere aprobación admin)
    SIGNUP_MODE: str = "auto"
    TRIAL_DIAS: int = 14
    # Billing: día de vencimiento de la factura del período y gracia antes de suspender
    FACTURA_VENCE_DIA: int = 10
    FACTURA_GRACIA_DIAS: int = 7
    # Offboarding: días que se conservan los datos tras pedir la baja
    BAJA_RETENCION_DIAS: int = 30
    # Jobs en background (expiración de pases + facturación). False en tests;
    # en producción multi-instancia corren como proceso aparte (app.jobs.runner).
    JOBS_ENABLED: bool = True
    # Rate limiting compartido entre workers (vacío = en memoria, single-instance)
    REDIS_URL: str | None = None

    # Web Push (VAPID) — generar con: py-vapid --gen. Vacío = push desactivado.
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:soporte@yapai.com"

    # OTP para login de clientes (segundo factor tras teléfono+CI).
    # provider "log" imprime el código en consola — SOLO desarrollo.
    # provider "webhook" hace POST a OTP_WEBHOOK_URL {telefono, codigo, ttl_minutos}
    # para integrar cualquier proveedor SMS/WhatsApp.
    CLIENTE_OTP_ENABLED: bool = True
    OTP_TTL_MINUTES: int = 5
    OTP_MAX_INTENTOS: int = 5
    # Segundos mínimos entre envíos de OTP al mismo destino (anti-spam/costo SMS)
    OTP_RESEND_COOLDOWN_SEG: int = 60
    OTP_PROVIDER: str = "log"
    OTP_WEBHOOK_URL: str = ""
    OTP_WEBHOOK_TOKEN: str = ""

    # Transporte de tokens: "bearer" (header), "cookie" (HttpOnly+SameSite) o "both".
    # "both" soporta navegadores (cookies) y clientes no-web (bearer) a la vez.
    AUTH_TRANSPORT: str = "both"
    # Dominio de las cookies ("." + dominio raíz) para compartirlas entre subdominios
    # (app./admin./api.ejemplo.com). Vacío = host-only (desarrollo local).
    COOKIE_DOMAIN: str = ""

    # Antifraude: alerta si un emisor (cajero/owner) otorga más de N puntos en 1h,
    # o un cliente recibe más de M en 24h. Registra en audit_log + métrica.
    FRAUDE_PUNTOS_EMISOR_HORA: int = 50_000
    FRAUDE_PUNTOS_CLIENTE_DIA: int = 20_000

    # Obligar 2FA a superadmins antes de usar el panel admin. Obligatorio en prod.
    REQUIRE_SUPERADMIN_2FA: bool = False

    # Stripe: webhook /api/v1/billing/stripe/webhook (firma HMAC verificada,
    # procesamiento idempotente). STRIPE_WEBHOOK_SECRET es obligatorio para usarlo.
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Cloudinary (Media / Subida de imágenes)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def docs_habilitados(self) -> bool:
        if self.DOCS_ENABLED is not None:
            return self.DOCS_ENABLED
        return self.ENV != "production"

    @model_validator(mode="after")
    def _produccion_segura(self) -> "Settings":
        """Fail-fast: en producción la configuración insegura aborta el arranque."""
        if self.ENV != "production":
            return self
        errores: list[str] = []
        if self.JWT_SECRET == _JWT_SECRET_DEV or len(self.JWT_SECRET) < 32:
            errores.append("JWT_SECRET debe ser propio y de >=32 caracteres")
        if self.DEBUG:
            errores.append("DEBUG debe ser false")
        if "*" in [o.strip() for o in self.CORS_ORIGINS.split(",")]:
            errores.append("CORS_ORIGINS no puede contener '*'")
        if not self.DATABASE_URL and self.POSTGRES_PASSWORD in ("", "postgres"):
            errores.append("POSTGRES_PASSWORD no puede ser el default")
        if self.SEED_ADMIN_PASSWORD == _SEED_PASSWORD_DEV:
            errores.append("SEED_ADMIN_PASSWORD no puede ser el default")
        if self.SEED_DEMO:
            errores.append("SEED_DEMO debe ser false (no sembrar datos demo)")
        if self.SIGNUP_MODE not in ("auto", "manual"):
            errores.append("SIGNUP_MODE debe ser 'auto' o 'manual'")
        if not self.CLIENTE_OTP_ENABLED:
            errores.append("CLIENTE_OTP_ENABLED debe ser true (login cliente requiere OTP)")
        elif self.OTP_PROVIDER != "webhook" or not self.OTP_WEBHOOK_URL:
            errores.append("OTP_PROVIDER debe ser 'webhook' con OTP_WEBHOOK_URL configurado")
        if not self.REQUIRE_SUPERADMIN_2FA:
            errores.append("REQUIRE_SUPERADMIN_2FA debe ser true (2FA obligatorio para admins)")
        if self.AUTH_TRANSPORT not in ("bearer", "cookie", "both"):
            errores.append("AUTH_TRANSPORT debe ser 'bearer', 'cookie' o 'both'")
        elif self.AUTH_TRANSPORT != "bearer" and not self.COOKIE_DOMAIN:
            errores.append("COOKIE_DOMAIN requerido cuando AUTH_TRANSPORT usa cookies")
        if errores:
            raise ValueError(
                "Configuración insegura para ENV=production: " + "; ".join(errores)
            )
        return self

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        extra="forbid",
    )


settings = Settings()
