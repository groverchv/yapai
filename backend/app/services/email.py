import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger("yapai.email")


class EmailService:
    """Envío de correos transaccionales. En dev (EMAIL_ENABLED=false) loguea el contenido."""

    def send(self, to: str, subject: str, html: str) -> bool:
        if not settings.EMAIL_ENABLED:
            logger.info("[EMAIL DEV] Para=%s | Asunto=%s\n%s", to, subject, html)
            return True
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True

    def send_onboarding(self, to: str, nombre_socio: str, link: str) -> bool:
        return self.send(
            to,
            "Bienvenido a YAPAI — Activa tu cuenta",
            f"""<h2>Hola, {nombre_socio}</h2>
            <p>Tu comercio fue afiliado a YAPAI. Establece tu contraseña con este enlace (vence en {settings.ONBOARDING_TOKEN_HOURS}h):</p>
            <p><a href="{link}">{link}</a></p>""",
        )

    def send_welcome(self, to: str, nombre_socio: str, trial_dias: int, pendiente: bool = False) -> bool:
        estado = ("Tu cuenta está <b>pendiente de aprobación</b>: te avisaremos cuando el equipo YAPAI la active."
                  if pendiente else
                  f"Tienes <b>{trial_dias} días de prueba</b> con todos los límites del plan Starter.")
        return self.send(
            to,
            "Bienvenido a YAPAI — Tu comercio ya está registrado",
            f"""<h2>Hola, {nombre_socio}</h2>
            <p>Tu programa de fidelización ya existe. {estado}</p>
            <p>Entra a tu portal, crea tu sucursal y tu primer premio para empezar.</p>""",
        )

    def send_password_reset(self, to: str, link: str) -> bool:
        return self.send(
            to,
            "YAPAI — Recuperación de contraseña",
            f"""<p>Usa este enlace para restablecer tu contraseña (vence en {settings.RESET_TOKEN_HOURS}h):</p>
            <p><a href="{link}">{link}</a></p>
            <p>Si no lo solicitaste, ignora este correo.</p>""",
        )


email_service = EmailService()
