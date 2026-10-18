from fastapi import APIRouter

from app.api.routers.cliente import comercios, comunicados, cuenta, pases

cliente_router = APIRouter()
cliente_router.include_router(cuenta.router, tags=["cliente"])
cliente_router.include_router(comercios.router, tags=["cliente"])
cliente_router.include_router(pases.router, tags=["cliente"])
cliente_router.include_router(comunicados.router, tags=["cliente"])
