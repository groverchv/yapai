"""Servicio de gestión de medios (imágenes) con Cloudinary."""
import cloudinary
import cloudinary.uploader
from app.core.config import settings

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
