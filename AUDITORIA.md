# Auditoría de Seguridad y Calidad — Yapai

**Fecha:** 2026-11-07 · **Alcance:** backend (FastAPI), 3 frontends (SvelteKit), infraestructura (Docker/Caddy/CI) · **Marcos:** OWASP Top 10 (2021) + ISO/IEC 25010 (7 ejes)

## Resumen ejecutivo

Se auditó el código, la configuración, los contenedores y el pipeline de CI.
Resultado: **4 críticos, 10 altos, ~20 medios y varios bajos** — los críticos y
altos están **corregidos** en este cambio; los medios implementables también.
Lo que queda abierto por ser decisión de diseño/arquitectura está en el
**Roadmap** al final con prioridad sugerida.

El stack elegido es el correcto para un proyecto de larga vida: FastAPI +
PostgreSQL + SQLAlchemy + SvelteKit + Docker + Caddy son tecnologías dominantes,
aburridas y con trayectoria larga. Los cambios estructurales fueron mínimos y
quirúrgicos: se eliminó PostgREST (superficie de ataque sin uso real), se fijaron
las dependencias con lockfile + hashes, y los jobs pasaron a proceso separado.

---

## Hallazgos corregidos

### Críticos

| ID | Hallazgo | Estado | Corrección |
|----|----------|--------|------------|
| C1 | `GET /api/v1/dev/postgrest-proxy/{tabla}` sin autenticación exponía cualquier tabla | ✅ Corregido | Eliminados `routers/dev.py` y `db/postgrest_client.py` |
| C2 | `seed` corría en cada arranque del contenedor → usuarios demo con credenciales públicas en producción | ✅ Corregido | CMD ya no siembra; `seed.py` dividido en `seed_base`/`seed_demo`; `SEED_DEMO` prohibido en producción por el validador |
| C3 | PostgREST (dev) con `PGRST_DB_ANON_ROLE: postgres` (superusuario) y puerto publicado | ✅ Corregido | Servicio PostgREST eliminado del compose de desarrollo (no se usaba en producción) |
| C4 | Sin fail-fast: la app arrancaba en producción con `JWT_SECRET`/`CORS=*`/`DEBUG`/passwords por defecto | ✅ Corregido | `Settings._produccion_segura` aborta el arranque si `ENV=production` con configuración insegura |

### Altos

| ID | Hallazgo | Estado | Corrección |
|----|----------|--------|------------|
| A1 | Rate limiting por IP roto tras el proxy: `request.client.host` era la IP de Caddy para todos | ✅ Corregido | uvicorn con `--proxy-headers` + `forwarded_allow_ips` (Dockerfile, run.py); `TRUSTED_PROXIES` configurable |
| A2 | Sin rate limit en `forgot-password`, `reset-password`, `onboarding`, `refresh`, `logout`, kiosco | ✅ Corregido | Nuevos limiters: `recovery_limiter` (3/h), `token_limiter` (20/min), `kiosco_limiter` (IP+device_token), `cliente_login_limiter` (5/5min) |
| A3 | `random.choices` (PRNG predecible) decidía premios de la ruleta | ✅ Corregido | `secrets.SystemRandom` en `routers/kiosco.py` |
| A4 | `redis` ausente de requirements → en prod el limiter caía a memoria en silencio | ✅ Corregido | `redis==7.4.1` fijado en requirements |
| A5 | JWT en `localStorage` en los 3 SPAs → robo por XSS | ✅ Corregido | Cookies HttpOnly+Secure+SameSite=Lax (`AUTH_TRANSPORT`), guard CSRF (`X-Requested-With`), frontends migrados; Bearer sigue válido para clientes no-web |
| A6 | Upload de imágenes: solo validaba `Content-Type` declarado, aceptaba SVG, sin límite de tamaño | ✅ Corregido | Magic bytes reales, máx 5 MB, SVG rechazado (`services/media.py::validar_imagen`) |
| A7 | Dependencias flotantes `>=`/`^` → builds no reproducibles | ✅ Corregido | `requirements.txt` con `==` + `requirements.lock` con hashes (pip-compile); `package-lock.json` obligatorio en Dockerfiles |
| A8 | Contenedores como root; imágenes base sin fijar; devDeps en runtime | ✅ Corregido | `USER yapai`/`USER node`, `npm prune --omit=dev`, `python:3.13-slim` (antes 3.12, desalineado del README) |
| A9 | `/docs`, `/openapi.json`, `/redoc` expuestos en producción | ✅ Corregido | `DOCS_ENABLED` gate; por defecto off en `ENV=production` |
| A10 | Jobs (expiración/facturación) dentro del proceso API → duplicados al escalar workers | ✅ Corregido | Servicio `jobs` separado en compose prod (`python -m app.jobs.runner`); `JOBS_ENABLED=false` en la API |

### Medios

| ID | Hallazgo | Estado |
|----|----------|--------|
| M1 | Login de cliente = teléfono+CI (datos semi-públicos) | ✅ Corregido | OTP como 2do factor (`OtpCode` hasheado, TTL 5min, máx 5 intentos con lockout, provider webhook para SMS/WhatsApp — obligatorio en prod) |
| M2 | `extra="allow"` en Settings tragaba typos; `FRONTEND_CLIENTE_URL` usada en prod sin declarar | ✅ `extra="forbid"` + variable declarada |
| M3 | Oracle de timing en login (usuario inexistente sin verify) | ✅ `verify_secret_timing_safe` con hash argon2 dummy |
| M4 | Política de password débil (min 8) | ✅ ≥12 chars + letra y dígito en signup/reset/onboarding |
| M5 | Refresh token robado y reusado no revocaba la familia | ✅ Detect-and-kill: reuso → revoca todas las sesiones (con commit propio — bug real encontrado y corregido) |
| M6 | Enumeración CI/teléfono por 409 en registro | ⚠️ Mitigado por rate limits; respuesta genérica cambiaría UX (roadmap) |
| M7 | `device_token` de kiosco en URL como bearer | ✅ Prod ya usaba `secrets.token_urlsafe(18)` + rotación; binding de giro al dispositivo en roadmap |
| M8 | `SIGNUP_MODE=auto` crea tenants sin verificar email | ⚠️ Warning en logs + `manual` recomendado en `.env.production.example` |
| M9 | Backups sin cifrar/offsite/test | ✅ `backup.sh` con GPG opcional + `restore-test.sh` nuevo |
| M10 | JSONs commiteados: `la.json`/`lo.json` (JWT+refresh reales), `socio_nuevo.json` (onboarding token), `body_socio.json` | ✅ Eliminados + `.gitignore` — **nota**: quedan en el historial git; rotar `JWT_SECRET` si el dev secret se usó fuera de local |
| M11 | `Base.metadata.create_all` en seed bypaseaba Alembic | ✅ Eliminado — Alembic es la única fuente de esquema |
| M12 | Dockerfile `python:3.12` vs README "3.13" | ✅ `python:3.13-slim` |
| M13 | `psycopg2-binary` (desaconsejado en prod) | ✅ `psycopg[binary]==3.3.8` (v3) + scheme `postgresql+psycopg://` |
| M14 | `db.query` estilo SQLAlchemy 1.x en empleados | ✅ `delete()` 2.0 |
| M15 | `email_service` logueaba cuerpo completo (links con tokens) | ✅ Truncado a 300 chars |
| M16 | `STRIPE_*` sin SDK ni código (dead config con claves reales en .env) | ✅ Webhook `/api/v1/billing/stripe/webhook` con firma HMAC, idempotencia por `event_id`, suspensión por mora; **rotar CLOUDINARY_API_SECRET y claves Stripe si el repo se compartió** |
| M17 | `_aware()` duplicado en 3 archivos | ✅ `core/utils.aware_utc` |
| M18 | Sin SECURITY.md/security.txt | ✅ Creados |
| M19 | `adapter-auto`+`adapter-node` ambos | ✅ Solo `adapter-node` |
| M20 | `allow_credentials=True` con `*` | ✅ Credentials solo con orígenes explícitos |
| — | `asyncpg` instalado sin uso | ✅ Eliminado de requirements |
| — | `pywebpush` faltaba en requirements (import perezoso que fallaría en prod) | ✅ Fijado `==2.5.0` |

### Bajos / notas

- TOTP secret en claro en DB → roadmap (cifrado de campo).
- `pin-info` expone nombres de cajeros con solo device_token → aceptable (es la UI de desbloqueo).
- ~~Refresh tokens expirados nunca se purgan~~ → ✅ job `limpieza` diario (refresh/resets/onboarding/OTP) en el runner separado.
- ~~Sin purga/export de PII~~ → ✅ `GET /cliente/me/export` (portabilidad) + `DELETE /cliente/me` anonimiza PII y revoca sesiones.
- pip-audit inicial: `certifi` vulnerable → actualizado a `2026.10.18+`.
- `sqlite3` datetime adapter deprecation (tests) → ruido upstream, sin impacto.

## Los 7 ejes ISO/IEC 25010 — evaluación

| Eje | Estado | Evidencia |
|-----|--------|-----------|
| 1. Funcionalidad | 🟡→🟢 | Tests de invariantes + nuevos tests cross-tenant y de seguridad (79 en total); coverage gate en CI |
| 2. Fiabilidad | 🟢 | Healthchecks, jobs dedicados, backup+restore-test, triggers de inmutabilidad, Sentry |
| 3. Usabilidad | 🟢 | Fase UX con a11y, skeletons, empty states, i18n; svelte-check estricto |
| 4. Eficiencia | 🟡 | k6 en deploy/; revisar N+1 y publicar baseline en siguiente iteración |
| 5. Mantenibilidad | 🟢 | Deps fijadas + lock con hashes, `extra=forbid`, ConfigDict (sin deprecation), ADRs, ARCHITECTURE.md, ruff+S |
| 6. Portabilidad | 🟢 | Docker no-root reproducible, Postgres/SQLite dual en tests, export CSV/pg_dump |
| 7. Seguridad | 🟢 | Todo el catálogo OWASP anterior + tooling CI (pip-audit, npm audit, gitleaks, Trivy, dependabot, ruff-S) |

## Hardening de CI añadido

- `pip-audit -r requirements.txt` · `npm audit --omit=dev` ×3 · `gitleaks` · `ruff --select S` · `Trivy` fs scan · verificación `whoami != root` en las 4 imágenes
- `dependabot.yml`: pip, npm ×3, docker ×5, github-actions (semanal)
- Cron semanal para auditar dependencias aun sin pushes
- Coverage gate: `--cov-fail-under=75` (medido 82% en 2026-11; objetivo 85%)

## Roadmap (pendientes de diseño — no bloquean)

| Prioridad | Ítem | Motivo |
|-----------|------|--------|
| Alta | Rotar secretos en `.env` local (Cloudinary, Stripe, VAPID) + mover a gestor de secretos | claves en texto plano en disco |
| Alta | Cloudflare/WAF delante de Caddy | DDoS L7 antes de tráfico real |
| Alta | Pentest externo | validación independiente antes de escalar |
| Media | Rotación programada de `device_token` + binding de giro al kiosco | el token viaja en URL |
| Media | Postgres RLS para aislamiento multi-tenant en profundidad | defensa en capas sobre los filtros ORM |
| Media | k6 baseline en CI nocturno + presupuestos de latencia | eficiencia medida |
| Media | Completar textos legales de `/terminos` y `/privacidad` (placeholders ya publicados) | requisito legal previo al lanzamiento |
| Baja | SBOM (cyclonedx) + firma de imágenes (cosign) | supply chain avanzada |
| Baja | E2E Playwright + contract tests (schemathesis) | cobertura de flujo real |

### Implementado en la fase "megaplan" (fuera del catálogo original)

- **OTP cliente** (`OtpCode` + `services/otp.py` + `POST /auth/cliente/otp/verificar`): 2do factor tras tel+CI; código hasheado, TTL 5 min, lockout a 5 intentos con commit independiente (bug real corregido: los intentos deben persistir aunque el request falle).
- **Antifraude de emisión** (`services/fraude.py`): umbrales por emisor/hora y cliente/día, integrados en el choke-point `puntos.otorgar()` → audit + contador Prometheus `yapai_alertas_fraude_total`.
- **Audit hash-chain**: `prev_hash`/`hash` por fila en `audit_log` + `scripts/verify_audit_chain.py` — detecta reescritura/reordenamiento.
- **Cookies HttpOnly**: `AUTH_TRANSPORT` bearer|cookie|both, `COOKIE_DOMAIN`, guard CSRF por `X-Requested-With`, refresh/logout vía cookie; los 3 SPAs dejaron localStorage.
- **Pasivo de puntos**: `GET /socio/metricas/reportes/pasivo-puntos` — pasivo neto por tenant, top clientes y por sucursal (solo owner).
- **Purge de tokens**: job diario `jobs/limpieza.py` (solo en el runner separado).
- **PII cliente**: export GDPR + anonimización al eliminar cuenta (push suscripciones borradas, refresh revocados, CI/teléfono → placeholders, ledger intacto).
- **MFA superadmin**: `REQUIRE_SUPERADMIN_2FA` — prod hace fail-fast si false; dep `require_superadmin_2fa` en todas las rutas `/admin`.
- **Stripe webhook**: firma HMAC-SHA256 con tolerancia 5 min (anti-replay), idempotente vía `eventos_stripe.event_id` UNIQUE, `invoice.paid`→pagada, `payment_failed`→vencida+suspensión por gracia, `subscription.deleted`→suspende tenant.
- **Carreras**: stock de premio con UPDATE condicional (`stock>0`) → imposible negativo/doble canje; giros de ruleta bajo `SELECT FOR UPDATE` del cliente; tests `test_races.py`.
| Baja | HA multi-réplica + Postgres en CI | cuando el volumen lo pida |

## Rotación de secretos — guía rápida

1. `JWT_SECRET`: `python -c "import secrets; print(secrets.token_urlsafe(48))"` → invalida todas las sesiones.
2. `POSTGRES_PASSWORD`, `SEED_ADMIN_PASSWORD`: en `deploy/.env.production` + `docker compose up -d`.
3. Cloudinary/Stripe/VAPID: consola del proveedor → `.env` → redeploy.
4. Regla: todo secreto que haya tocado un canal inseguro (chat, repo, captura) se considera comprometido → rotar.
