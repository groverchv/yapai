# UNIVERSIDAD AUTÓNOMA "GABRIEL RENÉ MORENO"
## FACULTAD DE INGENIERÍA EN CIENCIAS DE LA COMPUTACIÓN Y TELECOMUNICACIONES
### "CARRERA DE SISTEMAS"

---

# MODALIDAD
# PLAN DE EMPRENDIMIENTO – MÉTODO CANVAS: **YAPAI**

**AUTOR(ES):**
- Choque Villca Grover
- Gedalge Cayhuara Cristian Gabriel
- Quispe Callisaya Andres Leonardo

**SANTA CRUZ - BOLIVIA - 2026**

---

## Índice

1. Introducción
2. Modelo de Negocios en base a la Metodología CANVAS
   - 2.1 Bloque 1: Segmento de Clientes
   - 2.2 Bloque 2: Propuesta de Valor
   - 2.3 Bloque 3: Canales de Distribución
   - 2.4 Bloque 4: Relación con el Cliente
   - 2.5 Bloque 5: Flujo de Ingresos
   - 2.6 Bloque 6: Recursos Claves
   - 2.7 Bloque 7: Actividades Clave
   - 2.8 Bloque 8: Asociaciones Claves
   - 2.9 Bloque 9: Estructura de Costos
3. Análisis Financiero y Unit Economics
4. Riesgos y Mitigaciones
5. Conclusiones y Recomendaciones
6. Bibliografía
7. Anexos

---

# 1. Introducción

## 1.1. Contexto y problema

El presente documento detalla el modelo de negocio estructurado para **YAPAI**, una startup tecnológica orientada al sector B2B en Santa Cruz de la Sierra, Bolivia.

Los comercios de alto tráfico en Santa Cruz —cafeterías, pizzerías, comida rápida, retail de conveniencia— enfrentan un problema estructural: **el 60-70% de sus clientes son anónimos**. El comercio no sabe quién le compra, con qué frecuencia, ni puede comunicarse con ellos para traerlos de vuelta. Las soluciones existentes fallan:

- **Tarjetas de cartón/papel perforadas**: se pierden, se falsifican, no generan datos.
- **Módulos de lealtad de sistemas POS**: requieren licencias costosas (USD 50-150/mes), integración técnica compleja y solo funcionan en la caja que tiene ese POS.
- **Apps propietarias del comercio**: desarrollar una app cuesta USD 10.000+ y el cliente no descarga una app por cada local que visita.
- **Tótems/kioscos físicos**: CAPEX alto (Bs 15.000+ por unidad), mantenimiento presencial, punto único de falla.

## 1.2. La solución: YAPAI

Tras un proceso de validación comercial y análisis de costos de infraestructura, el modelo pivoteó hacia una **plataforma de fidelización 100% virtual basada en tecnología QR**, eliminando la dependencia del hardware físico.

**El flujo es deliberadamente mínimo**: el cliente escanea un QR en el acrílico del mostrador → se registra con nombre + Carnet de Identidad + teléfono en menos de 15 segundos → gira una ruleta de premios → acumula puntos → canjea premios con un pase digital que el cajero valida. Sin apps obligatorias, sin tarjetas físicas, sin integración POS.

## 1.3. Estructura del documento

El documento desarrolla los nueve bloques del Business Model Canvas de Osterwalder & Pigneur (2010), cuantificando cada bloque con datos del mercado cruceño, y complementa con análisis de unit economics, riesgos y recomendaciones estratégicas.

---

# 2. Modelo de Negocios en base a la Metodología CANVAS

## 2.1 Bloque 1: Segmento de Clientes

### 2.1.1. Descripción del segmento de mercado

YAPAI opera un **modelo multi-sided**: dos segmentos interdependientes donde el valor de uno alimenta al otro.

**Segmento primario (quien paga) — Comercios:**

Negocios del rubro gastronómico y retail de alto tráfico ubicados en zonas de alta recurrencia comercial de Santa Cruz de la Sierra:

- **Gastronomía**: pizzerías, cafeterías, comida rápida, heladerías, franquicias y cadenas locales.
- **Retail de alto tráfico**: tiendas de conveniencia, farmacias de barrio, panaderías.
- Zonas objetivo: centro histórico, Equipetrol, San Miguel, Calleja, Plan 3000 — corredores con flujo peatonal diario comprobable.

Perfil del decisor: dueño o gerente del local, 30-55 años, con smartphone, que ya intentó fidelizar con promociones informales ("el décimo café gratis") sin medir resultados.

**Segmento secundario (quien usa) — Cliente final:**

Consumidor recurrente de 18 a 45 años con dispositivo móvil y conectividad, cliente habitual del comercio (visita 2+ veces/mes). Es el "incentivo" que hace valiosa la red: no paga, pero su registro y retención justifican la suscripción del comercio.

**Segmento terciario (operador) — Cajeros/empleados:**

Personal de caja del comercio que valida canjes desde la terminal web. No decide la compra pero su experiencia determina si el programa se usa o se abandona — por eso la terminal fue diseñada para operarse en <15 segundos.

### 2.1.2. Criterios de segmentación

| Criterio | Aplicación |
|---|---|
| **Geográfico** | Santa Cruz de la Sierra; sucursales en zonas de tráfico peatonal alto |
| **Tamaño/giros** | Comercios formales con al menos 1 sucursal y 50+ transacciones/día |
| **Conductual** | Ya intentan fidelizar informalmente; alta rotación en caja; necesitan base de clientes propia sin depender de redes sociales |
| **Tecnológico** | No requieren POS específico: basta un smartphone/tablet para la terminal y navegador para el portal |
| **Exclusión** | Comercios sin mostrador físico (delivery-only) — el QR de mostrador es el punto de contacto |

### 2.1.3. Cuantificación de la demanda potencial

| Nivel | Estimación | Fuente/método |
|---|---|---|
| **Mercado total (TAM)** | ~40.000 comercios formales en Santa Cruz | Registros SEPREC/CAINCO; comercios con NIT activo |
| **Mercado servible (SAM)** | ~6.000 locales de gastronomía y retail de alto tráfico | ~15% del TAM: rubro + zona + tráfico mínimo |
| **Captación año 1 (SOM)** | 100 comercios afiliados | 1,7% del SAM — 8-9 cierres/mes con venta consultiva |
| **Capacidad de plataforma** | 20 comercios activos primeros 90 días | Capacidad operativa del equipo fundador |
| **Registros por comercio** | ~150 clientes finales/mes/comercio | ~5 escaneos/día en mostrador de tráfico medio |

**Clientes finales proyectados año 1**: 100 comercios × 150 registros/mes × 12 meses ≈ **hasta 180.000 registros** (con solapamiento natural de clientes compartidos entre comercios).

### 2.1.4. Personas

**Persona 1 — Doña Marlene (decisor)**: 42 años, dueña de una cafetería en Equipetrol. 120 clientes/día. Reparte tarjetas "10° café gratis" que se pierden. No sabe cuántos clientes vuelven. Quiere verse moderna sin gastar en un POS nuevo.

**Persona 2 — Kevin (cajero)**: 22 años, cajero de pizzería. Turno con picos de 20 clientes/hora. Si el canje tarda más de 15 segundos, lo salta. Su jefe evalúa YAPAI por si él "le da uso".

**Persona 3 — Lucía (cliente final)**: 28 años, oficinista. Almuerza 3 veces/semana en el mismo local. No descarga apps de locales, pero escanear un QR y girar una ruleta le toma 20 segundos entre que le sirven.

---

## 2.2 Bloque 2: Propuesta de Valor

### 2.2.1. Propuesta de valor por segmento

**Para el comercio gastronómico/alto tráfico:**

> *"Fidelización sin fricción: tu cliente se registra en menos de 15 segundos en el mostrador, sin descargar apps ni llenar formularios largos, y tú obtienes tu base de datos de clientes desde el día uno."*

- **Datos accionables inmediatos**: dashboard en tiempo real con clientes registrados, puntos otorgados, pases activos, frecuencia de retorno y top clientes.
- **Gamificación que vende**: la ruleta de puntos convierte el registro —una acción aburrida— en un momento de juego en el mostrador; el comercio configura segmentos, premios y probabilidades.
- **Cero hardware**: el único elemento físico es un acrílico de ~50 Bs con el QR. Sin POS, sin tótems, sin técnicos.
- **Marketing directo sin intermediarios**: publica ofertas que aparecen en la app del cliente; notificaciones push a la base registrada — canal propio que no paga pauta.

**Para retail multi-sucursal:**

- Programa de puntos **configurable por sucursal** (premios, ruleta, puntos de registro, PIN de caja por sucursal o por cajero).
- Métricas consolidadas del grupo + detalle por sucursal; control anti-fraude integrado.

**Para el cliente final:**

- Acumular puntos y canjear premios con el carnet de identidad o desde la app PWA — sin tarjetas físicas que se pierden ni cuentas con contraseña (login con CI + teléfono).
- Feed de ofertas de sus comercios favoritos, mapa de sucursales con GPS, pases digitales con QR de un solo uso.

### 2.2.2. Problema que soluciona

| Problema actual | Solución YAPAI |
|---|---|
| Tarjetas de cartón se extravían/falsifican | Puntos en ledger digital auditable, inmutable y congelable |
| Cliente anónimo: no se sabe quién compra | Registro con CI real en 15s → base de datos con identidad verificable |
| Hardware falla, se corta luz/internet | Solo un QR impreso; el kiosco corre en el teléfono del cliente, no en un aparato del local |
| Apps pesadas que nadie descarga | El registro es web (sin descarga); la app PWA es opcional y se instala con 1 toque |
| Promociones sin medición | Cada punto y canje queda registrado: ROI del programa medible |

### 2.2.3. Necesidad que satisface

Permite al negocio conocer exactamente **quién le compra** desde el momento del registro: identidad real (CI), contacto (teléfono), frecuencia de compra, hábitos de consumo y valor del cliente a lo largo del tiempo. Transforma la relación "cliente anónimo → dato propio" sin obligar al cliente a descargar aplicaciones pesadas ni al comercio a invertir en equipos.

### 2.2.4. Diferenciadores frente a alternativas

| Alternativa | Precio | Fricción cliente | Datos | Riesgo |
|---|---|---|---|---|
| Tarjeta cartón | ~0 (solo imprenta) | Baja pero se pierde | **Ninguno** | Fraude total |
| Módulo fidelización POS | USD 50-150/mes + hardware | Media | Solo ventas de esa caja | Lock-in del POS |
| App propia del comercio | USD 10.000+ desarrollo | Altísima (descarga) | Completos | Abandono >90% |
| Tótem con pantalla | Bs 15.000+ + mantenimiento | Baja | Completos | Punto único de falla |
| **YAPAI** | **Bs 0-700/mes** | **Mínima (escanear QR)** | **Completos + CI verificado** | **Un acrílico de 50 Bs** |

### 2.2.5. Descripción del producto

SaaS multi-tenant compuesto por cuatro superficies web:

| Componente | Descripción técnica |
|---|---|
| **Kiosco QR en mostrador** | Página web que abre al escanear el QR del acrílico: registro (nombre + CI + teléfono + consentimiento legal), ruleta de puntos configurable, modo atracción con slideshow de ofertas cuando nadie lo usa |
| **App del cliente (PWA)** | Instalable desde el navegador: saldo por comercio, catálogo de premios, pases digitales QR/PIN de un solo uso, feed de ofertas, historial de movimientos, notificaciones push, perfil con código de referido |
| **Portal del comercio** | Dashboard con KPIs y alertas, gestión de premios/sucursales/empleados/campañas/comunicados, configuración de ruleta y PINs, terminal de caja para validar canjes por cámara o PIN |
| **Portal administrador YAPAI** | Gestión de tenants (socios), planes, facturación, liquidaciones y monitoreo de la plataforma |

Respaldado por: API REST (FastAPI), base de datos PostgreSQL con **ledger de puntos append-only** (los movimientos no se editan ni borran — solo se contrarrestan), puntos congelados durante el canje (anti doble-gasto), rate limiting anti-fraude y notificaciones Web Push.

---

## 2.3 Bloque 3: Canales de Distribución

### 2.3.1. Canales por fase del embudo

| Fase | Canal | Detalle |
|---|---|---|
| **Awareness** | Venta directa + referidos + landing | Visita al local con demo en vivo desde el teléfono del vendedor |
| **Evaluación** | Demo remota + trial 90 días | El comercio prueba con clientes reales antes de pagar |
| **Compra** | Onboarding guiado en plataforma | Registro → sucursal → PIN caja → kiosco en 15 minutos |
| **Entrega** | Cuenta remota + acrílico POP | Entrega presencial del material: también es visita de relación |
| **Post-venta** | WhatsApp Business + dashboard | Soporte remoto; el dashboard mismo es el canal de valor continuo |

### 2.3.2. Integración de canales: el QR como doble canal

El canal de adquisición y el canal de entrega son distintos pero **se integran en el acrílico**: el QR en mostrador es simultáneamente (a) canal de entrega del servicio al cliente final y (b) canal de captación de nuevos clientes del comercio. Cada escaneo es un registro que alimenta el valor percibido del comercio → justifica la renovación de la suscripción → financia más canales. Es un **loop viral local**: más clientes registrados = más valor = más comercios interesados.

### 2.3.3. Cuantificación de costos del canal

| Canal | Costo | Tipo |
|---|---|---|
| Material POP (acrílico + QR impreso) | ~50 Bs único por local | Variable |
| Venta directa (movilidad + demos) | 500 Bs/mes | Fijo (en estructura) |
| Landing + WhatsApp Business + dominio | ~0-100 Bs/mes | Fijo bajo |
| Trial 90 días (costo de servir gratis) | ~17 Bs/comercio/mes (server compartido) | Variable |
| **CAC estimado por comercio** | **75-150 Bs** según segmento (ver 2.9.2) | — |

---

## 2.4 Bloque 4: Relación con el Cliente

### 2.4.1. Estrategia de relación

Relación **automatizada (autoservicio) con soporte 100% remoto** — diseñada para escalar sin equipo de soporte presencial:

| Momento del ciclo | Tipo de relación | Detalle |
|---|---|---|
| **Alta** | Onboarding guiado in-app | Checklist de activación: sucursal → premio → kiosco → primera venta |
| **Uso diario** | Autoservicio total | Dashboard en tiempo real, autosuficiente; cajero opera terminal sin capacitación formal |
| **Soporte** | Remoto (WhatsApp + email) | SLA informal en trial; SLA prioritario en plan Enterprise |
| **Retención** | El dato mismo retiene | La base de clientes registrados vive en YAPAI: el switching cost crece con cada registro |
| **Expansión** | Upgrade orgánico | Los límites del plan (sucursales, clientes) empujan el upgrade natural al crecer |

### 2.4.2. Cuantificación del costo de relación

| Ítem | Costo estimado |
|---|---|
| Onboarding + capacitación remota por alta nueva | ~50 Bs/comercio (único) |
| WhatsApp Business + correos automatizados | ~100 Bs/mes |
| Soporte remoto (~20 comercios, ~1h/comercio/mes) | ~500 Bs/mes en tiempo |
| **Total a escala de 20 comercios** | **~600 Bs/mes** — escala lineal suave, sin visitas de servicio técnico |

---

## 2.5 Bloque 5: Flujo de Ingresos

### 2.5.1. Flujos por segmento

| Fuente | Tipo | Detalle |
|---|---|---|
| **Suscripción mensual (SaaS)** | Recurrente, principal | Plan mensual por comercio según límites |
| **Comisión por uso** | Variable, alineada con valor | Bs 5 por cliente registrado + Bs 2,5 por premio canjeado — el comercio paga más cuanto más le funciona |
| **Cliente final** | Gratis | No paga: es el incentivo que hace valiosa la red |

### 2.5.2. Estrategia de precios

| Plan | Precio | Incluye |
|---|---|---|
| **Starter** | Bs 0/mes | 1 sucursal, 1 pantalla QR, hasta 500 clientes — puerta de entrada sin riesgo |
| **Pro** | Bs 350/mes | Hasta 5 sucursales y pantallas, 5.000 clientes, ruleta y campañas |
| **Enterprise** | Bs 700/mes | Límites ilimitados, soporte prioritario y API |

**Política comercial**: 90 días de prueba gratuita (baja la barrera del "déjame pensarlo"), cobro mensual o anual (anual con descuento ~17%: 10 meses cobran 12), por transferencia bancaria o QR Simple; facturación automática emitida por la plataforma.

### 2.5.3. Proyección de ingreso por comercio (ARPU)

| Componente | Estimación mensual por comercio Pro |
|---|---|
| Suscripción | 350 Bs |
| Comisión registros (~150/mes × Bs 5) | ~750 Bs |
| Comisión canjes (~60/mes × Bs 2,5) | ~150 Bs |
| **ARPU total** | **~1.250 Bs/mes** |

> La comisión por uso supera a la suscripción como fuente — diseño intencional: el comercio percibe el cargo ligado a resultados concretos (clientes reales, canjes reales), no a un gasto fijo.

### 2.5.4. Modalidades de cobro

- **Mensual**: transferencia o QR Simple; recordatorio automático.
- **Anual prepagado**: 10× precio mensual (2 meses gratis) — mejora cash-flow y reduce churn.
- **Liquidación de comisiones**: consolidada mensual desde el ledger (cada registro y canje ya es un evento contable auditable).

---

## 2.6 Bloque 6: Recursos Claves

| Tipo | Recurso | Rol |
|---|---|---|
| **Intelectual** | Plataforma YAPAI | App cliente PWA + portal socio + kiosco + terminal + portal admin; ledger append-only de puntos; sistema anti-fraude (rate limiting, puntos congelados, pases de un solo uso, PIN por sucursal/cajero) |
| | Marca y diseño | Identidad YAPAI, assets PWA, templates de ofertas |
| | Datos | Base de clientes registrados con CI — activo que crece con cada escaneo |
| **Físico/digital** | Infraestructura cloud | Servidor (AWS/GCP), PostgreSQL, Redis, CDN de imágenes (Cloudinary), HTTPS/TLS |
| | Material POP | Acrílicos con QR por local afiliado |
| **Humano** | Equipo fundador | Desarrollo full-stack + gestión comercial (3 socios con roles complementarios) |
| **Financiero** | Capital semilla | Cobertura de costos fijos hasta punto de equilibrio (~13 comercios, ver §3) |

---

## 2.7 Bloque 7: Actividades Clave

| Actividad | Frecuencia | Por qué es clave |
|---|---|---|
| Desarrollo y mantenimiento de plataforma | Continua | El producto ES el negocio; uptime y velocidad = valor percibido |
| Diseño UX de fricción cero | Iterativa | El registro <15s es la promesa central — cada segundo extra mata conversiones en mostrador |
| Venta consultiva B2B | Semanal | Único motor de crecimiento hasta ~100 comercios |
| Onboarding y activación de socios | Por alta | Un socio que no configura su kiosco churn en 90 días — la activación predice retención |
| Auditoría de integridad del ledger | Automática + revisión | Confianza del comercio depende de que los puntos no se puedan inflar |
| Soporte remoto | Diaria | Retención y referidos |
| Generación de contenido/ofertas demo | Por alta | Los comercios nuevos copian lo que ven funcionando |

---

## 2.8 Bloque 8: Asociaciones Claves

### 2.8.1. Alianzas estratégicas

| Aliado | Tipo | Valor |
|---|---|---|
| Imprentas gráficas locales | Proveedor | Acrílicos QR en 24-48h a ~50 Bs; candidata: imprentas zona mercado Los Pozos |
| Pasarelas de pago | Operativo | QR Simple / transferencias para cobro de suscripciones |
| Proveedores de POS | Estratégico futuro | Integración directa en caja (fase 2+: otorgar puntos por monto de venta, no solo por visita) |
| Instituciones del ecosistema | Credibilidad | CAINCO, aceleradoras cruceñas — aval ante comercios conservadores |

### 2.8.2. Socios clave

- **Proveedor cloud** (AWS región São Paulo / GCP): latencia baja a Bolivia, escalado por demanda.
- **Cloudinary** (imágenes): transformación on-the-fly de logos/fotos de premios y ofertas.
- **Push providers** (Google FCM/Mozilla push vía Web Push): canal de notificaciones al cliente.
- **Por formalizar**: imprenta local (cotización recibida, pendiente convenio de volumen), distribuidor POS en SCZ para pilotos de integración.

---

## 2.9 Bloque 9: Estructura de Costos

### 2.9.1. Cuantificación de costos

**Costos fijos mensuales:**

| Ítem | Costo |
|---|---|
| Soporte y desarrollo tecnológico (equipo) | 3.500 Bs/mes |
| Servidores cloud + dominio + CDN | 350 Bs/mes |
| Movilidad y viáticos comerciales | 500 Bs/mes |
| **Costos fijos totales** | **4.350 Bs/mes** |

**Costos variables:**

| Ítem | Costo |
|---|---|
| Material POP por comercio nuevo | 50 Bs único |
| Onboarding por alta | ~50 Bs único |
| Soporte incremental por comercio | ~25 Bs/mes |
| Servidor incremental (por volumen) | ~17 Bs/mes por comercio activo |

### 2.9.2. Costos por segmento

| Segmento | CAC (adquisición) | Notas |
|---|---|---|
| Retail local único | ~75 Bs | Demo remota + 1 visita + POP |
| Gastronomía (franquicia/cadena) | ~150 Bs | Venta consultiva multi-sucursal (~3 visitas) — compensa con varias sucursales por contrato |

---

# 3. Análisis Financiero y Unit Economics

## 3.1. Punto de equilibrio

| Escenario | Cálculo | Resultado |
|---|---|---|
| Solo suscripción Pro | 4.350 ÷ 350 Bs | **~13 comercios** |
| Con ARPU completo (~1.250 Bs) | 4.350 ÷ 1.250 | **~4 comercios** |

## 3.2. Unit economics por comercio Pro

| Métrica | Valor | Método |
|---|---|---|
| ARPU | 1.250 Bs/mes | Suscripción + comisiones (§2.5.3) |
| Margen bruto/comercio | ~1.208 Bs (97%) | ARPU − costos variables ~42 Bs |
| CAC | ~110 Bs | Promedio segmentos (§2.9.2) |
| Payback del CAC | **<1 mes** | CAC ÷ margen mensual |
| Churn estimado | 5%/mes (conservador) | SaaS SMB benchmark |
| **LTV** | **~24.000 Bs** | Margen mensual ÷ churn (1.208 ÷ 0.05) |
| **LTV/CAC** | **~220×** | Excepcional — cada boliviano en ventas rinde ~220 |

> Incluso con churn del 15%/mes (escenario pesimista SMB), LTV/CAC ≈ 73× — el modelo soporta fallas de retención porque el CAC es ínfimo frente al margen.

## 3.3. Proyección de ingresos año 1

| Trimestre | Comercios (acum.) | Ingreso mensual final (Bs) | Supuestos |
|---|---|---|---|
| Q1 | 20 | ~25.000 | 100% Pro con uso medio |
| Q2 | 45 | ~56.000 | 2 cierres/semana |
| Q3 | 70 | ~87.000 | Referidos empiezan a bajar CAC |
| Q4 | 100 | ~125.000 | SOM alcanzado |

---

# 4. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Comercio no renueva tras trial | Media | Alto | Checklist de activación + métricas que demuestran ROI antes del día 60 |
| Cliente no escanea el QR | Media | Alto | Ruleta (incentivo inmediato) + acrílico visible + cajero invita verbalmente |
| Fraude (registros falsos, canjes duplicados) | Media | Alto | Ledger append-only, pases de un solo uso con expiración, puntos congelados, PIN de caja, rate limiting por IP/CI |
| Caída de internet en el local | Media | Bajo | El kiosco corre en el teléfono del cliente (su propio dato móvil); QR impreso sigue escaneándose |
| Competidor copia el modelo | Alta (largo plazo) | Medio | La base de clientes registrados es el foso: el switching cost crece con cada registro |
| Regulación de datos personales | Baja-media | Medio | Consentimiento explícito en registro, eliminación de cuenta desde la app, política publicada |

---

# 5. Conclusiones y Recomendaciones

## 5.1. Conclusiones

1. **El modelo QR 100% virtual es la estructura óptima para escalar rápido**: elimina CAPEX en hardware, reduce costos fijos a ~4.350 Bs/mes y alcanza el punto de equilibrio con ~13 comercios (o ~4 considerando ARPU completo). A partir de ahí, cada comercio adicional aporta margen incremental >90%.

2. **Las unit economics son excepcionales**: LTV/CAC ~220× (o ~73× en escenario pesimista) gracias al CAC ínfimo (~110 Bs) frente a márgenes ~97%. La única variable crítica es la velocidad de venta consultiva.

3. **El diseño anti-fraude resuelve la confianza**: ledger inmutable, pases de un solo uso, puntos congelados y registro con CI real + consentimiento dan trazabilidad legal y contable sin fricción adicional.

4. **El trial de 90 días + comisión por uso alinean el riesgo**: el comercio no paga por promesas sino por resultados ya vistos — la conversión se vuelve una decisión contable, no de fe.

## 5.2. Recomendaciones

| Prioridad | Acción | Justificación |
|---|---|---|
| (a) | **Prueba gratuita como palanca central de conversión** | CAC casi nulo durante trial; el dashboard vende solo |
| (b) | **Cerrar alianzas con imprenta y pasarela de pago** | POP es el único insumo físico: asegurar stock y precio |
| (c) | **Crecer por cadena/franquicia antes que por local individual** | Un contrato multi-sucursal = 3-5 deploys por una venta |
| (d) | **Instrumentar métricas de activación desde el día 1** | % socios que completan onboarding predice churn — actuar antes del día 60 |
| (e) | **Integración POS en fase 2, no ahora** | Puntos por monto de venta duplica el valor, pero requiere volumen para negociar con vendors POS |

---

# 6. Bibliografía

- Osterwalder, A., & Pigneur, Y. (2010). *Business Model Generation / Generación de modelos de negocio*. Barcelona: Deusto.
- Ries, E. (2011). *El método Lean Startup*. Barcelona: Deusto.
- Blank, S., & Dorf, B. (2012). *The Startup Owner's Manual*. K&S Ranch.
- SEPREC (2025). *Estadísticas de registros comerciales — Santa Cruz*. Servicio Plurinacional de Registro de Comercio.
- CAINCO (2025). *Anuario económico departamental*. Cámara de Industria, Comercio, Servicios y Turismo de Santa Cruz.
- INE Bolivia (2024). *Proyecciones de población y penetración de telefonía móvil*. Instituto Nacional de Estadística.

---

# 7. Anexos

**Anexo A** — Canvas resumido en una página (diagrama de los 9 bloques).
**Anexo B** — Tabla detallada de unit economics (escenarios optimista/base/pesimista).
**Anexo C** — Capturas de pantalla de la plataforma (kiosco QR, app cliente, portal socio).
**Anexo D** — Cotización de material POP (acrílico QR).
**Anexo E** — Carta de consentimiento/términos mostrada en el registro del cliente.
