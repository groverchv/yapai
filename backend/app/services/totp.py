"""2FA TOTP para superadmin/owner (Google Authenticator / compatibles)."""
import pyotp
import qrcode
from qrcode.image.svg import SvgPathImage

ISSUER = "YAPAI"


def nuevo_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def qr_svg(uri: str) -> str:
    return qrcode.make(uri, image_factory=SvgPathImage).to_string(encoding="unicode")


def verificar(secret: str, codigo: str) -> bool:
    """valid_window=1 tolera ±30s de desfase de reloj."""
    return pyotp.TOTP(secret).verify(codigo.strip(), valid_window=1)
