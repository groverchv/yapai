from app.api.routers.admin import catalogos, facturacion, liquidaciones, monitoreo, planes, socios
from fastapi import APIRouter

admin_router = APIRouter()
admin_router.include_router(socios.router, prefix="/socios", tags=["admin-socios"])
admin_router.include_router(planes.router, prefix="/planes", tags=["admin-planes"])
admin_router.include_router(catalogos.router, tags=["admin-catalogos"])
admin_router.include_router(monitoreo.router, tags=["admin-monitoreo"])
admin_router.include_router(liquidaciones.router, prefix="/liquidaciones", tags=["admin-liquidaciones"])
admin_router.include_router(facturacion.router, prefix="/facturacion", tags=["admin-facturacion"])
