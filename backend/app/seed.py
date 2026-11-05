"""Semilla inicial idempotente. Uso: python -m app.seed

Crea: superadmin, categorías base, esquema demo y un tenant demo completo
(owner + sucursal + pantalla + cajero + premios + ruleta + cliente demo).
"""
import unicodedata

from app.core.config import settings
from app.core.security import hash_secret
from app.db.base import Base  # noqa: F401  (registra modelos)
from app.db.session import SessionLocal, engine
from app.models import (
    CategoriaNegocio,
    Cliente,
    ConfigPin,
    EmpleadoSucursal,
    EsquemaComision,
    EstadoCliente,
    EstadoPremio,
    ModoPin,
    MovimientoPuntos,
    Pantalla,
    Plan,
    Premio,
    RolUsuario,
    RuletaSegmento,
    Sucursal,
    Tenant,
    TipoMovimiento,
    Usuario,
)
from sqlalchemy import select

PLANES = [
    dict(slug="starter", nombre="Starter", precio_mensual=0, orden=1,
         descripcion="Para empezar: un local y tu programa de puntos",
         max_sucursales=1, max_pantallas=1, max_clientes=500, max_empleados=2,
         ruleta_habilitada=False),
    dict(slug="pro", nombre="Pro", precio_mensual=299, orden=2,
         descripcion="Crece con ruleta, más locales y más clientes",
         max_sucursales=5, max_pantallas=5, max_clientes=5000, max_empleados=15,
         ruleta_habilitada=True),
    dict(slug="enterprise", nombre="Enterprise", precio_mensual=999, orden=3,
         descripcion="Sin límites, soporte prioritario y API",
         max_sucursales=0, max_pantallas=0, max_clientes=0, max_empleados=0,
         ruleta_habilitada=True),
]

CATEGORIAS = ["Gastronomía", "Indumentaria", "Salud y Belleza", "Tecnología", "Servicios"]


def _slugify(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace(" ", "-")


def get_or_create(db, model, defaults: dict | None = None, **filters):
    obj = db.scalar(select(model).filter_by(**filters))
    if obj:
        return obj, False
    obj = model(**{**filters, **(defaults or {})})
    db.add(obj)
    db.flush()
    return obj, True


def run():
    Base.metadata.create_all(bind=engine)  # fallback si no se corrió alembic (dev)
    db = SessionLocal()
    try:
        admin, creado = get_or_create(
            db, Usuario,
            email=settings.SEED_ADMIN_EMAIL,
            defaults=dict(
                nombre="Super Admin",
                rol=RolUsuario.superadmin,
                password_hash=hash_secret(settings.SEED_ADMIN_PASSWORD),
            ),
        )
        if creado:
            print(f"[seed] superadmin: {settings.SEED_ADMIN_EMAIL} / {settings.SEED_ADMIN_PASSWORD}")

        cats = {}
        for nombre in CATEGORIAS:
            slug = _slugify(nombre)
            cat, _ = get_or_create(db, CategoriaNegocio, slug=slug, defaults=dict(nombre=nombre))
            cats[slug] = cat

        esquema, _ = get_or_create(
            db, EsquemaComision, nombre="Estándar",
            defaults=dict(costo_registro=5.00, costo_canje=2.50, moneda="BOB"),
        )

        planes = {}
        for datos in PLANES:
            p, _ = get_or_create(db, Plan, slug=datos["slug"], defaults=datos)
            planes[p.slug] = p

        gastro = cats["gastronomia"]
        tenant, creado = get_or_create(
            db, Tenant, nit_rut="1234567019",
            defaults=dict(
                nombre_comercial="Pizzería Don Yapai",
                razon_social="Don Yapai SRL",
                categoria_id=gastro.id,
                esquema_comision_id=esquema.id,
                email_contacto="owner@demo.com",
                telefono="70000000",
                plan_id=planes["pro"].id,
            ),
        )
        if not tenant.plan_id:
            tenant.plan_id = planes["pro"].id

        if creado:
            owner, _ = get_or_create(
                db, Usuario, email="owner@demo.com",
                defaults=dict(nombre="Dueño Demo", rol=RolUsuario.owner,
                              tenant_id=tenant.id, password_hash=hash_secret("Owner123!")),
            )
            sucursal, _ = get_or_create(
                db, Sucursal, tenant_id=tenant.id, nombre="Sucursal Centro",
                defaults=dict(direccion="Av. Principal 123", encargado_nombre="Dueño Demo"),
            )
            cajero, _ = get_or_create(
                db, Usuario, email="cajero@demo.com",
                defaults=dict(nombre="Cajero Demo", rol=RolUsuario.cajero,
                              tenant_id=tenant.id, password_hash=hash_secret("Cajero123!")),
            )
            get_or_create(db, EmpleadoSucursal, usuario_id=cajero.id, sucursal_id=sucursal.id)
            get_or_create(db, ConfigPin, tenant_id=tenant.id, defaults=dict(modo=ModoPin.por_sucursal))
            get_or_create(
                db, Pantalla, device_token="kiosco-demo-001",
                defaults=dict(sucursal_id=sucursal.id, nombre="Pantalla entrada"),
            )
            get_or_create(
                db, Premio, tenant_id=tenant.id, nombre="Pizza familiar gratis",
                defaults=dict(costo_puntos=500, stock_limitado=True, stock=10, estado=EstadoPremio.activo),
            )
            get_or_create(
                db, Premio, tenant_id=tenant.id, nombre="Gaseosa 2L",
                defaults=dict(costo_puntos=150, stock_limitado=False, estado=EstadoPremio.activo),
            )
            for etiqueta, puntos, peso in [("10 pts", 10, 4), ("25 pts", 25, 3), ("50 pts", 50, 2), ("100 pts", 100, 1)]:
                get_or_create(db, RuletaSegmento, tenant_id=tenant.id, etiqueta=etiqueta,
                              defaults=dict(puntos=puntos, peso=peso))

            cliente, _ = get_or_create(
                db, Cliente, ci="12345678",
                defaults=dict(nombre="Cliente Demo", telefono="70000001",
                              estado=EstadoCliente.activo, tenant_registro_id=tenant.id),
            )
            if not db.scalar(select(MovimientoPuntos).where(MovimientoPuntos.cliente_id == cliente.id)):
                db.add_all([
                    MovimientoPuntos(cliente_id=cliente.id, tenant_id=tenant.id,
                                     tipo=TipoMovimiento.registro, puntos=300),
                    MovimientoPuntos(cliente_id=cliente.id, tenant_id=tenant.id,
                                     tipo=TipoMovimiento.ruleta, puntos=50),
                ])
                db.flush()
                cliente.saldo_puntos = 350
            print("[seed] demo: owner@demo.com/Owner123! · cajero@demo.com/Cajero123! · cliente CI 12345678 tel 70000001")

        db.commit()
        print("[seed] OK")
    finally:
        db.close()


if __name__ == "__main__":
    run()
