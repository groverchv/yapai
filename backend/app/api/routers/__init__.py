from fastapi import APIRouter

from app.api.routers import auth, dev, kiosco
from app.api.routers.admin import admin_router
from app.api.routers.caja import caja_router
from app.api.routers.cliente import cliente_router
from app.api.routers.socio import socio_router

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(socio_router, prefix="/socio", tags=["socio"])
api_router.include_router(cliente_router, prefix="/cliente", tags=["cliente"])
api_router.include_router(kiosco.router, prefix="/kiosco", tags=["kiosco"])
api_router.include_router(caja_router, prefix="/caja", tags=["caja"])
api_router.include_router(dev.router, prefix="/dev", tags=["dev"])
