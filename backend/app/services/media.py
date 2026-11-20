"""Servicio de gestión de medios (imágenes) con Cloudinary."""
import io

import cloudinary
import cloudinary.uploader
from app.core.config import settings

TAMANO_MAX_BYTES = 5 * 1024 * 1024  # 5 MB

# Firmas de bytes (magic numbers) de formatos de imagen permitidos.
# Se valida el contenido real — no el Content-Type que declara el cliente.
_FIRMAS: tuple[bytes, ...] = (
    b"\xff\xd8\xff",              # JPEG
    b"\x89PNG\r\n\x1a\n",          # PNG
    b"GIF87a", b"GIF89a",          # GIF
    b"RIFF",                       # WebP (RIFF....WEBP, verificado abajo)
)


def validar_imagen(data: bytes) -> str | None:
    """Devuelve el formato detectado ('jpeg'|'png'|'gif'|'webp') o None.

    SVG queda explícitamente fuera: es XML scriptable (XSS almacenado).
    """
    if len(data) > TAMANO_MAX_BYTES:
        raise ValueError(f"La imagen supera el máximo de {TAMANO_MAX_BYTES // 1024 // 1024} MB")
    if data[:15].lower().startswith((b"<?xml", b"<svg")) or b"<svg" in data[:512].lower():
        return None
    for firma in _FIRMAS:
        if data.startswith(firma):
            if firma == b"RIFF" and data[8:12] != b"WEBP":
                continue
            return "ok"
    return None


# Configurar Cloudinary si las credenciales están presentes
if settings.CLOUDINARY_CLOUD_NAME:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def subir_imagen(archivo, folder: str = "yapai", public_id: str | None = None) -> str:
    """Sube una imagen a Cloudinary y devuelve su URL segura (HTTPS).

    :param archivo: Archivo binario, path, o base64
    :param folder: Carpeta en Cloudinary (ej: "yapai/logos", "yapai/premios")
    :param public_id: Identificador opcional
    :return: URL segura de la imagen
    """
    if not settings.CLOUDINARY_CLOUD_NAME:
        raise ValueError("Cloudinary no está configurado en .env")

    params = {
        "folder": folder,
        "resource_type": "image",
    }
    if public_id:
        params["public_id"] = public_id

    respuesta = cloudinary.uploader.upload(archivo, **params)
    return respuesta.get("secure_url") or respuesta.get("url")


def leer_imagen_validada(data: bytes) -> io.BytesIO:
    """Valida bytes de imagen y devuelve un stream listo para subir."""
    if not validar_imagen(data):
        raise ValueError("El archivo no es una imagen válida (JPG, PNG, WebP o GIF, sin SVG)")
    return io.BytesIO(data)
