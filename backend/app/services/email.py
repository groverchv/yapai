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
            # Truncado: el cuerpo puede contener links con tokens (reset, onboarding)
            logger.info("[EMAIL DEV] Para=%s | Asunto=%s\n%s…", to, subject, html[:300])
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

    # --- Ciclo de vida de facturación ---

    def send_factura_emitida(self, to: str, negocio: str, periodo: str,
                             monto: float, moneda: str, vence: str) -> bool:
        return self.send(
            to,
            f"YAPAI — Factura {periodo} emitida",
            f"""<h2>Hola, {negocio}</h2>
            <p>Tu factura del período <b>{periodo}</b> por <b>{monto:.2f} {moneda}</b>
            ya está disponible en tu portal de facturación.</p>
            <p>Fecha de vencimiento: <b>{vence}</b>. Después de esa fecha tu cuenta
            entra en mora y puede ser suspendida.</p>""",
        )

    def send_factura_vencida(self, to: str, negocio: str, periodo: str,
                             monto: float, moneda: str, gracia_dias: int) -> bool:
        return self.send(
            to,
            f"YAPAI — Factura {periodo} vencida",
            f"""<h2>Hola, {negocio}</h2>
            <p>Tu factura del período <b>{periodo}</b> por <b>{monto:.2f} {moneda}</b>
            venció sin pago registrado.</p>
            <p>Tienes <b>{gracia_dias} días de gracia</b> antes de que el acceso
            a tu portal y pantallas quede suspendido.</p>""",
        )

    def send_pago_recibido(self, to: str, negocio: str, periodo: str,
                           monto: float, moneda: str) -> bool:
        return self.send(
            to,
            f"YAPAI — Pago recibido ({periodo})",
            f"""<h2>Gracias, {negocio}</h2>
            <p>Registramos tu pago de <b>{monto:.2f} {moneda}</b> correspondiente
            al período <b>{periodo}</b>. Tu cuenta está al día.</p>""",
        )

    def send_trial_por_vencer(self, to: str, negocio: str, dias: int) -> bool:
        return self.send(
            to,
            f"YAPAI — Tu prueba termina en {dias} días",
            f"""<h2>Hola, {negocio}</h2>
            <p>Tu período de prueba termina en <b>{dias} días</b>. Para seguir usando
            YAPAI sin interrupciones, revisa tu plan en el portal de facturación.</p>""",
        )

    def send_tenant_suspendido(self, to: str, negocio: str, motivo: str) -> bool:
        return self.send(
            to,
            "YAPAI — Tu cuenta fue suspendida",
            f"""<h2>Hola, {negocio}</h2>
            <p>Tu cuenta de YAPAI fue <b>suspendida</b>. Motivo: {motivo}.</p>
            <p>Mientras dure la suspensión, tu portal y tus pantallas de kiosco
            no estarán disponibles. Regulariza tu situación para reactivarla.</p>""",
        )

    def send_tenant_reactivado(self, to: str, negocio: str) -> bool:
        return self.send(
            to,
            "YAPAI — Tu cuenta fue reactivada",
            f"""<h2>Hola, {negocio}</h2>
            <p>Tu cuenta de YAPAI está <b>activa</b> nuevamente. Tus usuarios ya
            pueden ingresar; las pantallas pedirán el PIN de caja otra vez.</p>""",
        )

    def send_alerta_fraude(self, to: str, negocio: str, tipo: str,
                           detalle: str) -> bool:
        return self.send(
            to,
            "YAPAI — Alerta de actividad inusual en puntos",
            f"""<h2>Hola, {negocio}</h2>
            <p>Detectamos emisión de puntos por encima de lo normal ({tipo}):
            {detalle}.</p>
            <p>Revisa los movimientos en tu portal. Si fue un error o abuso de
            un empleado, puedes suspenderlo desde Empleados.</p>""",
        )

    def send_baja_solicitada(self, to: str, negocio: str, dias_retencion: int) -> bool:
        return self.send(
            to,
            "YAPAI — Solicitud de baja recibida",
            f"""<h2>Hola, {negocio}</h2>
            <p>Recibimos tu solicitud de baja. Tu cuenta quedó suspendida y tus
            datos se conservarán durante <b>{dias_retencion} días</b>, por si
            cambias de opinión (escribe a soporte para cancelar la baja).</p>
            <p>Pasado ese plazo, la información de tu programa —clientes, puntos,
            premios y facturas— se eliminará de forma definitiva.</p>""",
        )

    def send_verificacion_email(self, to: str, link: str) -> bool:
        return self.send(
            to,
            "YAPAI — Confirma tu correo electrónico",
            f"""<p>Confirma que este correo es tuyo con este enlace:</p>
            <p><a href="{link}">{link}</a></p>
            <p>Si no creaste una cuenta en YAPAI, ignora este mensaje.</p>""",
        )


def emails_owner(db, tenant_id: int) -> list[str]:
    """Destinatarios de avisos de cuenta: owners activos del tenant, con
    email_contacto del tenant como respaldo."""
    from app.models import EstadoUsuario, RolUsuario, Tenant, Usuario
    from sqlalchemy import select

    mails = list(db.scalars(
        select(Usuario.email).where(
            Usuario.tenant_id == tenant_id,
            Usuario.rol == RolUsuario.owner,
            Usuario.estado == EstadoUsuario.activo,
        )
    ).all())
    if not mails:
        tenant = db.get(Tenant, tenant_id)
        if tenant and tenant.email_contacto:
            mails = [tenant.email_contacto]
    return mails


email_service = EmailService()
