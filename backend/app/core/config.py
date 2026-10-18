from pathlib import Path
from pydantic_settings import BaseSettings

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

    POSTGREST_URL: str = "http://localhost:3000"

    # JWT
    JWT_SECRET: str = "yapai-dev-secret-cambiar-en-produccion"
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

    # CORS: orígenes permitidos separados por coma ("*" solo en desarrollo)
    CORS_ORIGINS: str = "*"

    # Observabilidad
    SENTRY_DSN: str = ""           # vacío = Sentry desactivado
    SENTRY_TRACES_SAMPLE: float = 0.1
    LOG_JSON: bool = False         # true en producción (access log JSON)

    # Semilla inicial
    SEED_ADMIN_EMAIL: str = "admin@yapai.com"
    SEED_ADMIN_PASSWORD: str = "Admin123!"

    # SaaS: registro público de socios — "auto" (activo al instante) | "manual" (requiere aprobación admin)
    SIGNUP_MODE: str = "auto"
    TRIAL_DIAS: int = 14
    # Billing: día de vencimiento de la factura del período y gracia antes de suspender
    FACTURA_VENCE_DIA: int = 10
    FACTURA_GRACIA_DIAS: int = 7
    # Jobs en background (expiración de pases + facturación). False en tests.
    JOBS_ENABLED: bool = True
    # Rate limiting compartido entre workers (vacío = en memoria, single-instance)
    REDIS_URL: str | None = None

    # Pasarela de Pagos Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    # Cloudinary (Media / Subida de imágenes)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent / ".env")
        extra = "allow"

settings = Settings()
