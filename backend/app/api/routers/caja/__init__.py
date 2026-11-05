from app.api.routers.caja import pantalla, terminal
from fastapi import APIRouter

caja_router = APIRouter()
caja_router.include_router(terminal.router, tags=["caja"])
caja_router.include_router(pantalla.router, tags=["caja"])
