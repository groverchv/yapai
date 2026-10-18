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
            {"nombre": "Pizza familiar gratis", "puntos": 500, "stock": 25, "img": "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=400", "desc": "Pizza artesanal familiar de 8 porciones a elección."},
            {"nombre": "Pizza Mediana Pepperoni", "puntos": 380, "stock": 35, "img": "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400", "desc": "Masa crujiente, queso mozzarella fundido y abundante pepperoni."},
            {"nombre": "Calzone Relleno 4 Quesos", "puntos": 320, "stock": 20, "img": "https://images.unsplash.com/photo-1541745537411-b8046dc6d66c?w=400", "desc": "Masa horneada rellena de mozzarella, provolone, gorgonzola y parmesano."},
            {"nombre": "Gaseosa 2L a elección", "puntos": 150, "stock": 60, "img": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400", "desc": "Botella de 2 litros bien fría (Coca-Cola, Fanta o Sprite)."},
            {"nombre": "Porción de Pan de Ajo Gratinado", "puntos": 100, "stock": 45, "img": "https://images.unsplash.com/photo-1573140247632-f8fd74997d5c?w=400", "desc": "4 piezas de pan baguette con mantequilla de ajo, perejil y queso."},
            {"nombre": "Tiramisú Artesanal Italiano", "puntos": 200, "stock": 30, "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400", "desc": "Delicado postre de café espresso, mascarpone y cacao puro."},
            {"nombre": "Combo Fiesta: Pizza + Acompañamiento + Bebida", "puntos": 650, "stock": 15, "img": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400", "desc": "El combo definitivo para compartir con amigos o familia."},
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
            {"nombre": "Cappuccino Doble Especial", "puntos": 120, "stock": 50, "img": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400", "desc": "Café de especialidad con leche texturizada y arte latte."},
            {"nombre": "Tarta de Frutos Rojos", "puntos": 220, "stock": 25, "img": "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400", "desc": "Porción de tarta fresca con frambuesas, moras y crema pastelera."},
            {"nombre": "Café Americano Grande", "puntos": 80, "stock": 60, "img": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400", "desc": "Espresso doble con agua purificada y notas de chocolate amargo."},
            {"nombre": "Croissant de Jamón y Queso", "puntos": 160, "stock": 35, "img": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400", "desc": "Hojaldre francés crujiente horneado cada mañana."},
            {"nombre": "Frappé Moka con Crema Chantilly", "puntos": 180, "stock": 30, "img": "https://images.unsplash.com/photo-1578314675249-a6910f80cc4e?w=400", "desc": "Bebida helada de café con jarabe de chocolate y salsa de caramelo."},
            {"nombre": "Desayuno Aroma Completo", "puntos": 350, "stock": 20, "img": "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=400", "desc": "Café a elección + tostadas + huevos revueltos + jugo de naranja natural."},
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
            {"nombre": "Combo Burger Bacon Deluxe", "puntos": 450, "stock": 30, "img": "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=400", "desc": "Hamburguesa angus 200g, panceta crujiente, cheddar y papas."},
            {"nombre": "Papas Rústicas con Cheddar y Tocino", "puntos": 180, "stock": 45, "img": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400", "desc": "Papas fritas con piel, salsa de queso cheddar fundido y trocitos de tocino."},
            {"nombre": "Doble Smash Cheeseburger", "puntos": 380, "stock": 25, "img": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400", "desc": "Dos medallones smash bien sellados con cebolla caramelizada."},
            {"nombre": "Alitas BBQ Glaseadas (6 pcs)", "puntos": 280, "stock": 25, "img": "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=400", "desc": "Alitas crocantes bañadas en salsa barbacoa ahumada casera."},
            {"nombre": "Aros de Cebolla Crocantes", "puntos": 140, "stock": 40, "img": "https://images.unsplash.com/photo-1639024471287-032f66ab750d?w=400", "desc": "Rebozados en panko con dip de mayonesa de ajo asado."},
            {"nombre": "Milkshake Gigante Oreo & Vainilla", "puntos": 220, "stock": 35, "img": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400", "desc": "Batido cremoso de helado de vainilla, galletas Oreo y salsa de fudge."},
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
            {"nombre": "Perfilado de Barba con Toalla Caliente", "puntos": 250, "stock": 25, "img": "https://images.unsplash.com/photo-1621605815971-fbc98d665033?w=400", "desc": "Ritual tradicional con navaja clásica, aceites esenciales y toalla al vapor."},
            {"nombre": "Corte Clásico Caballero", "puntos": 400, "stock": 20, "img": "https://images.unsplash.com/photo-1599351431202-1e0f0137899a?w=400", "desc": "Corte a tijera o máquina degradado con asesoría de estilo."},
            {"nombre": "Lavado Capilar + Masaje Antiestrés", "puntos": 180, "stock": 30, "img": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400", "desc": "Shampoo mentolado revitalizante y 10 minutos de masaje capilar."},
            {"nombre": "Cera Moldeadora Matte Barón 100ml", "puntos": 300, "stock": 18, "img": "https://images.unsplash.com/photo-1597354984706-fac992d9306f?w=400", "desc": "Fijación media-alta con acabado mate natural sin residuos."},
            {"nombre": "Aceite Hidratante para Barba 30ml", "puntos": 260, "stock": 20, "img": "https://images.unsplash.com/photo-1608248597359-5f2105151520?w=400", "desc": "Enriquecido con jojoba y argán para suavidad y brillo impecable."},
            {"nombre": "Servicio VIP Completo (Corte + Barba + Mascarilla)", "puntos": 650, "stock": 10, "img": "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=400", "desc": "La experiencia total de barbería con bebida de cortesía."},
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
            {"nombre": "Audífonos In-Ear Bluetooth TWS", "puntos": 800, "stock": 15, "img": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400", "desc": "Cancelación de ruido activa, estuche de carga USB-C y sonido estéreo HD."},
            {"nombre": "Cable Carga Rápida USB-C Blindado", "puntos": 300, "stock": 40, "img": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=400", "desc": "Cable trenzado de 2 metros compatible con carga rápida 65W."},
            {"nombre": "Powerbank Portátil 10.000 mAh", "puntos": 700, "stock": 15, "img": "https://images.unsplash.com/photo-1609592424109-dd9892f1b177?w=400", "desc": "Batería externa delgada con pantalla digital e indicador de porcentaje."},
            {"nombre": "Soporte Magnético para Celular Auto", "puntos": 250, "stock": 35, "img": "https://images.unsplash.com/photo-1584438784894-089d6a62b8fa?w=400", "desc": "Fijación firme a rejilla de ventilación con rotación 360 grados."},
            {"nombre": "Mouse Inalámbrico Ergonómico", "puntos": 450, "stock": 20, "img": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400", "desc": "Sensor óptico silencioso, diseño ergonómico y receptor nano USB."},
            {"nombre": "Parlante Bluetooth Portátil Resistente al Agua", "puntos": 950, "stock": 8, "img": "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=400", "desc": "Sonido 360 envolvente, graves profundos y certificación IPX6."},
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
            {"nombre": "Bufanda de Alpaca Fina Artesanal", "puntos": 600, "stock": 15, "img": "https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=400", "desc": "Tejido 100% alpaca boliviana, ultra suave, abrigada y elegante."},
            {"nombre": "Cupón Descuento 50 Bs en Tienda", "puntos": 350, "stock": 60, "img": "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=400", "desc": "Aplicable a cualquier compra de prendas de temporada."},
            {"nombre": "Tote Bag Ecológica Bella Moda", "puntos": 220, "stock": 40, "img": "https://images.unsplash.com/photo-1544816155-12df9643f363?w=400", "desc": "Bolsa de lona resistente de algodón orgánico con diseño exclusivo."},
            {"nombre": "Cinturón de Cuero Genuino", "puntos": 450, "stock": 20, "img": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400", "desc": "Cuero vacuno legítimo con hebilla metálica satinada."},
            {"nombre": "Pañuelo de Seda Estampado", "puntos": 280, "stock": 30, "img": "https://images.unsplash.com/photo-1601924994987-69e26d50dc26?w=400", "desc": "Accesorio versátil para cuello, bolso o cabello."},
            {"nombre": "Vale de Compra 100 Bs Premium", "puntos": 650, "stock": 25, "img": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400", "desc": "Válido en colección otoño-invierno y vestidos de fiesta."},
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
            {"nombre": "Pase Diario Completo + Sauna", "puntos": 300, "stock": 40, "img": "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=400", "desc": "Acceso libre a sala de pesas, cardio y área de sauna seco/vapor."},
            {"nombre": "Shaker Proteico Antigrumos 700ml", "puntos": 250, "stock": 35, "img": "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=400", "desc": "Botella mezcladora libre de BPA con esfera de acero quirúrgico."},
            {"nombre": "Evaluación Física InBody y Dieta", "puntos": 350, "stock": 25, "img": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=400", "desc": "Análisis de masa muscular, porcentaje de grasa y pautas de nutrición."},
            {"nombre": "Toalla de Microfibra de Secado Rápido", "puntos": 180, "stock": 50, "img": "https://images.unsplash.com/photo-1616627547584-bf28cee262db?w=400", "desc": "Compacta y ultra absorbente con clip para máquinas de gimnasio."},
            {"nombre": "Entrenamiento Personalizado 1 a 1 (1 hora)", "puntos": 500, "stock": 15, "img": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400", "desc": "Sesión guiada con entrenador certificado para maximizar tus resultados."},
            {"nombre": "Mochila Deportiva Reforzada Iron Gym", "puntos": 750, "stock": 10, "img": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400", "desc": "Compartimento ventilado para zapatillas y tela resistente al agua."},
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
            {"nombre": "Lavado de Edredón 2 Plazas", "puntos": 400, "stock": 25, "img": "https://images.unsplash.com/photo-1545173168-9f1947eebb7f?w=400", "desc": "Tratamiento hipoalergénico antiácaros y secado esponjoso."},
            {"nombre": "Lavado al Seco de Traje 2 Piezas", "puntos": 500, "stock": 20, "img": "https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=400", "desc": "Limpieza ecológica profesional y planchado a vapor presurizado."},
            {"nombre": "Planchado Express de 5 Camisas", "puntos": 300, "stock": 35, "img": "https://images.unsplash.com/photo-1517677208171-0bc6725a3e60?w=400", "desc": "Acabado perfecto en cuello y puños listas en colgador."},
            {"nombre": "Lavado y Desmanchado de Zapatillas Deportivas", "puntos": 250, "stock": 30, "img": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=400", "desc": "Desinfección profunda de suela, capellada y cordones."},
            {"nombre": "Canasta de Lavado Express 6kg", "puntos": 350, "stock": 30, "img": "https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=400", "desc": "Lavado, suavizante aromático y doblado cuidadoso de ropa diaria."},
            {"nombre": "Cupón de Descuento 40 Bs en Servicio", "puntos": 200, "stock": 50, "img": "https://images.unsplash.com/photo-1545173168-9f1947eebb7f?w=400", "desc": "Descuento directo en tu próxima boleta de lavandería."},
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
            if tenant:
                if not tenant.logo_url or tenant.logo_url != s_def["logo_url"]:
                    tenant.logo_url = s_def["logo_url"]
                    db.flush()

                # Upsert premios para socios existentes
                for pr_data in s_def["premios"]:
                    pr_existente = db.query(Premio).filter_by(tenant_id=tenant.id, nombre=pr_data["nombre"]).first()
                    desc_premio = pr_data.get("desc", f"Premio exclusivo de {s_def['nombre_comercial']}")
                    if pr_existente:
                        pr_existente.costo_puntos = pr_data["puntos"]
                        pr_existente.stock = pr_data["stock"]
                        pr_existente.imagen_url = pr_data["img"]
                        pr_existente.descripcion = desc_premio
                        pr_existente.estado = EstadoPremio.activo
                    else:
                        nuevo_pr = Premio(
                            tenant_id=tenant.id,
                            nombre=pr_data["nombre"],
                            descripcion=desc_premio,
                            costo_puntos=pr_data["puntos"],
                            stock_limitado=True,
                            stock=pr_data["stock"],
                            imagen_url=pr_data["img"],
                            estado=EstadoPremio.activo,
                        )
                        db.add(nuevo_pr)
                db.flush()

                for pr in db.query(Premio).filter_by(tenant_id=tenant.id).all():
                    premios_creados.append(pr)
                tenants_creados.append(tenant)
            else:
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
                tenants_creados.append(tenant)

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
                        descripcion=pr_data.get("desc", f"Premio exclusivo de {s_def['nombre_comercial']}"),
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
                "total_recompensas": sum(len(s["premios"]) for s in SOCIOS_DEF),
                "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            },
            "cloudinary_configuracion": {
                "cloud_name": "dwerzrgya",
                "api_key": "581815563668339",
                "api_secret": "ul_5HAkewevM14trmtf7onSxZtU",
                "cdn_base_url": "https://res.cloudinary.com/dwerzrgya/image/upload/",
                "carpetas": {
                    "logos_empresa": "yapai/empresas/logos",
                    "premios_fotos": "yapai/premios/{tenant_id}",
                    "comunicados": "yapai/tenants/{tenant_id}/comunicados",
                    "general": "yapai/general"
                },
                "endpoints": {
                    "subida_directa_backend": "POST http://localhost:8000/api/v1/socio/media/upload",
                    "firma_subida_browser": "POST http://localhost:8000/api/v1/socio/comunicados/uploads/firma"
                },
                "estado": "Activo y verificado con SDK oficial en Backend y Frontend Socio"
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
                        "logo_url": s["logo_url"],
                        "url_socio": "http://localhost:5175/login",
                        "url_terminal_caja": "http://localhost:5175/terminal",
                        "url_kiosco": f"http://localhost:5175/kiosco/{s['sucursales'][0]['pantalla']}",
                        "pin_kiosco": s["sucursales"][0]["pin"],
                        "owner_login": {"email": s["email"], "password": "Owner123!"},
                        "cajero_login": {"email": s["cajero_email"], "password": "Cajero123!"},
                        "total_recompensas": len(s["premios"]),
                        "catalogo_recompensas": [
                            {
                                "nombre": pr["nombre"],
                                "puntos": pr["puntos"],
                                "stock": pr["stock"],
                                "descripcion": pr.get("desc", ""),
                                "imagen_url": pr["img"]
                            }
                            for pr in s["premios"]
                        ],
                        "premios_muestra": s["premios"],
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
            "1. ALMACENAMIENTO DE IMÁGENES EN CLOUDINARY",
            "   Cloud Name:    dwerzrgya",
            "   API Key:       581815563668339",
            "   API Secret:    ul_5HAkewevM14trmtf7onSxZtU",
            "   CDN Base:      https://res.cloudinary.com/dwerzrgya/image/upload/",
            "",
            "   ¿Cómo usarlo en la plataforma?:",
            "   * Logo de Empresa:  http://localhost:5175/perfil",
            "     Entra al perfil de socio, sube o arrastra el logo de tu comercio.",
            "     Se guarda en Cloudinary y se sincroniza en la App Móvil, Kioscos y Terminal.",
            "   * Fotos de Premios: http://localhost:5175/premios",
            "     Al crear o editar premios, sube la foto del producto directo a Cloudinary.",
            "",
            "   Endpoints de Backend disponibles:",
            "   * POST /api/v1/socio/media/upload (multipart: file, tipo='logo'|'premio')",
            "   * POST /api/v1/socio/comunicados/uploads/firma (firma para upload directo)",
            "",
            "2. ACCESO ADMINISTRADOR GENERAL (Superadmin)",
            "   URL:        http://localhost:5173",
            "   Email:      admin@yapai.com",
            "   Password:   Admin123!",
            "   Funciones:  Dashboard global, socios, liquidaciones, planes SaaS, auditoría.",
            "",
            "3. ACCESO SOCIOS COMERCIALES Y RECOMPENSAS (Owners, Cajeros y Kioscos)",
            "   Portal Socio:     http://localhost:5175",
            "   Terminal de Caja: http://localhost:5175/terminal",
            "",
        ]

        for s in SOCIOS_DEF:
            lineas.append(f"   [{s['nombre_comercial']}] ({s['categoria'].upper()} - Plan {s['plan'].upper()})")
            lineas.append(f"   * Logo URL: {s['logo_url']}")
            lineas.append(f"   * Owner:    {s['email']}  /  Owner123!")
            lineas.append(f"   * Cajero:   {s['cajero_email']}  /  Cajero123!")
            lineas.append(f"   * Kiosco:   http://localhost:5175/kiosco/{s['sucursales'][0]['pantalla']}  (PIN: {s['sucursales'][0]['pin']})")
            lineas.append(f"   * Catálogo de Recompensas ({len(s['premios'])} premios disponibles):")
            for pr in s["premios"]:
                lineas.append(f"     - [{pr['puntos']:>4} pts] {pr['nombre']} (Stock: {pr['stock']:>2})")
                lineas.append(f"       Detalle: {pr.get('desc', '')}")
                lineas.append(f"       Imagen:  {pr['img']}")
            lineas.append("")

        lineas.extend([
            "4. ACCESO APP MÓVIL CLIENTE (50 Clientes Registrados)",
            "   En la app móvil ingresa con cualquier combinación de Teléfono y CI:",
            "-" * 78,
            f"{'N°':<4} | {'Nombre':<30} | {'Teléfono':<12} | {'CI':<12} | {'Puntos':<8} | {'Comercio':<20}",
            "-" * 78,
        ])

        for c in json_clientes:
            lineas.append(f"{c['numero']:<4} | {c['nombre'][:30]:<30} | {c['telefono']:<12} | {c['ci']:<12} | {c['saldo_puntos']:<8} | {c['comercio_registro'][:20]:<20}")

        lineas.extend([
            "-" * 78,
            "",
            "=" * 78,
            "5. TABLA RESUMEN DE TODAS LAS RECOMPENSAS POR COMERCIO",
            "=" * 78,
            f"{'Comercio':<24} | {'Recompensa':<32} | {'Puntos':<7} | {'Stock':<5}",
            "-" * 78,
        ])
        for s in SOCIOS_DEF:
            for pr in s["premios"]:
                lineas.append(f"{s['nombre_comercial'][:24]:<24} | {pr['nombre'][:32]:<32} | {pr['puntos']:<7} | {pr['stock']:<5}")

        lineas.append("-" * 78)
        lineas.append("\nTodos los datos y configuraciones están sincronizados en PostgreSQL yapai_db y Cloudinary.")

        with open(datos_txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))
        print(f"[poblar] Archivo legible guardado: {datos_txt_path}")

    finally:
        db.close()


if __name__ == "__main__":
    poblar()
