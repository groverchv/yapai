"""Generador y cargador de 50 clientes y ecosistema completo de datos iniciales en Yapai.
Genera datos para Administrador, Socios y Clientes, guardando en datos.json, datos, y PostgreSQL.
"""
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone

# Añadir backend al sys.path para usar sus modelos y db session
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.security import hash_secret
from app.db.session import SessionLocal
from app.models import (
    AuditLog, Campana, CategoriaNegocio, Cliente, ConfigPin, EmpleadoSucursal,
    EsquemaComision, EstadoCliente, EstadoFactura, EstadoLiquidacion, EstadoPase,
    EstadoPremio, EstadoSucursal, EstadoTenant, EstadoUsuario, FacturaPlan,
    Liquidacion, ModoPin, MovimientoPuntos, Pantalla, PaseDigital, PinSucursal, Plan,
    Premio, RolUsuario, RuletaSegmento, Sucursal, Tenant, TipoMovimiento, Usuario,
)

NOMBRES = [
    ("Juan Carlos", "Pérez Morales"), ("María Elena", "Gómez Suárez"), ("Carlos Alberto", "Mamani Flores"),
    ("Lucía Fernanda", "Rojas Quispe"), ("Alejandro", "Vargas Torrico"), ("Sofía Belén", "Choque Condori"),
    ("Roberto", "Flores Mendizábal"), ("Valeria", "Gutiérrez Hurtado"), ("Mateo", "Fernández Paz"),
    ("Camila Andrea", "Sánchez Pinto"), ("Diego Armando", "Romero Cruz"), ("Gabriela", "Villanueva Ríos"),
    ("Rodrigo", "Navarro Calle"), ("Daniela Paola", "Morales Ortiz"), ("Andrés Felipe", "Castillo Soliz"),
    ("Mariana", "Aparicio Baldivieso"), ("José Luis", "Delgado Guzmán"), ("Natalia", "Mendoza Claros"),
    ("Fernando", "Aguilar Montaño"), ("Paola Andrea", "Cabrera Zeballos"), ("Ignacio", "Salazar Peñaranda"),
    ("Claudia", "Paredes Terán"), ("Hugo", "Espinoza Arteaga"), ("Lorena", "Benítez Cossio"),
    ("Javier", "Ramos Escalante"), ("Adriana", "Camacho Rivera"), ("Mauricio", "Guzmán Saavedra"),
    ("Silvia", "Torres Mercado"), ("Sebastián", "Alarcón Medina"), ("Patricia", "Quinteros Vaca"),
    ("Marcos", "Heredia Justiniano"), ("Verónica", "Chávez Cuéllar"), ("Joaquín", "Peralta Villarroel"),
    ("Jimena", "Zambrana Ledezma"), ("Gonzalo", "Callejas Barrientos"), ("Beatriz", "Velasco Montero"),
    ("Emilio", "Carvalho Roca"), ("Flavia", "Daza Aramayo"), ("Bruno", "Soliz Osinaga"),
    ("Renata", "Llanos Bustillos"), ("Nicolás", "Chirinos Prado"), ("Tatiana", "Sucre Loayza"),
    ("Lucas", "Arze Cardona"), ("Romina", "Terceros Vallejos"), ("Fabián", "Monje Camacho"),
    ("Carla", "Urquidi Antelo"), ("Álvaro", "Peña Soria"), ("Jessica", "Villarroel Lanza"),
    ("Leonardo", "Céspedes Claure"), ("Vanessa", "Zelada Tórrez"),
]

SOCIOS_DEF = [
    {
        "nit": "1234567019",
        "nombre_comercial": "Pizzería Don Yapai",
        "razon_social": "Don Yapai SRL",
        "categoria": "gastronomia",
        "plan": "pro",
        "email": "owner@demo.com",
        "cajero_email": "cajero@demo.com",
        "telefono": "70000000",
        "logo_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400",
        "sucursales": [
            {"nombre": "Sucursal Centro", "direccion": "Av. Principal 123", "pantalla": "kiosco-demo-001", "pin": "4521"},
            {"nombre": "Sucursal Sur", "direccion": "Calle 21 de Calacoto 450", "pantalla": "kiosco-sur-001", "pin": "4522"},
        ],
        "premios": [
            {"nombre": "Pizza familiar gratis", "puntos": 500, "stock": 15, "img": "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=400"},
            {"nombre": "Gaseosa 2L", "puntos": 150, "stock": 50, "img": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400"},
            {"nombre": "Porción de Pan de Ajo", "puntos": 100, "stock": 30, "img": "https://images.unsplash.com/photo-1573140247632-f8fd74997d5c?w=400"},
        ],
        "ruleta": [("10 pts", 10, 4), ("25 pts", 25, 3), ("50 pts", 50, 2), ("100 pts", 100, 1)],
    },
    {
        "nit": "2345678011",
        "nombre_comercial": "Café Aroma Urbano",
        "razon_social": "Aroma Urbano SRL",
        "categoria": "gastronomia",
        "plan": "starter",
        "email": "owner.cafe@yapai.com",
        "cajero_email": "cajero.cafe@yapai.com",
        "telefono": "70110000",
        "logo_url": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=400",
        "sucursales": [
            {"nombre": "Aroma Prado", "direccion": "El Prado Edif. Alameda PB", "pantalla": "kiosco-cafe-001", "pin": "1234"},
        ],
        "premios": [
            {"nombre": "Cappuccino Doble", "puntos": 120, "stock": 40, "img": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400"},
            {"nombre": "Tarta de Frutos Rojos", "puntos": 220, "stock": 20, "img": "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400"},
        ],
        "ruleta": [("15 pts", 15, 4), ("30 pts", 30, 3), ("60 pts", 60, 1)],
    },
    {
        "nit": "3456789012",
        "nombre_comercial": "Burger Kingpin Gourmet",
        "razon_social": "Kingpin Foods SA",
        "categoria": "gastronomia",
        "plan": "pro",
        "email": "owner.burger@yapai.com",
        "cajero_email": "cajero.burger@yapai.com",
        "telefono": "70220000",
        "logo_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
        "sucursales": [
            {"nombre": "Kingpin Sopocachi", "direccion": "Plaza Abaroa 200", "pantalla": "kiosco-burger-001", "pin": "7890"},
            {"nombre": "Kingpin Miraflores", "direccion": "Av. Busch 1420", "pantalla": "kiosco-burger-002", "pin": "7891"},
        ],
        "premios": [
            {"nombre": "Combo Burger Bacon Deluxe", "puntos": 450, "stock": 25, "img": "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=400"},
            {"nombre": "Papas Rústicas Cheddar", "puntos": 180, "stock": 35, "img": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400"},
        ],
        "ruleta": [("20 pts", 20, 4), ("40 pts", 40, 3), ("80 pts", 80, 2), ("150 pts", 150, 1)],
    },
    {
        "nit": "4567890013",
        "nombre_comercial": "Barbería El Barón",
        "razon_social": "El Barón Estilo Masculino",
        "categoria": "salud-y-belleza",
        "plan": "starter",
        "email": "owner.barberia@yapai.com",
        "cajero_email": "cajero.barberia@yapai.com",
        "telefono": "70330000",
        "logo_url": "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=400",
        "sucursales": [
            {"nombre": "El Barón Central", "direccion": "Av. Montenegro 890", "pantalla": "kiosco-baron-001", "pin": "3321"},
        ],
        "premios": [
            {"nombre": "Perfilado de Barba Gratis", "puntos": 250, "stock": 20, "img": "https://images.unsplash.com/photo-1621605815971-fbc98d665033?w=400"},
            {"nombre": "Corte Clásico Caballero", "puntos": 400, "stock": 15, "img": "https://images.unsplash.com/photo-1599351431202-1e0f0137899a?w=400"},
        ],
        "ruleta": [("25 pts", 25, 4), ("50 pts", 50, 2), ("100 pts", 100, 1)],
    },
    {
        "nit": "5678901014",
        "nombre_comercial": "TechZone Gadgets",
        "razon_social": "TechZone Bolivia SRL",
        "categoria": "tecnologia",
        "plan": "enterprise",
        "email": "owner.tech@yapai.com",
        "cajero_email": "cajero.tech@yapai.com",
        "telefono": "70440000",
        "logo_url": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=400",
        "sucursales": [
            {"nombre": "TechZone Megacenter", "direccion": "Megacenter Local 34", "pantalla": "kiosco-tech-001", "pin": "9911"},
            {"nombre": "TechZone Multicine", "direccion": "Av. Arce Multicine Nivel 2", "pantalla": "kiosco-tech-002", "pin": "9912"},
        ],
        "premios": [
            {"nombre": "Audífonos In-Ear Bluetooth", "puntos": 800, "stock": 10, "img": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400"},
            {"nombre": "Cable Carga Rápida USB-C", "puntos": 300, "stock": 30, "img": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=400"},
        ],
        "ruleta": [("50 pts", 50, 4), ("100 pts", 100, 3), ("200 pts", 200, 1)],
    },
    {
        "nit": "6789012015",
        "nombre_comercial": "Boutique Bella Moda",
        "razon_social": "Bella Moda Creaciones",
        "categoria": "indumentaria",
        "plan": "pro",
        "email": "owner.moda@yapai.com",
        "cajero_email": "cajero.moda@yapai.com",
        "telefono": "70550000",
        "logo_url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400",
        "sucursales": [
            {"nombre": "Bella Moda San Miguel", "direccion": "Calle 18 Calacoto 110", "pantalla": "kiosco-moda-001", "pin": "5544"},
        ],
        "premios": [
            {"nombre": "Bufanda de Alpaca Fina", "puntos": 600, "stock": 8, "img": "https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=400"},
            {"nombre": "Descuento 50 Bs en compra", "puntos": 350, "stock": 50, "img": "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=400"},
        ],
        "ruleta": [("20 pts", 20, 3), ("50 pts", 50, 2), ("150 pts", 150, 1)],
    },
    {
        "nit": "7890123016",
        "nombre_comercial": "Iron Fitness Gym",
        "razon_social": "Iron Gym Club Deportivo",
        "categoria": "salud-y-belleza",
        "plan": "enterprise",
        "email": "owner.gym@yapai.com",
        "cajero_email": "cajero.gym@yapai.com",
        "telefono": "70660000",
        "logo_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400",
        "sucursales": [
            {"nombre": "Iron Gym Central", "direccion": "Av. 6 de Agosto 2140", "pantalla": "kiosco-gym-001", "pin": "6677"},
        ],
        "premios": [
            {"nombre": "Pase Diario Completo + Sauna", "puntos": 300, "stock": 30, "img": "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=400"},
            {"nombre": "Shaker Proteico 700ml", "puntos": 250, "stock": 25, "img": "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=400"},
        ],
        "ruleta": [("30 pts", 30, 4), ("60 pts", 60, 2), ("120 pts", 120, 1)],
    },
    {
        "nit": "8901234017",
        "nombre_comercial": "CleanExpress Lavanderías",
        "razon_social": "CleanExpress Servicios SRL",
        "categoria": "servicios",
        "plan": "starter",
        "email": "owner.clean@yapai.com",
        "cajero_email": "cajero.clean@yapai.com",
        "telefono": "70770000",
        "logo_url": "https://images.unsplash.com/photo-1517677208171-0bc6725a3e60?w=400",
        "sucursales": [
            {"nombre": "CleanExpress Achumani", "direccion": "Calle 22 Achumani 45", "pantalla": "kiosco-clean-001", "pin": "1122"},
        ],
        "premios": [
            {"nombre": "Lavado de Edredón 2 Plazas", "puntos": 400, "stock": 15, "img": "https://images.unsplash.com/photo-1545173168-9f1947eebb7f?w=400"},
            {"nombre": "Lavado al Seco de Traje", "puntos": 500, "stock": 10, "img": "https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=400"},
        ],
        "ruleta": [("25 pts", 25, 4), ("50 pts", 50, 2), ("100 pts", 100, 1)],
    },
]


def poblar():
    db = SessionLocal()
    try:
        print("[poblar] Verificando planes y categorías base...")
        cats_map = {c.slug: c for c in db.query(CategoriaNegocio).all()}
        planes_map = {p.slug: p for p in db.query(Plan).all()}
        esquema = db.query(EsquemaComision).first()

        # 1. Crear Socios, Sucursales, Cajeros, Pantallas, Premios
        tenants_creados = []
        sucursales_creadas = []
        premios_creados = []

        for s_def in SOCIOS_DEF:
            tenant = db.query(Tenant).filter_by(nit_rut=s_def["nit"]).first()
            if not tenant:
                tenant = Tenant(
                    nombre_comercial=s_def["nombre_comercial"],
                    razon_social=s_def["razon_social"],
                    nit_rut=s_def["nit"],
                    categoria_id=cats_map[s_def["categoria"]].id,
                    esquema_comision_id=esquema.id,
                    email_contacto=s_def["email"],
                    telefono=s_def["telefono"],
                    logo_url=s_def["logo_url"],
                    plan_id=planes_map[s_def["plan"]].id,
                    estado=EstadoTenant.activo,
                    puntos_registro=300,
                    puntos_referido=50,
                )
                db.add(tenant)
                db.flush()

                # Owner
                owner = Usuario(
                    email=s_def["email"],
                    password_hash=hash_secret("Owner123!"),
                    nombre=f"Dueño {s_def['nombre_comercial']}",
                    rol=RolUsuario.owner,
                    tenant_id=tenant.id,
                    estado=EstadoUsuario.activo,
                )
                db.add(owner)

                # Cajero
                cajero = Usuario(
                    email=s_def["cajero_email"],
                    password_hash=hash_secret("Cajero123!"),
                    nombre=f"Cajero {s_def['nombre_comercial']}",
                    rol=RolUsuario.cajero,
                    tenant_id=tenant.id,
                    estado=EstadoUsuario.activo,
                )
                db.add(cajero)
                db.flush()

                # Config PIN
                db.add(ConfigPin(tenant_id=tenant.id, modo=ModoPin.por_sucursal))

                # Sucursales y Pantallas
                for suc_data in s_def["sucursales"]:
                    suc = Sucursal(
                        tenant_id=tenant.id,
                        nombre=suc_data["nombre"],
                        direccion=suc_data["direccion"],
                        encargado_nombre=f"Encargado {suc_data['nombre']}",
                        estado=EstadoSucursal.activa,
                    )
                    db.add(suc)
                    db.flush()
                    db.add(PinSucursal(sucursal_id=suc.id, pin_hash=hash_secret(suc_data["pin"])))
                    sucursales_creadas.append(suc)
                    db.add(EmpleadoSucursal(usuario_id=cajero.id, sucursal_id=suc.id))

                    pantalla = Pantalla(
                        sucursal_id=suc.id,
                        nombre=f"Pantalla {suc_data['nombre']}",
                        device_token=suc_data["pantalla"],
                        habilitada_hasta=datetime.now(timezone.utc) + timedelta(days=365),
                    )
                    db.add(pantalla)

                # Premios
                for pr_data in s_def["premios"]:
                    premio = Premio(
                        tenant_id=tenant.id,
                        nombre=pr_data["nombre"],
                        descripcion=f"Premio exclusivo de {s_def['nombre_comercial']}",
                        costo_puntos=pr_data["puntos"],
                        stock_limitado=True,
                        stock=pr_data["stock"],
                        imagen_url=pr_data["img"],
                        estado=EstadoPremio.activo,
                    )
                    db.add(premio)
                    db.flush()
                    premios_creados.append(premio)

                # Ruleta
                for etiqueta, puntos, peso in s_def["ruleta"]:
                    db.add(RuletaSegmento(
                        tenant_id=tenant.id,
                        etiqueta=etiqueta,
                        puntos=puntos,
                        peso=peso,
                        activo=True,
                    ))

                # Facturas SaaS demo
                for periodo, estado in [("2026-08", EstadoFactura.pagada), ("2026-09", EstadoFactura.pagada), ("2026-10", EstadoFactura.pendiente)]:
                    db.add(FacturaPlan(
                        tenant_id=tenant.id,
                        plan_id=planes_map[s_def["plan"]].id,
                        plan_nombre=planes_map[s_def["plan"]].nombre,
                        periodo=periodo,
                        monto=planes_map[s_def["plan"]].precio_mensual,
                        moneda="BOB",
                        estado=estado,
                        vence_en=datetime(2026, int(periodo.split("-")[1]), 15, tzinfo=timezone.utc),
                        pagada_en=datetime(2026, int(periodo.split("-")[1]), 10, tzinfo=timezone.utc) if estado == EstadoFactura.pagada else None,
                        metodo="stripe" if estado == EstadoFactura.pagada else None,
                    ))

                # Liquidación demo
                for periodo, estado, nuevos, canjes in [("2026-08", EstadoLiquidacion.pagada, 18, 12), ("2026-09", EstadoLiquidacion.pagada, 25, 19), ("2026-10", EstadoLiquidacion.pendiente, 14, 8)]:
                    db.add(Liquidacion(
                        tenant_id=tenant.id,
                        periodo=periodo,
                        clientes_nuevos=nuevos,
                        canjes_validados=canjes,
                        costo_registro_unit=5.0,
                        costo_canje_unit=2.5,
                        monto_total=(nuevos * 5.0) + (canjes * 2.5),
                        moneda="BOB",
                        estado=estado,
                        pagada_en=datetime(2026, int(periodo.split("-")[1]), 28, tzinfo=timezone.utc) if estado == EstadoLiquidacion.pagada else None,
                    ))

            tenants_creados.append(tenant)

        db.flush()
        print(f"[poblar] {len(tenants_creados)} socios y catálogos listos.")

        # 2. Generar 50 Clientes con datos realistas
        print("[poblar] Creando 50 clientes y sus movimientos...")
        random.seed(42)  # Determinista para pruebas repetibles
        clientes_db = []
        json_clientes = []

        primer_tenant = tenants_creados[0]
        primer_sucursal = db.query(Sucursal).filter_by(tenant_id=primer_tenant.id).first()

        for i, (nom, ape) in enumerate(NOMBRES, start=1):
            telefono = f"70000{i:03d}"
            ci = f"10000{i:03d}"
            nombre_completo = f"{nom} {ape}"

            cliente = db.query(Cliente).filter((Cliente.ci == ci) | (Cliente.telefono == telefono)).first()
            if not cliente:
                # Código de referido de 8 letras
                codigo_ref = f"YAP{i:03d}BO"
                # Asignar un referidor para algunos
                referidor_id = clientes_db[i // 4].id if (i > 3 and i % 3 == 0 and clientes_db) else None

                t_asignado = random.choice(tenants_creados)
                suc_asignada = db.query(Sucursal).filter_by(tenant_id=t_asignado.id).first() or primer_sucursal

                # Puntos iniciales
                pts_registro = 300
                pts_ruleta = random.choice([20, 50, 100, 150])
                pts_bonus = random.choice([0, 50, 100, 250, 500])
                total_ganados = pts_registro + pts_ruleta + pts_bonus

                cliente = Cliente(
                    nombre=nombre_completo,
                    ci=ci,
                    telefono=telefono,
                    estado=EstadoCliente.activo,
                    saldo_puntos=total_ganados,
                    puntos_congelados=0,
                    tenant_registro_id=t_asignado.id,
                    codigo_referido=codigo_ref,
                    referido_por_id=referidor_id,
                )
                db.add(cliente)
                db.flush()

                # Ledger append-only de movimientos
                db.add(MovimientoPuntos(
                    cliente_id=cliente.id,
                    tenant_id=t_asignado.id,
                    sucursal_id=suc_asignada.id,
                    tipo=TipoMovimiento.registro,
                    puntos=pts_registro,
                    detalle={"motivo": "Registro en Kiosco", "comercio": t_asignado.nombre_comercial},
                ))
                db.add(MovimientoPuntos(
                    cliente_id=cliente.id,
                    tenant_id=t_asignado.id,
                    sucursal_id=suc_asignada.id,
                    tipo=TipoMovimiento.ruleta,
                    puntos=pts_ruleta,
                    detalle={"motivo": "Giro Ruleta Bienvenida"},
                ))
                if pts_bonus > 0:
                    db.add(MovimientoPuntos(
                        cliente_id=cliente.id,
                        tenant_id=t_asignado.id,
                        sucursal_id=suc_asignada.id,
                        tipo=TipoMovimiento.bonus_manual,
                        puntos=pts_bonus,
                        detalle={"motivo": "Bonus compra en tienda", "monto_compra_bob": pts_bonus * 2},
                    ))

                # Crear un Pase Digital activo para los primeros 10 clientes
                if i <= 10 and premios_creados:
                    premio_canje = random.choice(premios_creados)
                    if cliente.saldo_puntos >= premio_canje.costo_puntos:
                        pin_pase = f"{random.randint(100000, 999999)}"
                        pase = PaseDigital(
                            cliente_id=cliente.id,
                            premio_id=premio_canje.id,
                            tenant_id=premio_canje.tenant_id,
                            pin_corto=pin_pase,
                            puntos=premio_canje.costo_puntos,
                            estado=EstadoPase.activo,
                            expira_en=datetime.now(timezone.utc) + timedelta(hours=24),
                        )
                        db.add(pase)
                        db.flush()
                        cliente.saldo_puntos -= premio_canje.costo_puntos
                        cliente.puntos_congelados = premio_canje.costo_puntos
                        db.add(MovimientoPuntos(
                            cliente_id=cliente.id,
                            tenant_id=premio_canje.tenant_id,
                            pase_id=pase.id,
                            tipo=TipoMovimiento.congelar,
                            puntos=-premio_canje.costo_puntos,
                            detalle={"premio": premio_canje.nombre, "pin": pin_pase},
                        ))

            clientes_db.append(cliente)

            json_clientes.append({
                "numero": i,
                "nombre": cliente.nombre,
                "telefono": cliente.telefono,
                "ci": cliente.ci,
                "saldo_puntos": cliente.saldo_puntos,
                "puntos_congelados": cliente.puntos_congelados,
                "codigo_referido": cliente.codigo_referido,
                "comercio_registro": db.get(Tenant, cliente.tenant_registro_id).nombre_comercial if cliente.tenant_registro_id else "Yapai Central",
            })

        db.commit()
        print(f"[poblar] ¡50 Clientes y datos completos insertados exitosamente en PostgreSQL!")

        # 3. Guardar en datos.json
        data_completa = {
            "resumen": {
                "superadministradores": 1,
                "socios_comercios": len(SOCIOS_DEF),
                "total_clientes": len(json_clientes),
                "total_premios": len(premios_creados),
                "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            },
            "credenciales_acceso": {
                "administrador": {
                    "url": "http://localhost:5173",
                    "email": "admin@yapai.com",
                    "password": "Admin123!",
                    "descripcion": "Panel general con métricas globales, socios, esquemas, facturación SaaS y liquidaciones."
                },
                "socios_demo": [
                    {
                        "comercio": s["nombre_comercial"],
                        "categoria": s["categoria"],
                        "plan": s["plan"],
                        "url_socio": "http://localhost:5175/login",
                        "url_terminal_caja": "http://localhost:5175/terminal",
                        "url_kiosco": f"http://localhost:5175/kiosco/{s['sucursales'][0]['pantalla']}",
                        "pin_kiosco": s["sucursales"][0]["pin"],
                        "owner_login": {"email": s["email"], "password": "Owner123!"},
                        "cajero_login": {"email": s["cajero_email"], "password": "Cajero123!"},
                    }
                    for s in SOCIOS_DEF
                ],
                "movil_cliente": {
                    "app": "Flutter Movil Cliente (Android / Web)",
                    "instrucciones": "Ingresa con el Teléfono y Cédula de Identidad de cualquiera de los 50 clientes.",
                    "cliente_demo_principal": {"telefono": "70000001", "ci": "10000001", "nombre": "Juan Carlos Pérez Morales"}
                }
            },
            "clientes_50": json_clientes,
        }

        json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "datos.json"))
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data_completa, f, indent=2, ensure_ascii=False)
        print(f"[poblar] Archivo guardado: {json_path}")

        # 4. Guardar archivo legible en d:\Yapai\Datos\datos
        datos_txt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "datos"))
        lineas = [
            "=" * 78,
            "                   YAPAI - ECOSISTEMA DE DATOS INICIALES",
            "=" * 78,
            "",
            "1. ACCESO ADMINISTRADOR GENERAL (Superadmin)",
            "   URL:        http://localhost:5173",
            "   Email:      admin@yapai.com",
            "   Password:   Admin123!",
            "   Funciones:  Dashboard global, socios, liquidaciones, planes SaaS, auditoría.",
            "",
            "2. ACCESO SOCIOS COMERCIALES (Owners, Cajeros y Kioscos)",
            "   Portal Socio:     http://localhost:5175",
            "   Terminal de Caja: http://localhost:5175/terminal",
            "",
        ]

        for s in SOCIOS_DEF:
            lineas.append(f"   [{s['nombre_comercial']}] ({s['categoria'].upper()} - Plan {s['plan'].upper()})")
            lineas.append(f"   * Owner:    {s['email']}  /  Owner123!")
            lineas.append(f"   * Cajero:   {s['cajero_email']}  /  Cajero123!")
            lineas.append(f"   * Kiosco:   http://localhost:5175/kiosco/{s['sucursales'][0]['pantalla']}  (PIN: {s['sucursales'][0]['pin']})")
            lineas.append("")

        lineas.extend([
            "3. ACCESO APP MÓVIL CLIENTE (50 Clientes Registrados)",
            "   En la app móvil ingresa con cualquier combinación de Teléfono y CI:",
            "-" * 78,
            f"{'N°':<4} | {'Nombre':<30} | {'Teléfono':<12} | {'CI':<12} | {'Puntos':<8} | {'Comercio':<20}",
            "-" * 78,
        ])

        for c in json_clientes:
            lineas.append(f"{c['numero']:<4} | {c['nombre'][:30]:<30} | {c['telefono']:<12} | {c['ci']:<12} | {c['saldo_puntos']:<8} | {c['comercio_registro'][:20]:<20}")

        lineas.append("-" * 78)
        lineas.append("\nTodos los datos están sincronizados en la base de datos PostgreSQL yapai_db.")

        with open(datos_txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))
        print(f"[poblar] Archivo legible guardado: {datos_txt_path}")

    finally:
        db.close()


if __name__ == "__main__":
    poblar()
