# YAPAI — Planificación Maestra del Sistema de Fidelización

> Documento de planificación técnica y funcional de todo el ecosistema YAPAI.
> Stack confirmado: **FastAPI + PostgreSQL/PostgREST** (backend) · **SvelteKit 5** (portales web) · **Flutter** (app cliente).

---

## 1. Visión General del Ecosistema

```
┌──────────────────────────────────────────────────────────────────┐
│                        YAPAI PLATFORM                            │
│                                                                  │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────────┐  │
│  │ PORTAL ADMIN  │   │ PORTAL SOCIO  │   │   APP CLIENTE     │  │
│  │ (YAPAI interno│   │ (Owner/Cajero │   │   (Flutter)       │  │
│  │  SuperAdmin)  │   │  + Kiosco)    │   │                   │  │
│  └──────┬────────┘   └──────┬────────┘   └─────────┬─────────┘  │
│         │                   │                      │            │
│         └───────────────────┼──────────────────────┘            │
│                             ▼ HTTPS /api/v1                     │
│                  ┌──────────────────────┐                       │
│                  │   BACKEND FastAPI    │                       │
│                  │  (lógica + JWT auth) │                       │
│                  └──────────┬───────────┘                       │
│                             ▼                                   │
│              ┌────────────────────────────┐                     │
│              │  PostgreSQL  (+ PostgREST  │                     │
│              │  opcional para reporting)  │                     │
│              └────────────────────────────┘                     │
└──────────────────────────────────────────────────────────────────┘
```

### Componentes

| Componente | Carpeta | Usuario | Rol |
|---|---|---|---|
| Portal Admin | `frontend_administrador/` | Equipo YAPAI | `superadmin` |
| Portal Socio | `frontend_socio/` | Dueño del negocio | `owner` |
| Terminal de Caja + Kiosco | `frontend_socio/` (rutas públicas) | Personal | `cajero` / dispositivo |
| App Cliente | `movil_cliente/` | Cliente final | `cliente` |
| API | `backend/` | — | — |

---

## 2. Actores y Matriz de Roles

| Rol | Dónde opera | Acceso |
|---|---|---|
| `superadmin` | Portal Admin | Los 3 módulos admin completos |
| `owner` | Portal Socio | Los 5 módulos del negocio |
| `cajero` | Portal Socio | **Solo** Terminal de Caja (canjes + bonus) |
| `cliente` | App móvil | Wallet, catálogo, pases |
| `kiosco` (dispositivo) | Ruta pública `/kiosco` | Registro de cliente + ruleta, habilitado por PIN |

**Regla dura:** los roles `owner`/`cajero` son fijos e inmutables (no existe gestor de roles en el portal socio). El `superadmin` se crea por seed/migración, no por UI.

---

## 3. Modelo de Datos (PostgreSQL)

### 3.1 Entidades globales (dominio Admin)

```
categorias_negocio
  id, nombre, slug, icono_url, activa, created_at

esquemas_comision
  id, nombre, costo_registro NUMERIC(12,2), costo_canje NUMERIC(12,2),
  moneda (ej. 'BOB'), activo, created_at
  -- inmutable en montos si tiene liquidaciones/transacciones asociadas

usuarios
  id, email UNIQUE, password_hash, nombre,
  rol ENUM('superadmin','owner','cajero'),
  tenant_id NULLABLE → tenants.id,
  estado ENUM('activo','suspendido'),
  ultimo_login, created_at
```

### 3.2 Entidades del socio (tenant)

```
tenants
  id, nombre_comercial, razon_social, nit_rut UNIQUE,
  categoria_id → categorias_negocio,
  esquema_comision_id → esquemas_comision,
  email_contacto, telefono, logo_url,
  estado ENUM('activo','suspendido'),
  suspendido_en, suspendido_por → usuarios.id, created_at

sucursales
  id, tenant_id → tenants, nombre, direccion,
  encargado_nombre, estado ENUM('activa','suspendida'), created_at

empleado_sucursal        -- M:N cajeros ↔ sucursales
  usuario_id → usuarios, sucursal_id → sucursales
  PK(usuario_id, sucursal_id)

pantallas (kioscos físicos)
  id, sucursal_id → sucursales, nombre, device_token UNIQUE,
  estado ENUM('activa','bloqueada'),
  habilitada_por → usuarios.id NULL, habilitada_hasta NULL

config_pin
  tenant_id PK → tenants,
  modo ENUM('por_sucursal','por_cajero'), updated_at

pin_sucursal
  sucursal_id PK → sucursales, pin_hash, updated_at

pin_cajero
  usuario_id PK → usuarios, pin_hash, updated_at
```

### 3.3 Cliente y motor de puntos

```
clientes
  id, nombre, ci, telefono,
  UNIQUE(ci), UNIQUE(telefono),
  estado ENUM('activo','eliminado'),      -- baja lógica GDPR
  saldo_puntos INT DEFAULT 0,             -- cache, recalculado en cada movimiento
  puntos_congelados INT DEFAULT 0,        -- cache de pases activos
  created_at, eliminado_en

premios
  id, tenant_id → tenants, nombre, descripcion,
  costo_puntos INT, imagen_url,
  stock_limitado BOOL, stock INT NULL,
  estado ENUM('activo','agotado','inactivo'), created_at

movimientos_puntos  -- LEDGER APPEND-ONLY (inmutable)
  id, cliente_id → clientes, tenant_id → tenants,
  sucursal_id NULL → sucursales,
  tipo ENUM('registro','ruleta','bonus_manual','canje','congelar','liberar','anulacion'),
  puntos INT (signo +/−),
  pase_id NULL → pases_digitales, premio_id NULL → premios,
  ejecutado_por NULL → usuarios.id,       -- cajero/owner que originó la acción
  metadata JSONB, created_at

pases_digitales
  id, cliente_id → clientes, premio_id → premios, tenant_id → tenants,
  codigo_qr UUID UNIQUE, pin_corto VARCHAR(6) UNIQUE,
  puntos INT,                            -- puntos congelados
  estado ENUM('activo','canjeado','cancelado','expirado'),
  expira_en, canjeado_en, canjeado_por → usuarios.id,
  sucursal_canje_id → sucursales, created_at

ruleta_segmentos (config de la ruleta por socio)
  id, tenant_id → tenants, etiqueta, puntos INT,
  peso INT, color, activo
```

### 3.4 Liquidación y auditoría

```
liquidaciones
  id, tenant_id → tenants, periodo CHAR(7),   -- 'YYYY-MM'
  clientes_nuevos INT, canjes_validados INT,
  costo_registro_unit NUMERIC, costo_canje_unit NUMERIC,  -- snapshot del esquema
  monto_total NUMERIC(12,2),
  estado ENUM('pendiente','pagada'),
  pagada_en, aprobada_por → usuarios.id,
  UNIQUE(tenant_id, periodo), created_at

audit_log                -- acciones sensibles (quién aprobó qué)
  id, actor_id → usuarios.id, accion, entidad, entidad_id,
  detalle JSONB, created_at

onboarding_tokens        -- alta de owners
  id, token_hash, email, tenant_id → tenants,
  expira_en, usado_en NULL

password_resets
  id, usuario_id → usuarios, token_hash, expira_en, usado_en NULL

refresh_tokens
  id, sujeto_tipo ENUM('usuario','cliente'), sujeto_id,
  token_hash, expira_en, revocado BOOL
```

### 3.5 Reglas del ledger

- `movimientos_puntos` **no expone UPDATE ni DELETE** (sin endpoints + trigger `RULE/INSTEAD` opcional en Postgres).
- `saldo_puntos = Σ puntos` de movimientos; `puntos_congelados = Σ puntos` de pases `activo`.
- **Saldo disponible = saldo_puntos − puntos_congelados.**
- Todo cambio de saldo y de pase se hace en **una transacción DB** (movimiento + cache + estado del pase).

---

## 4. PORTAL ADMINISTRADOR — Planificación detallada

### 4.1 Mapa del menú (sidebar)

```
YAPAI ADMIN
│
├── 📊 Dashboard                    /dashboard
│      KPIs globales: socios activos, transacciones del día,
│      liquidaciones pendientes, clientes registrados
│
├── 🏢 Socios
│      ├── Listado                  /socios
│      ├── Nuevo socio              /socios/nuevo
│      └── Detalle (por socio)      /socios/[id]
│             tabs: Perfil · Usuarios · Sucursales · KPIs · Clientes
│
├── 📈 Monitoreo
│      ├── Transacciones globales   /monitoreo/transacciones
│      └── Rendimiento por socio    /monitoreo/rendimiento
│
├── 💰 Liquidaciones
│      ├── Panel mensual            /liquidaciones
│      └── Detalle                  /liquidaciones/[id]
│
└── ⚙️ Configuración
       ├── Categorías de negocio    /configuracion/categorias
       ├── Esquemas de comisión     /configuracion/esquemas
       └── Mi cuenta                /configuracion/cuenta
```

> **Auth:** `/login` fuera del layout protegido. Todas las rutas `(app)` verifican JWT + `rol=superadmin` en `+layout.server.ts` / guard de cliente.

### 4.2 Pantallas por módulo

#### Módulo A — Dashboard (`/dashboard`)

| Componente | Descripción |
|---|---|
| `KpiCard ×4` | Socios activos · Transacciones hoy · Liquidaciones pendientes (monto) · Clientes totales |
| `ChartLine` | Transacciones por día (últimos 30 días) |
| `DataTable mini` | Últimas 10 transacciones globales |
| `AlertList` | Liquidaciones vencidas, socios sin actividad |

#### Módulo B — Gestión de Socios (`/socios`)

**B1. Listado** — `src/routes/(app)/socios/+page.svelte`

- `DataGrid` con **paginación server-side** (`page`, `pageSize`, `sort`).
- Filtros: `estado` (select Activo/Suspendido/Todos) · `nombre_comercial` (texto debounce) · `nit_rut` (texto).
- Columnas: Logo · Nombre comercial · NIT/RUT · Categoría · Esquema · Estado (badge) · Fecha alta · Acciones.
- Acciones por fila: Ver detalle · Suspender/Reactivar · Forzar reset de clave · Reenviar onboarding.
- Botón **Exportar CSV**: `GET /admin/socios?format=csv&<mismos filtros>` → descarga.
- Botón **+ Nuevo socio**.

**B2. Alta manual** — `/socios/nuevo`

Formulario en 3 pasos (wizard o secciones):
1. **Datos comerciales:** nombre comercial, razón social, NIT/RUT, email contacto, teléfono, logo, categoría (select desde API).
2. **Usuario Owner:** nombre + email del administrador del socio.
3. **Esquema de comisión:** select de esquemas activos + resumen de tarifas.

Al confirmar → `POST /admin/socios` → backend crea tenant + usuario owner + token onboarding → **envío automático de email** con link `https://socio.yapai.../onboarding?token=...` (vencimiento configurable, ej. 72h).

**B3. Detalle de socio** — `/socios/[id]`

| Tab | Contenido |
|---|---|
| Perfil | Edición de datos comerciales, categoría, esquema. Botones de **Suspender/Reactivar** (modal de confirmación: "bloquea portal y pantallas físicas") y **Forzar recuperación de clave** del Owner |
| Usuarios | Owner + cajeros del socio (read-only + reset) |
| Sucursales | Listado read-only con estado |
| KPIs | `KpiCard`: clientes nuevos (mes), puntos emitidos, canjes exitosos + gráfico |
| Clientes | DataGrid de clientes captados por este socio |

#### Módulo C — Monitoreo (`/monitoreo`)

**C1. Transacciones globales** — `/monitoreo/transacciones`

- Tabla **solo lectura** del ledger (sin acciones de edición — inmutabilidad garantizada por backend).
- Filtros combinables: rango de fechas (date-range picker) · socio (select) · cliente (CI o teléfono) · tipo de acción (registro/ruleta/canje/bonus/congelar/liberar) · sucursal.
- Columnas: Fecha/hora · Socio · Sucursal · Cliente (CI) · Tipo · Puntos (+/−) · Detalle · Ejecutado por.
- Exportar CSV.

**C2. Rendimiento por socio** — `/monitoreo/rendimiento`

- Selector de socio + rango de fechas.
- `KpiCard`: clientes nuevos captados · puntos emitidos · puntos canjeados · canjes exitosos.
- DataGrid de clientes del comercio con paginación.

#### Módulo D — Liquidaciones (`/liquidaciones`)

**D1. Panel mensual** — `/liquidaciones`

- Selector de periodo (month picker).
- DataGrid: Socio · Periodo · Clientes nuevos · Canjes validados · Monto calculado · Estado (`Pendiente`/`Pagada`) · Acciones.
- Botón **Generar liquidaciones del periodo** (ejecuta cálculo masivo, idempotente por `UNIQUE(tenant_id, periodo)`).

**D2. Detalle** — `/liquidaciones/[id]`

- Desglose de la fórmula:

```
Monto = (Clientes Nuevos × Costo Registro) + (Canjes Validados × Costo Canje)
```

  con los unitarios **snapshot** del esquema vigente al momento del cálculo.
- Listado de movimientos que componen el cobro.
- Acción **Marcar como Pagada** → modal de confirmación → `POST /admin/liquidaciones/:id/pagar` → registra `aprobada_por` (usuario interno) + `audit_log`.

#### Módulo E — Configuración (`/configuracion`)

**E1. Categorías de negocio** — `/configuracion/categorias`

- CRUD simple: nombre, slug, ícono, estado.
- **Protección:** botón eliminar deshabilitado si `socios_vinculados > 0` (el backend retorna el conteo); solo permite desactivar.

**E2. Esquemas de comisión** — `/configuracion/esquemas`

- CRUD: nombre, costo_registro, costo_canje, moneda, activo.
- **Inmutabilidad financiera:** si el esquema tiene transacciones/liquidaciones asociadas (`has_usage=true` desde API), los campos numéricos quedan `readonly` con tooltip "Esquema con liquidaciones asociadas — cree uno nuevo". Se sugiere flujo "Duplicar esquema" para crear versión nueva.

**E3. Mi cuenta** — `/configuracion/cuenta`: datos personales + cambio de contraseña.

### 4.3 Estructura de archivos propuesta (`frontend_administrador`)

```
src/
├── lib/
│   ├── api/
│   │   ├── client.ts            # fetch wrapper: baseURL, JWT, refresh, errores
│   │   ├── socios.ts            # funciones por dominio (tipadas)
│   │   ├── monitoreo.ts
│   │   ├── liquidaciones.ts
│   │   └── configuracion.ts
│   ├── components/
│   │   ├── ui/                  # DataGrid, Modal, Badge, KpiCard, DateRangePicker,
│   │   │                        # ConfirmDialog, EmptyState, Pagination, ExportButton
│   │   └── layout/              # Sidebar, Topbar, UserMenu, NavItem
│   ├── stores/
│   │   ├── auth.svelte.ts       # sesión superadmin (runes Svelte 5)
│   │   └── toast.svelte.ts
│   ├── schemas/                 # zod: validación de formularios
│   └── utils/                   # formatMoney, formatDate, downloadCsv
├── routes/
│   ├── login/+page.svelte
│   └── (app)/
│       ├── +layout.svelte       # sidebar + guard de rol
│       ├── dashboard/+page.svelte
│       ├── socios/
│       │   ├── +page.svelte
│       │   ├── nuevo/+page.svelte
│       │   └── [id]/+page.svelte
│       ├── monitoreo/
│       │   ├── transacciones/+page.svelte
│       │   └── rendimiento/+page.svelte
│       ├── liquidaciones/
│       │   ├── +page.svelte
│       │   └── [id]/+page.svelte
│       └── configuracion/
│           ├── categorias/+page.svelte
│           ├── esquemas/+page.svelte
│           └── cuenta/+page.svelte
└── app.html
```

### 4.4 Librerías recomendadas (admin)

| Necesidad | Librería sugerida |
|---|---|
| Estilos | TailwindCSS 4 + bits-ui (o shadcn-svelte) |
| DataGrid server-side | `@tanstack/svelte-table` |
| Formularios | `sveltekit-superforms` + `zod` |
| Gráficos | `layerchart` o `chart.js` |
| Fechas | `date-fns` |
| Iconos | `lucide-svelte` |

---

## 5. PORTAL SOCIO — Planificación

### 5.1 Mapa del menú

```
YAPAI SOCIO
│
├── 📊 Dashboard                    /dashboard          (KPIs + alertas stock)
├── 🏪 Sucursales                   /sucursales
├── 👥 Empleados                    /empleados
├── 🎁 Recompensas                  /recompensas        (catálogo de premios)
├── 🎡 Ruleta                       /ruleta             (segmentos/premios del juego)
├── 🧾 Terminal de Caja             /terminal           (solo owner + cajero)
├── 📜 Transacciones                /transacciones      (auditoría del local)
├── 🔐 Seguridad / PIN de Caja      /seguridad
└── 👤 Mi cuenta                    /cuenta

Rutas públicas (sin login):
├── /onboarding?token=…             # owner establece contraseña
├── /recuperar                      # reset por email
└── /kiosco/[token]                 # pantalla física: registro cliente + ruleta
```

### 5.2 Resumen por módulo

| Módulo | Pantallas / funciones clave |
|---|---|
| Seguridad y usuarios | Login email+clave, recuperar por email, logout, perfil propio. **Empleados:** DataGrid paginado, alta (rol cajero + asignación de sucursales), edición, suspender/reactivar (baja lógica), reenviar credenciales. Roles fijos: owner/cajero |
| Sucursales y accesos | CRUD sucursales (nombre, dirección, encargado); al suspender → backend bloquea sus pantallas. **PIN de Caja:** elegir modo `por_sucursal` / `por_cajero`, set/rotar PIN de 4 dígitos (se guarda hasheado) |
| Catálogo de recompensas | CRUD premios (nombre, descripción, costo puntos, imagen). Stock limitado → al llegar a 0, estado `agotado` y oculto en app. **Bloqueo:** no editar `costo_puntos` si hay pases activos del premio |
| Terminal de Caja | Búsqueda de pase por **QR (cámara)** o **PIN corto**. Pantalla de confirmación (cliente, CI, premio, puntos) → confirmar: débito + stock −1 + registro cajero. **Bonus manual:** buscar cliente por CI/teléfono y otorgar puntos por compra, con límites diarios/por transacción (anti-fraude) |
| Dashboard y métricas | KPIs filtrables por fecha/sucursal (nuevos clientes, puntos otorgados, consumidos, stock crítico). Historial inmutable con filtros (cajero, tipo, cliente) + export CSV/Excel |

---

## 6. APP MÓVIL CLIENTE — Planificación (Flutter)

### 6.1 Navegación (bottom navigation)

```
├── 🏠 Wallet          Saldo total · puntos congelados · accesos rápidos · historial +/−
├── 🏪 Explorar        Directorio de comercios (buscador + filtro por categoría)
│                      └─ Detalle socio: grilla de premios + sucursales donde canjear
├── 🎟️ Mis Pases       Pases activos (QR grande + PIN corto) · cancelar → libera puntos
└── 👤 Perfil          Datos (nombre, CI, teléfono) · eliminar cuenta (baja lógica)
```

### 6.2 Reglas de la app

- **Login sin OTP:** teléfono + CI (preregistrados en kiosco). Token seguro en `flutter_secure_storage` → sesión persistente.
- **Bloqueo por saldo:** premio con `costo > saldo_disponible` → atenuado + etiqueta "Puntos Insuficientes" + botón deshabilitado.
- **Pase digital:** modal de confirmación → backend genera QR + PIN (4–6 chars) + **congela puntos** → sección "Mis Pases" con cancelación manual que libera saldo.
- **Eliminación de cuenta:** baja lógica + pérdida de puntos (registro en ledger tipo `anulacion`).

### 6.3 Librerías sugeridas

`riverpod` (estado) · `dio` (HTTP) · `go_router` · `flutter_secure_storage` · `qr_flutter` · `cached_network_image` · `intl`

---

## 7. BACKEND — Mapa de Endpoints (`/api/v1`)

### Auth

```
POST /auth/login                  {email, password}          → usuario (admin/owner/cajero)
POST /auth/cliente/login          {telefono, ci}             → cliente
POST /auth/refresh                {refresh_token}
POST /auth/logout
POST /auth/forgot-password        {email}
POST /auth/reset-password         {token, password}
POST /auth/onboarding             {token, password, nombre}  → activa owner
```

### Admin (`rol=superadmin`)

```
GET    /admin/dashboard/kpis
GET    /admin/socios              ?estado=&q=&nit=&page=&size=&format=csv
POST   /admin/socios              → crea tenant + owner + envía onboarding
GET    /admin/socios/{id}         PATCH /admin/socios/{id}
POST   /admin/socios/{id}/suspender    /reactivar
POST   /admin/socios/{id}/forzar-reset /reenviar-onboarding
GET    /admin/socios/{id}/kpis    GET /admin/socios/{id}/clientes
GET    /admin/transacciones       ?desde=&hasta=&tenant=&cliente=&tipo=&sucursal=&format=csv
GET    /admin/liquidaciones       ?periodo=&estado=
POST   /admin/liquidaciones/generar  {periodo}            → cálculo masivo idempotente
GET    /admin/liquidaciones/{id}
POST   /admin/liquidaciones/{id}/pagar
GET|POST|PATCH|DELETE /admin/categorias         (delete protegido por FK de socios)
GET|POST|PATCH|DELETE /admin/esquemas           (PATCH numérico bloqueado si has_usage)
```

### Socio (`rol=owner`)

```
GET|PATCH /socio/perfil
GET    /socio/empleados           POST /socio/empleados   PATCH /socio/empleados/{id}
POST   /socio/empleados/{id}/suspender|reactivar|reenviar
GET|POST|PATCH /socio/sucursales  POST /socio/sucursales/{id}/suspender
GET|PUT  /socio/pin/config        POST /socio/pin/sucursal/{id}|cajero/{id}/rotar
GET|POST|PATCH /socio/premios     POST /socio/premios/{id}/desactivar
GET|POST|PATCH /socio/ruleta/segmentos
GET    /socio/metricas/resumen    ?desde=&hasta=&sucursal=
GET    /socio/transacciones       ?cajero=&tipo=&cliente=&format=csv
```

### Caja (`rol=cajero|owner`)

```
GET  /caja/pases/{codigo}          # QR o PIN corto → preview cliente+premio+puntos
POST /caja/pases/{codigo}/canjear  # débito + stock −1 + log cajero (transacción atómica)
GET  /caja/clientes/buscar?q=      # por CI/teléfono
POST /caja/bonus                   {cliente_id, puntos, motivo}  → valida límites
POST /caja/pantalla/habilitar      {device_token, pin}           → habilita kiosco
```

### Kiosco público (device token, sin login)

```
GET  /kiosco/{device_token}/config       # estado + segmentos ruleta (si habilitada)
POST /kiosco/{device_token}/registro     {nombre, ci, telefono} → alta cliente + puntos registro
POST /kiosco/{device_token}/ruleta/girar {cliente_id} → resultado + puntos
```

### Cliente (app móvil)

```
GET    /cliente/me                 PATCH /cliente/me
DELETE /cliente/me                 → baja lógica + anula puntos
GET    /cliente/wallet             {saldo, congelado, disponible}
GET    /cliente/movimientos        ?page=
GET    /cliente/comercios          ?categoria=&q=
GET    /cliente/comercios/{id}     → info + sucursales
GET    /cliente/comercios/{id}/premios
POST   /cliente/pases              {premio_id} → congela puntos + QR + PIN
GET    /cliente/pases?estado=activo
POST   /cliente/pases/{id}/cancelar → libera puntos
```

---

## 8. Reglas de Negocio e Invariantes

| # | Regla | Dónde se garantiza |
|---|---|---|
| 1 | Ledger de puntos inmutable | Sin endpoints UPDATE/DELETE + trigger DB `BEFORE UPDATE OR DELETE → RAISE` |
| 2 | Suspender socio bloquea portal **y** pantallas | Transacción: `tenants.estado` + `usuarios.estado` + `pantallas.estado` del tenant |
| 3 | Suspender sucursal bloquea sus pantallas | Misma transacción |
| 4 | Categoría con socios no se elimina físicamente | Check `count(tenants)` antes de DELETE → solo `activa=false` |
| 5 | Esquema con uso no edita montos | `has_usage` (existe liquidación o tenant activo) → 409 en PATCH de montos |
| 6 | Premio con pases activos no edita `costo_puntos` | Check `count(pases activos)` → 409 |
| 7 | Congelamiento de saldo | Generar pase = movimiento `congelar` + `puntos_congelados += n` en una TX |
| 8 | Doble gasto imposible | `saldo_disponible = saldo − congelado`; canje valida estado del pase |
| 9 | Canje atómico | TX: pase→`canjeado` + movimiento `canje` + `stock−1` + `cajero_id` |
| 10 | Stock 0 → premio `agotado` automático | Trigger lógico en el canje + filtro en catálogo app |
| 11 | Bonus con límites | Config por tenant (`max_puntos_tx`, `max_puntos_dia_cajero`) → 429 si excede |
| 12 | Liquidación = snapshot | Copia unitarios del esquema al generar; `UNIQUE(tenant_id, periodo)` |
| 13 | Marcar pagada audita quién | `aprobada_por` + fila en `audit_log` |
| 14 | PIN hasheado (nunca plano) | bcrypt/argon2; rotación = nuevo hash |
| 15 | Baja de cliente es lógica | `estado='eliminado'` + movimiento `anulacion` del saldo restante |

---

## 9. Flujos Críticos End-to-End

### 9.1 Alta de socio + onboarding

```
Admin → POST /admin/socios
  → crea tenant (activo) + usuario owner (sin password, estado activo)
  → crea onboarding_token (72h) → envía email con link único
Owner → /onboarding?token= → POST /auth/onboarding {token, password}
  → valida token no usado/no vencido → set password_hash → marca usado_en
```

### 9.2 Habilitar pantalla física (PIN)

```
Cajero en pantalla del local → POST /caja/pantalla/habilitar {device_token, pin}
  → según config_pin.modo: compara pin_sucursal.pin_hash  |  pin_cajero.pin_hash (por empleado)
  → OK → pantallas.habilitada_hasta = now+TTL (ej. turno/8h), habilitada_por = cajero
Kiosco → GET /kiosco/{token}/config → si habilitada y sucursal/socio activos → muestra ruleta
```

### 9.3 Canje completo (cliente → caja)

```
App: POST /cliente/pases {premio_id}
  → TX: valida saldo_disponible ≥ costo → pase 'activo' + movimiento 'congelar'
  → respuesta: QR (uuid) + PIN corto
Caja: GET /caja/pases/{codigo} → preview (nombre, CI, premio, puntos)
Caja: POST .../canjear
  → TX: pase 'canjeado' + movimiento 'canje' (−puntos) + premio.stock−1
       + canjeado_por=cajero, sucursal_canje → si stock=0 → 'agotado'
```

### 9.4 Liquidación mensual

```
Admin → POST /admin/liquidaciones/generar {periodo:'2026-10'}
  → por cada tenant activo:
      clientes_nuevos = count(movimientos tipo 'registro' del periodo)
      canjes_validados = count(pases 'canjeado' del periodo)
      monto = cn*esquema.costo_registro + cv*esquema.costo_canje   (snapshot)
      upsert liquidaciones (tenant, periodo)
Admin → POST /admin/liquidaciones/{id}/pagar → estado 'pagada' + aprobada_por + audit_log
```

---

## 10. Seguridad

- **JWT**: access token corto (15 min) + refresh rotativo persistido (`refresh_tokens`, revocable).
- **Passwords**: bcrypt/argon2. PINs de 4 dígitos: hash igualmente + **rate limit** en `/habilitar` (ej. 5 intentos → lock 15 min).
- **Autorización**: dependency FastAPI por rol (`require_role('superadmin')`) + verificación `tenant_id` en cada query del socio (nunca confiar en IDs del cliente).
- **Kiosco**: `device_token` opaco por pantalla + flag `habilitada_hasta`; sin credenciales de usuario.
- **Emails**: tokens de un solo uso (`usado_en`), solo hash en DB.
- **Auditoría**: `audit_log` en acciones sensibles (suspensión, pago liquidación, reset forzado, rotación PIN).
- **CORS**: restringir `allow_origins` a los dominios reales en producción (hoy `*`).

---

## 11. Plan de Implementación por Fases

### Fase 0 — Fundaciones (backend) ✅
- [x] Modelos SQLAlchemy completos + Alembic (migración inicial)
- [x] Auth JWT: login usuarios, login cliente, refresh, guards de rol
- [x] Seeds: superadmin, categorías base, esquema demo, tenant demo
- [x] Servicio de email (modo dev: log en consola; SMTP configurable por .env)
- [x] `audit_log` + helper de registro

### Fase 1 — Portal Admin (vertical slice) ✅
- [x] Layout (sidebar/topbar) + login + guard
- [x] Categorías y esquemas (CRUD + reglas 4 y 5)
- [x] Socios: listado server-side, filtros, CSV, alta + onboarding
- [x] Detalle socio + suspender/reactivar (reglas 2–3) + reset forzado
- [x] Dashboard con KPIs globales
- [x] Bonus: monitor global de transacciones + liquidaciones (adelantado de Fase 5)

### Fase 2 — Portal Socio (base operativa)
- [x] Onboarding owner + login + perfil
- [x] Sucursales CRUD + empleados (cajeros) + PIN de caja (2 modos)
- [x] Catálogo de premios + stock (regla 6, 10)
- [x] Ruleta: segmentos + endpoint giro *(giro se implementa en Fase 3 con el kiosco)*
- [x] Dashboard del socio: KPIs por fecha/sucursal + historial de transacciones + CSV (adelantado de Fase 5)

### Fase 3 — App cliente + motor de puntos ✅
- [x] Login teléfono+CI, wallet, movimientos
- [x] Explorador: directorio, catálogo, bloqueo por saldo
- [x] Pases digitales: generar/congelar/cancelar (reglas 7–8)
- [x] Kiosco público: registro cliente + ruleta (`/kiosco/[token]` en frontend_socio)
- [x] `services/puntos.py`: motor atómico (congelar/liberar/canjear, reglas 9–10)
- [x] `/caja/pantalla/habilitar`: PIN de caja 2 modos (adelantado de Fase 4)
- [x] App Flutter: login persistente, wallet, explorador, pases QR, perfil/baja

### Fase 4 — Terminal de Caja ✅
- [x] Escaneo QR / PIN corto → preview → canje atómico (regla 9)
- [x] Bonus manual con límites por TX y por día/cajero (regla 11)
- [x] Habilitación de pantalla por PIN (flujo 9.2) — pad de PIN en el kiosco
- [x] UI `/terminal` para cajero: canje, bonus, habilitar pantalla + selector de sucursal

### Fase 5 — Monitoreo y liquidación ✅
- [x] Monitor global de transacciones + filtros + CSV (admin y socio) — adelantado en Fases 1–2
- [x] KPIs por socio (admin) y dashboard del socio — adelantado en Fases 1–2
- [x] Generación de liquidaciones + marcar pagada + auditoría (reglas 12–13) — hecho en Fase 1

### Fase 6 — Hardening ✅
- [x] Rate limits (login 10/min·IP, PIN pantalla 5 intentos→15min·IP — `app/core/ratelimit.py`)
- [x] Triggers de inmutabilidad DB: `movimientos_puntos` y `audit_log` append-only (migración `a1b2c3d4e5f6`, Postgres + SQLite)
- [x] Tests de invariantes: 15 tests pytest cubriendo reglas #1,2,3,5,7,8,9,10,11,14,15 (`backend/tests/`)
- [x] Eliminación de cuenta cliente (hecho en Fase 3)
- [x] Expiración automática de pases: job cada 5 min en lifespan + `python -m app.jobs.expiracion` standalone
- [x] Docker completo (`backend/Dockerfile` + compose con api/db/postgrest), CI GitHub Actions (`.github/workflows/ci.yml`), `CORS_ORIGINS` por env

### Fase 7 — SaaS core: planes, signup, trial ✅
- [x] Modelo `planes` (slug, precio, límites: sucursales/pantallas/clientes/empleados, ruleta flag) + `tenants.plan_id` + `tenants.trial_fin` — migración `59789e55c4b8` (batch mode SQLite-safe)
- [x] Límite 0 = ilimitado; tenant sin plan = sin restricciones (cuentas históricas)
- [x] Enforcement `403 {code: upgrade_required}` en: crear sucursal, crear pantalla, crear empleado, registro de cliente en kiosco, ruleta (crear segmento + girar)
- [x] `POST /auth/signup` público (rate limit 5/h·IP): crea tenant en trial de `TRIAL_DIAS` + plan inicial + owner con su clave + ConfigPin; `SIGNUP_MODE=auto` devuelve tokens, `manual` deja el tenant suspendido hasta aprobación admin
- [x] `GET /auth/planes` público (landing) · `GET /socio/plan` (uso vs límites + días de trial) · `admin/planes` CRUD + `PATCH /admin/socios/{id}/plan`
- [x] Landing pública en `frontend_socio /` (hero, cómo funciona, features, pricing desde API) + `/registro` self-serve (auto-login si aprobado, pantalla "en revisión" si manual)
- [x] Dashboard socio: banner de trial con cuenta regresiva + barras de uso vs límites
- [x] Admin: `/configuracion/planes` CRUD + card "Plan comercial" en detalle de socio (cambiar plan + fecha trial)
- [x] `ApiError` soporta `detail` objeto (`code`, `recurso`, `mensaje`) en ambos frontends
- [x] Seed: Starter (gratis, 1 suc/1 pant/500 cli/2 emp, sin ruleta) · Pro (299, 5/5/5k/15, ruleta) · Enterprise (ilimitado); tenant demo en Pro
- [x] 9 tests nuevos en `test_planes.py` — **24 tests pasando** en total

### Fase 9 — Activación: wizard + QR kiosco ✅
- [x] `GET /socio/onboarding` — checklist real por tenant (sucursal→pantalla→premio→ruleta→cajero→primer giro)
- [x] Dashboard socio: card de activación con progreso y links a cada paso
- [x] QR imprimible por pantalla: `GET /socio/sucursales/pantallas/{id}/qr` (SVG) + botón "Ver QR"/descargar/imprimir en `/sucursales`
- [x] Time-to-first-spin: `horas_a_primer_giro` por socio + `ttfs_medio_h` en dashboard admin
- [x] **27 tests pasando**

### Fase 10 — Operación: observabilidad + infra productiva ✅
- [x] `app/core/observability.py`: request-id + access log JSON (`LOG_JSON`) + métricas Prometheus + `init_sentry()` (`SENTRY_DSN`)
- [x] `GET /metrics` (Prometheus; bloqueado al público en Caddy) · header `X-Request-ID` en toda respuesta
- [x] Frontends: `adapter-node` + Dockerfiles multi-stage + `PUBLIC_API_BASE` configurable en runtime
- [x] `deploy/`: `docker-compose.prod.yml`, `Caddyfile` (TLS auto, api./app./admin.), `backup.sh` (pg_dump+retención), `RESTORE.md`, `.env.production.example`, `README.md` runbook
- [x] Flutter: Sentry por `--dart-define SENTRY_DSN` · CI: job docker build ×3

### Fase 11 — Billing (núcleo) ✅
- [x] `facturas_plan`: factura mensual por plan (snapshot precio, única por tenant+período) — migración `ef3d7fa30a8d`
- [x] `POST /admin/facturacion/generar` idempotente · `…/{id}/pagar` (método+referencia, auditado) · `…/{id}/anular`
- [x] `GET /socio/facturacion` → estado de cuenta (al_dia|pendiente|vencida) + historial
- [x] Job horario: emite facturas del período → marca vencidas (`FACTURA_VENCE_DIA`) → suspende por impago tras gracia (`FACTURA_GRACIA_DIAS`)
- [x] UI: `/facturacion` en ambos portales + banner de mora en dashboard socio + badge estado de cuenta en detalle admin
- [x] `JOBS_ENABLED=false` en tests · 34/34 pasando · Pasarela online pendiente (webhook→`pagar_factura`)

### Fase 12 — Motor de marketing ✅
- [x] `campanas`: multiplicador x2–x5 (ventana + sucursal opcional) en registro y ruleta del kiosco — `multiplicador`/`campana` en respuestas para UI; `campana_id` en ledger
- [x] Referidos: `codigo_referido` único por cliente + bonus `tenant.puntos_referido` al referidor (tipo `referido`)
- [x] `premio.vigencia_hasta`: promoción temporal (bloquea canje y oculta del catálogo al vencer)
- [x] Reactivación: segmento `/socio/campanas/inactivos?dias` + CSV (canal WhatsApp manual — sin email de clientes)
- [x] UI socio `/campanas` + campo vigencia en premios · 40/40 tests

### Fase 13 — Hardening productivo ✅ (núcleo)
- [x] **2FA TOTP** (migración `e08bad9f7dad`): `usuarios.totp_secret`/`totp_habilitado`, `pyotp` + QR SVG de provisión — login devuelve `requires_2fa`+`pre_token` (type `pre_2fa`, inútil como access token) → `POST /auth/login/2fa` emite tokens; gestión auditada y rate-limited (5/5min)
- [x] **Headers de seguridad**: middleware en API (nosniff/DENY/no-referrer/Permissions-Policy/CSP) + bloque en Caddy para frontends
- [x] **Rate limiter Redis-ready**: `REDIS_URL` → ventana fija `INCR`+`EXPIRE` atómica compartida entre workers; fallback memoria; fail-open si Redis cae
- [x] UI: paso de código en ambos logins + card "Verificación en dos pasos" en perfil socio y nueva `/perfil` admin
- [x] Runbook operativo `deploy/RUNBOOK.md` (secretos, rotación JWT, incidentes, DR)
- [x] Índices compuestos en hot paths (migración `9c4f2e71ab08`) + script k6 `deploy/k6/load.js` listo para staging
- [x] Multi-moneda: `liquidaciones.moneda` snapshot del esquema (`7b3a9c1de204`) + `formatDinero` con `Intl.NumberFormat`
- [x] i18n base (store `i18n.svelte.ts` es/en + selector en perfil, aplicado a nav/login) + a11y (`lang="es"`, Modal con role/aria-modal/Esc)
- [x] `test_seguridad.py`: 5 tests — **45/45 pasando**
- [ ] Pendiente crecimiento: ejecutar k6 en staging, axe automatizado, i18n completo por página

> Las fases restantes del crecimiento están en `PLANIFICACION_STARTUP.md`.

---

## 12. Decisiones Abiertas

| Tema | Opciones | Nota |
|---|---|---|
| Proveedor email | SMTP propio · Resend · SendGrid | Necesario Fase 1 (onboarding) |
| Expiración de pases | TTL fijo (ej. 24h) + job, o sin expiración | Afecta puntos congelados |
| Kiosco | Dentro de `frontend_socio` (propuesto) vs. app separada | Una ruta pública evita 4to proyecto |
| PostgREST | Mantener como proxy de reporting o retirarlo | FastAPI ya cubre la API; evaluar necesidad |
| Storage de imágenes | Local `/static` · S3/Cloudflare R2 | Logos y premios |
| QR scanning en caja | Librería web (ZXing/html5-qrcode) vs. lector físico como teclado | Lector físico es más rápido en POS |

---

## 13. Checklist de Calidad por Feature

Cada feature se considera terminada cuando:
1. Endpoint con schema Pydantic + guard de rol + test del invariante asociado.
2. UI con estado de carga, vacío y error; formularios con validación zod.
3. Acción sensible registrada en `audit_log`.
4. Paginación/filtros server-side en toda tabla.
