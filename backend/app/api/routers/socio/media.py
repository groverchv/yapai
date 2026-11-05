"""Router de carga de medios e imágenes para el portal socio (Cloudinary)."""
from app.core.deps import require_owner
from app.db.session import get_db
from app.models import Tenant, Usuario
from app.schemas.socio import MediaUploadOut
from app.services.media import subir_imagen
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(require_owner)])


@router.post("/upload", response_model=MediaUploadOut)
async def upload_media(
    file: UploadFile = File(...),
    tipo: str = Form(default="logo"),  # 'logo' | 'premio' | 'general'
    usuario: Usuario = Depends(require_owner),
    db: Session = Depends(get_db),
):
    """Sube una imagen a Cloudinary en carpetas organizadas por socio y propósito."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser una imagen válida (JPG, PNG, WebP, SVG)",
        )

    folder_map = {
        "logo": "yapai/empresas/logos",
        "premio": f"yapai/premios/{usuario.tenant_id}",
        "general": f"yapai/empresas/{usuario.tenant_id}",
    }
    folder = folder_map.get(tipo, f"yapai/general/{usuario.tenant_id}")

    try:
        url = subir_imagen(file.file, folder=folder)
    except ValueError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e)) from e
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Error al subir imagen a Cloudinary: {str(e)}",
        ) from e

    # Si se sube como logo de empresa, actualizar inmediatamente el tenant
    if tipo == "logo" and usuario.tenant_id:
        tenant = db.get(Tenant, usuario.tenant_id)
        if tenant:
            tenant.logo_url = url
            db.commit()

    return MediaUploadOut(url=url)
