# YAPAI — Super Planificación Startup (Fases 7-13)

> Documento de brechas y roadmap para convertir el producto técnico (Fases 0-6, completas)
> en una startup SaaS operable y vendible. Fecha: 2026-10-17.

---

## 1. Diagnóstico honesto

**Lo que existe hoy (100% funcional en dev):**
- 4 superficies (admin, socio, terminal, kiosco) + app Flutter compilada
- 15 reglas de negocio garantizadas por API + triggers DB + 15 tests
- Liquidación manual por uso (registro/canje) — el modelo de negocio *actual*

**El problema central:** el producto funciona, pero **no es un negocio autoservible**.
Hoy cada paso comercial depende del fundador operando a mano:

| Flujo de negocio | Estado actual | Lo que necesita una startup |
|---|---|---|
| Captar un socio | Admin crea el tenant a mano | Signup público self-serve + trial |
| Cobrar | Liquidación mensual + "marcar pagada" a mano | Planes con límites + cobro automático |
| Activar un socio | El owner configura solo, sin guía | Wizard de onboarding medible |
| Retener | Sin datos de uso por cuenta | Métricas SaaS (MRR, churn, activación) |
| Notificar | Emails se loguean en consola | SMTP real + push + WhatsApp/SMS |
| Operar | Sin observabilidad ni backups | Sentry + métricas + respaldos + DR |
| Legal | Sin términos/consentimiento | ToS, privacidad, opt-in en kiosco |

---

## 2. Brechas del modelo de negocio (producto)

### 2.1 Monetización — **brecha crítica**
Hoy solo existe facturación por uso manual. Una startup necesita:

- **Planes con límites por tenant** (entidad `planes`):
  - `Starter` (gratis): 1 sucursal, 1 pantalla, 500 clientes, sin ruleta
  - `Pro`: 5 sucursales, 5 pantallas, 5k clientes, ruleta + bonus
  - `Enterprise`: ilimitado + API + soporte
- Enforcement en backend: 403 con `upgrade_required` al exceder límites
- **Billing**: integración con pasarela (Stripe internacional / Mercado Pago / QR
  local Bolivia — decidir por mercado objetivo), facturas, período de gracia,
  suspensión por impago (ya existe el mecanismo de suspensión)
- Las liquidaciones por uso actuales quedan como **modelo híbrido opcional**
  (plan base + comisión por uso) — diferenciador real vs competencia

### 2.2 Self-serve signup — **brecha crítica**
- `POST /auth/signup` público: datos del comercio + owner → crea tenant en estado
  `trial` con plan Starter → wizard en el portal
- Aprobación automática o manual según configuración (`SIGNUP_MODE`)
- Trial de 14 días con cuenta regresiva en el dashboard del socio
- **Landing pública** (`/` del dominio): propuesta de valor, planes, CTA de registro

### 2.3 Onboarding y activación — **brecha alta**
El socio nuevo no sabe qué hacer primero:
- **Wizard/checklist** en el dashboard del socio: "1. Crea tu sucursal → 2. Agrega
  un premio → 3. Configura la ruleta → 4. Imprime tu kiosco → 5. Invita un cajero"
- Métrica North-Star: *time to first spin* (tiempo desde signup hasta el primer
  giro de ruleta de un cliente real)
- QR imprimible del kiosco por pantalla (el socio lo imprime y pega en el local)

### 2.4 Notificaciones — **brecha alta**
- Email transaccional real: SMTP de producción o API (Resend/SendGrid) —
  `EMAIL_ENABLED` ya existe, falta proveedor y plantillas HTML con marca
- **Push (FCM)** en Flutter: "tus puntos vencen", "premio disponible", canje ok
- WhatsApp/SMS (Twilio/Meta Business) para el canal dominante en LatAm —
  registro del kiosco podría mandar "ganaste X pts" por WhatsApp
- Centro de preferencias: opt-in/opt-out por canal (legal)

### 2.5 Motor de marketing — **brecha media (diferenciador)**
- **Campañas**: multiplicador de puntos por fecha ("x2 los martes"), por sucursal
- **Referidos**: cliente invita → ambos ganan pts (código personal)
- **Segmentación**: clientes inactivos 30d → campaña de reactivación automática
- **Promos limitadas**: premios con vigencia ("solo este fin de semana")

### 2.6 Legal y cumplimiento — **brecha media, bloqueante para cobrar**
- Consentimiento en kiosco/registro (checkbox ToS + privacidad)
- Páginas legales públicas: `/legal/terminos`, `/legal/privacidad`
- Retención de datos: política de borrado de pases/movimientos antiguos
- Facturación fiscal según país (en Bolivia: SFV/sin; decidir jurisdicción)

### 2.7 Métricas SaaS — **brecha media**
- Panel admin extendido: MRR, cuentas activas, churn, ARPU,
  funnel de activación (signup → primer canje), cohortes de retención
- Evento tracking interno ya existe (ledger + audit_log) — solo falta la vista

---

## 3. Brechas técnicas y operativas

### 3.1 Observabilidad — **crítico para operar**
- Sentry (backend + frontends + Flutter) — errores reales visibles
- Logs estructurados JSON + request-id correlativo
- Endpoint `/metrics` (Prometheus) + alertas (uptime, errores 5xx, latencia)
- Status page pública simple (uptime de API + kioscos)

### 3.2 Infraestructura productiva — **crítico**
- Reverse proxy con TLS: Caddy (HTTPS automático) o Nginx
- Docker completo: `Dockerfile` por frontend (build→nginx) + compose prod
- **Backups Postgres**: cron `pg_dump` + subida a S3/B2 + restore probado
- Entornos: `staging` + `prod` separados (dos compose/env files)
- Deploy CI: push→tests→build images→registry→deploy (SSH/Watchtower/fly.io)

### 3.3 Seguridad de producción — **alto**
- `JWT_SECRET` y secretos por env manager (no .env en repo — ya ok pero rotarlos)
- **2FA** para superadmin y owners (TOTP — librería `pyotp`)
- Política de contraseñas (mínimo 10 chars, zxcvbn o similar)
- Auditoría de accesos admin (login log por actor — audit_log ya lo permite)
- Rate limiter → Redis si escala a multi-worker
- Headers de seguridad (CSP, HSTS, X-Frame-Options) en proxy

### 3.4 Escalabilidad — **medio**
- Cola de jobs real (email/push/expiración): hoy asyncio in-process — suficiente
  hasta ~1k tenants, luego Celery/RQ + Redis
- Cache de config de kiosco y catálogos (Redis o in-process con TTL)
- Índices: revisar plan de queries en listados con filtros (EXPLAIN periódico)
- CDN para assets de frontends

### 3.5 Calidad — **medio**
- Tests E2E API (Playwright/pytest+TestClient) de los 4 flujos críticos
- Load testing (k6/locust) en endpoints calientes: kiosco config, girar, canje
- Coverage mínimo 80% en services; CI bloquea merge si falla
- Tests de contrato frontend↔backend (o OpenAPI codegen de types)

### 3.6 UX/deuda menor
- i18n: hoy es-BO hardcoded en fechas/mensajes → `svelte-i18n` + `Intl`
- Multi-moneda en esquemas/liquidaciones (hoy BOB)
- Flutter en dispositivo real: build Android + internal testing (Play Console)
- Accesibilidad: auditoría axe de los 3 portales

---

## 4. Roadmap propuesto (Fases 7-13)

### Fase 7 — SaaS core: planes, signup, trial ✅
- [x] Modelo `planes` + `tenant.plan_id` + límites (sucursales/pantallas/clientes/empleados)
- [x] Enforcement de límites con error `upgrade_required` (403)
- [x] `POST /auth/signup` público + aprobación auto/manual (`SIGNUP_MODE`)
- [x] Trial 14 días + countdown en dashboard socio
- [x] Landing pública con planes y CTA (`frontend_socio /`)
- [x] Admin: gestión de planes y asignación por socio

### Fase 8 — Notificaciones reales
- [ ] Proveedor email productivo + plantillas HTML con marca
- [ ] FCM push en Flutter (registro de token, backend `notificaciones` table)
- [ ] Opt-in/out por canal + preferencias en app y portal
- [ ] (Decidir) WhatsApp Business API para kiosco/registro

### Fase 9 — Activación: wizard socio + QR kiosco ✅
- [x] `GET /socio/onboarding`: checklist real (sucursal → pantalla → premio → ruleta* → cajero → primer giro; *solo si el plan incluye ruleta)
- [x] Dashboard socio: card "Activa tu programa" con progreso, pasos tachados y links directos
- [x] `GET /socio/sucursales/pantallas/{id}/qr`: QR SVG imprimible del kiosco — botón "Ver QR" por pantalla + descargar/imprimir
- [x] Métrica time-to-first-spin: `horas_a_primer_giro` en KPIs por socio + `ttfs_medio_h` en dashboard global admin

### Fase 10 — Operación: observabilidad + infra prod ✅
- [x] Sentry backend (`SENTRY_DSN` activa automáticamente) + Flutter (`--dart-define SENTRY_DSN`) — frontends web pendientes de DSN (documentado)
- [x] `ObservabilityMiddleware`: X-Request-ID propagado + access log (JSON si `LOG_JSON=true`) + `/metrics` Prometheus (conteo por ruta+status, histograma de latencia)
- [x] Dockerfiles de ambos frontends (`adapter-node`, `PUBLIC_API_BASE` por env en runtime)
- [x] `deploy/`: `docker-compose.prod.yml` (api+db+2 frontends+caddy), `Caddyfile` con TLS automático por subdominios (api./app./admin.) + `/metrics` bloqueado al público
- [x] `deploy/backup.sh` (pg_dump gzip + retención 14d + cron) + `RESTORE.md` con runbook de restore y DR
- [x] CI: job `docker` que compila las 3 imágenes en cada push

### Fase 11 — Billing ✅ (núcleo; pasarela online pendiente)
- [x] `facturas_plan` (migración `ef3d7fa30a8d`): factura mensual por plan con snapshot de precio — única por tenant+período
- [x] Cobro manual gateway-agnóstico: `POST /admin/facturacion/generar` (idempotente), `…/{id}/pagar` (método+referencia, auditado), `…/{id}/anular`
- [x] Estado de cuenta: `GET /socio/facturacion` (al_dia|pendiente|vencida) + badge en detalle de socio admin
- [x] Job `app/jobs/facturacion.py` (cada hora): auto-emite facturas del período, marca vencidas (`FACTURA_VENCE_DIA`), suspende tras `FACTURA_GRACIA_DIAS` reutilizando `suspender_tenant`
- [x] Frontends: `/facturacion` admin (generar/filtrar/pagar/anular) + `/facturacion` socio (estado, historial, instrucciones de pago) + banner de mora en dashboard
- [x] Solo factura a planes de precio>0 con trial vencido · `JOBS_ENABLED=false` en tests · 34/34 tests
- [ ] Pasarela online (Stripe vs MP/QR local según mercado): el flujo `pagar` ya es el punto de integración — webhook → `pagar_factura`

### Fase 12 — Motor de marketing ✅
- [x] `campanas` (migración `8a33a1fe4f44`): multiplicador x2–x5 con ventana inicio/fin y scope por sucursal — aplica a registro y ruleta en el kiosco (no al bonus manual); respuesta incluye `multiplicador`+`campana` para que el kiosco muestre la promo; el ledger registra `campana_id`
- [x] Referidos: `cliente.codigo_referido` único (generado/backfill en login) + `referido_por_id` — registro en kiosco acepta código → referidor gana `tenant.puntos_referido` (default 100, movimiento tipo `referido`)
- [x] `premio.vigencia_hasta`: promoción temporal — vencido no es canjeable (400) ni visible en el catálogo; badge "Vence/Venció" en premios del socio
- [x] Reactivación: `GET /socio/campanas/inactivos?dias` (segmento con última actividad, días inactivo, saldo) + export CSV + mensaje sugerido — decisión honesta: los clientes no tienen email, el canal real es WhatsApp manual; envío automático requeriría integración de WhatsApp (pendiente)
- [x] Frontend `/campanas`: CRUD multiplicador + segmento inactivos con CSV · 40/40 tests

### Fase 13 — Hardening prod final ✅ (núcleo)
- [x] 2FA TOTP para superadmin/owner: migración `e08bad9f7dad`, `pyotp`, setup con QR + URI de provisión, activación solo tras código válido, desactivación con contraseña; login devuelve challenge (`requires_2fa` + `pre_token` de corta vida) → `POST /auth/login/2fa` emite tokens; rate limit dedicado 5/5min; auditado (`habilitar_2fa`, `deshabilitar_2fa`, `login_2fa`); UI en perfil de socio + página "Mi perfil" nueva en admin; el `pre_token` no sirve como access token (type `pre_2fa` rechazado por deps)
- [x] Headers de seguridad: middleware en API (nosniff, DENY, no-referrer, Permissions-Policy, CSP) + bloque `headers_seguridad` en Caddy para ambos frontends (CSP con connect-src a api.*)
- [x] Rate limiter Redis-ready: `INCR`+`EXPIRE` atómico cuando `REDIS_URL` está definido, fallback en memoria y fail-open si Redis cae; nuevo `totp_limiter`
- [x] Runbook `deploy/RUNBOOK.md`: secretos obligatorios, rotación JWT, deploy, backups, monitoreo/alertas, incidentes (2FA lockout, limiter, suspensión por impago, migración fallida)
- [x] Tuning de índices (migración `9c4f2e71ab08`): compuestos para las queries reales — movimientos (tenant,fecha) y (cliente,fecha), clientes por tenant_registro, pases (estado,expira), premios (tenant,estado), campañas (tenant,activa), facturas (estado,vence)
- [x] Script de carga `deploy/k6/load.js`: escenarios smoke/load con thresholds (p95<800ms, errores<2%), cubre público + socio autenticado + path caliente del kiosco (registro→giro) — pendiente de ejecutar en staging
- [x] Multi-moneda base: `liquidaciones.moneda` (snapshot del esquema, migración `7b3a9c1de204` con backfill), `formatDinero` ahora usa `Intl.NumberFormat` con fallback — ya existía en planes/facturas/esquemas
- [x] i18n base: `src/lib/i18n.svelte.ts` (store runes, es/en, persistido en localStorage, `document.lang` dinámico) — aplicado a sidebars, topbars y logins de ambos portales; selector de idioma en `/perfil`; el resto de páginas adopta `i18n.t()` incrementalmente
- [x] A11y: `lang="es"` en app.html (era "en" — bug real), Modal con `role="dialog"`/`aria-modal`/`aria-label` + cierre con Esc, svelte-check reporta 0 warnings de accesibilidad en ambos portales
- [ ] Ejecutar k6 en staging y ajustar según resultados
- [ ] Auditoría axe automatizada (axe-core/playwright) — svelte-check cubre estáticos, falta runtime
- [ ] i18n completo: extraer strings de todas las páginas (base lista, adopción incremental)

---

## 5. KPIs que debe medir la plataforma (north-star)

| Métrica | Definición | Meta inicial |
|---|---|---|
| **Time to first spin** | signup → primer giro de un cliente real | < 24 h |
| Activación | socios que completan wizard / signups | > 60% |
| Retención semanal | tenants con ≥1 giro en últimos 7 días | > 70% |
| MRR | ingreso mensual recurrente | primer hito: 10 socios pagando |
| Churn | cancelaciones / activos por mes | < 5% |
| Canjes/cliente/mes | frecuencia de uso real | > 1.5 |

---

## 6. Decisiones que solo el fundador puede tomar

1. **Mercado inicial**: ¿Bolivia primero? → define pasarela (QR local vs Stripe),
   moneda principal, legal/facturación
2. **Modelo de cobro**: ¿plan fijo, comisión por uso, o híbrido (plan + comisión)?
   Recomiendo híbrido: plan bajo + comisión alinea incentivos
3. **Sign-up abierto vs. venta asistida**: abierto escala más pero necesita
   límites anti-abuso en plan gratis
4. **Canal de notificación dominante**: ¿WhatsApp > email en tu mercado?
   Cambia la prioridad de la Fase 8
5. **App kiosco dedicada**: ¿kiosco web basta o hace falta APK Android para
   tablets fijas? (web funciona en kiosk-mode, más barato)

---

## 7. Resumen ejecutivo

**El producto técnico está terminado y es sólido.** Para ser startup faltan 3
cosas estructurales, en este orden:

1. **Que cualquiera pueda registrarse y quedar activo solo** (Fases 7+9) —
   sin esto, cada venta cuesta tu tiempo
2. **Que cobre automáticamente** (Fase 7 límites + Fase 11 billing) —
   sin esto, no hay negocio
3. **Que puedas operarlo sin apagarlo** (Fase 10 observabilidad+backups) —
   sin esto, el primer incidente real mata la confianza

El resto (notificaciones, marketing, 2FA, i18n) es crecimiento — importante,
pero no bloquea el lanzamiento. **MVP vendible realista: Fases 7 + 9 + 10
+ Stripe básico** ≈ producto que cobra y se opera solo.
