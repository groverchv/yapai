"""Firma para subidas directas a Cloudinary.

El frontend sube el archivo directamente a Cloudinary (sin pasar por nuestro
server). Nosotros solo firmamos los parámetros: carpeta por tenant, timestamp
y transformaciones permitidas. Sin credenciales configuradas → 503 en el router.
"""
import hashlib
import time

from app.core.config import settings


def firma_disponible() -> bool:
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )


def generar_firma(tenant_id: int | None = None, carpeta: str = "logos") -> dict:
    """Parámetros firmados para `POST https://api.cloudinary.com/v1_1/{cloud}/image/upload`.

    El signature es SHA-1 de los params ordenados alfabéticamente + secret.
    """
    timestamp = int(time.time())
    if tenant_id:
        folder = f"yapai/tenants/{tenant_id}/{carpeta}"
    else:
        folder = f"yapai/{carpeta}"
    params = {"folder": folder, "timestamp": str(timestamp)}
    base = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    signature = hashlib.sha1(f"{base}{settings.CLOUDINARY_API_SECRET}".encode()).hexdigest()
    return {
        "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
        "api_key": settings.CLOUDINARY_API_KEY,
        "timestamp": timestamp,
        "folder": folder,
        "signature": signature,
    }
