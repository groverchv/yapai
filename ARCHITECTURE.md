# Arquitectura — Yapai

SaaS multi-tenant de fidelización: comercios (tenants) otorgan puntos a sus
clientes, que los canjean por premios. Tres portales web + kioscos en tienda +
una API.

## Mapa de componentes

```
                        ┌─────────────┐
   cliente (PWA)   ───► │             │
   apex / www           │             │
                        │             │
   socio (owner/cajero) │    CADDY    │   TLS automático, headers,
   app.*                │  (proxy)    │   /metrics 404 al público
                        │             │
   admin (superadmin)   │             │
   admin.*              └──────┬──────┘
                               │
              ┌────────────────┼──────────────────┐
              ▼                ▼                  ▼
        ┌──────────┐    ┌───────────┐      ┌───────────┐
        │ SvelteKit│ ×3 │ FastAPI   │      │  jobs     │
        │ SPA (node)│   │ api       │      │ (runner)  │
        └──────────┘    └─────┬─────┘      └─────┬─────┘
                              │                  │
                       ┌──────┴──────┐    ┌──────┴──────┐
                       ▼             ▼    ▼             ▼
                   ┌───────┐    ┌────────┐        (misma imagen,
                   │Postgres│   │ Redis  │         JOBS_ENABLED
                   │  16    │   │  7     │         =false en api)
                   └───────┘    └────────┘
```

## Decisiones estructurales

- **Monolito modular** (FastAPI): routers por dominio (`admin/`, `socio/`,
  `cliente/`, `caja/`, `kiosco`), servicios reutilizables en `app/services/`,
  modelos SQLAlchemy 2.x. Correcto para el tamaño del equipo y el dominio;
  no microservicios — ver ADR-0005.
- **Multi-tenancy por `tenant_id`** en cada fila + filtros obligatorios en
  queries. Tests cross-tenant en `tests/test_aislamiento.py` verifican que un
  owner jamás toca recursos ajenos. Roadmap: Postgres RLS como segunda capa.
- **Cliente ≠ Usuario**: `Cliente` (app final, login tel+CI) y `Usuario`
  (superadmin/owner/cajero, email+password+TOTP) son sujetos distintos con
  prefijos `c:`/`u:` en el `sub` del JWT.
- **Ledger append-only**: `movimientos_puntos` y `audit_log` tienen triggers de
  inmutabilidad en DB (UPDATE/DELETE prohibidos) — la verdad financiera no se
  edita, se compensa.
- **Jobs en proceso separado** (`app.jobs.runner`): la API puede escalar a N
  réplicas sin duplicar facturación ni expiración de pases.
- **Esquema solo por Alembic**: `create_all` no existe en producción; las
  migraciones son append-only (nunca se borran — soportan upgrades de cualquier
  versión histórica, clave para 50 años).
- **PostgREST eliminado** (2026-11): era capa REST extra sin consumidores en
  producción y conexión superuser — superficie de ataque sin beneficio.

## Flujo de autenticación

1. Login → access JWT (15 min) + refresh opaco (30 días) hasheado en DB.
2. `POST /auth/refresh` rota el refresh (el viejo queda revocado).
3. Reuso de un refresh revocado → **revocación de toda la familia de sesiones**.
4. Frontends guardan tokens en memoria/localStorage (SPA); roadmap: cookies
   httpOnly + BFF.

## Configuración (`app/core/config.py`)

Una sola `Settings` (pydantic-settings, `extra="forbid"`). En `ENV=production`
el validador **aborta** si hay defaults inseguros: `JWT_SECRET`, `CORS=*`,
`DEBUG`, `POSTGRES_PASSWORD`, `SEED_ADMIN_PASSWORD`, `SEED_DEMO`.

## Datos sensibles

- PII: `clientes` (CI, teléfono, nombre), `usuarios` (email, nombre).
- Secretos: solo en variables de entorno — nunca en el repo (gitleaks en CI).
- Backups: `deploy/backup.sh` (gzip + GPG opcional) → `restore-test.sh` semanal.

## Puertos y superficie

Públicos (vía Caddy): 80/443. Internos docker: `api:8000` (jamás publicar),
`postgres:5432`, `redis:6379`, frontends `:3000`.
