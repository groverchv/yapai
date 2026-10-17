from fastapi import APIRouter

from app.api.routers.socio import campanas, empleados, facturacion, metricas, onboarding, perfil, pin, plan, premios, ruleta, sucursales

socio_router = APIRouter()
socio_router.include_router(perfil.router, prefix="/perfil", tags=["socio-perfil"])
socio_router.include_router(plan.router, prefix="/plan", tags=["socio-plan"])
socio_router.include_router(facturacion.router, prefix="/facturacion", tags=["socio-facturacion"])
socio_router.include_router(campanas.router, prefix="/campanas", tags=["socio-campanas"])
socio_router.include_router(onboarding.router, prefix="/onboarding", tags=["socio-onboarding"])
socio_router.include_router(empleados.router, prefix="/empleados", tags=["socio-empleados"])
socio_router.include_router(sucursales.router, prefix="/sucursales", tags=["socio-sucursales"])
socio_router.include_router(pin.router, prefix="/pin", tags=["socio-pin"])
socio_router.include_router(premios.router, prefix="/premios", tags=["socio-premios"])
socio_router.include_router(ruleta.router, prefix="/ruleta", tags=["socio-ruleta"])
socio_router.include_router(metricas.router, tags=["socio-metricas"])
