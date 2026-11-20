# Yapai - Ecosistema de Proyectos

Este repositorio contiene la arquitectura completa de la solución Yapai:

| Componente | Carpeta | Tecnologías | Descripción |
|---|---|---|---|
| **Backend** | [`backend/`](file:///d:/Yapai/backend) | Python 3.13, FastAPI, SQLAlchemy, Alembic, Docker | API REST sobre PostgreSQL |
| **Frontend Administrador** | [`frontend_administrador/`](file:///d:/Yapai/frontend_administrador) | SvelteKit, TypeScript, Vite | Panel web para administración general |
| **Frontend Socio** | [`frontend_socio/`](file:///d:/Yapai/frontend_socio) | SvelteKit, TypeScript, Vite | Portal web para socios comerciales |
| **Frontend Cliente** | [`frontend_cliente/`](file:///d:/Yapai/frontend_cliente) | SvelteKit, TypeScript, Vite | Web del cliente: billetera de puntos, explorar, pases QR, perfil |

---

## 1. Backend (FastAPI + PostgreSQL)

### Requisitos y Ejecución
1. Crear entorno virtual e instalar dependencias:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```
   `requirements.txt` tiene versiones fijadas (`==`); `requirements.lock` lleva
   el árbol completo con hashes (pip-compile) para builds verificables.
2. Base de datos — elige una opción:
   - **Con Docker (PostgreSQL):** `docker compose up -d` y deja `DATABASE_URL` vacío en `.env`.
   - **Sin Docker (SQLite dev):** define `DATABASE_URL=sqlite:///./yapai_dev.db` en `.env`.
3. Aplicar migraciones y datos semilla:
   ```bash
   python -m alembic upgrade head
   python -m app.seed            # base + demo (dev); --no-demo solo base
   ```
   Credenciales demo: `admin@yapai.com` / `Admin123!` (superadmin) · `owner@demo.com` / `Owner123!` · `cajero@demo.com` / `Cajero123!` · cliente CI `12345678` tel `70000001`.
4. Iniciar el servidor FastAPI:
   ```bash
   # Con hot-reload y SQLite de demo (recomendado en dev):
   .\dev.ps1          # Windows
   ./dev.sh           # Linux/macOS

   # O manual:
   python run.py
   ```
   - Swagger / Documentación interactiva: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Endpoint raíz: [http://localhost:8000/](http://localhost:8000/)

5. Tests de invariantes (reglas de negocio):
   ```bash
   pip install -r requirements-dev.txt
   python -m pytest tests/
   ```

**Hardening incluido (Fase 6 + auditoría 2026-11):** rate limits en todos los
endpoints sensibles (login, cliente, PIN, signup, recuperación, refresh, kiosco)
por IP real tras proxy, triggers de inmutabilidad a nivel DB sobre
`movimientos_puntos` y `audit_log` (migración `a1b2c3d4e5f6`, Postgres + SQLite),
validador de configuración que **aborta el arranque en producción** con defaults
inseguros (`ENV=production` + `JWT_SECRET`/`CORS`/`DEBUG`/passwords default),
refresh tokens con detección de reuso (robo → revoca la familia), uploads con
validación de magic bytes, contenedores no-root, deps fijadas con hashes y
auditoría semanal en CI (pip-audit, npm audit, gitleaks, Trivy). Jobs periódicos
en proceso separado (`python -m app.jobs.runner`). Ver
[`AUDITORIA.md`](file:///d:/Yapai/AUDITORIA.md), [`SECURITY.md`](file:///d:/Yapai/SECURITY.md)
y [`ARCHITECTURE.md`](file:///d:/Yapai/ARCHITECTURE.md).

---

## 2. Frontend Administrador (SvelteKit + Tailwind)
```bash
cd frontend_administrador
npm install
npm run dev          # http://localhost:5173 (o 5174 si está ocupado)
```
Login con el superadmin del seed: `admin@yapai.com` / `Admin123!`.

---

## 3. Frontend Socio (SvelteKit + Tailwind)
```bash
cd frontend_socio
npm install
npm run dev -- --port 5175   # http://localhost:5175
```
Login con el owner del seed: `owner@demo.com` / `Owner123!`.
El cajero (`cajero@demo.com` / `Cajero123!`) entra a `/terminal`: canje de pases, bonus por compra y habilitación de pantalla.

---

## 4. Web Cliente (SvelteKit + Tailwind)
```bash
cd frontend_cliente
npm install
npm run dev -- --port 5176   # http://localhost:5176
```
Login con el cliente del seed: teléfono `70000001`, CI `12345678` (o registra uno nuevo en el kiosco).
`PUBLIC_API_BASE` apunta al backend (default `http://localhost:8000/api/v1`); `PUBLIC_DEMO=1` muestra el botón de usuario demo.

**Kiosco (pantalla del local):** abre `http://localhost:5175/kiosco/kiosco-demo-001` — primero habilítala con el PIN de caja (`POST /caja/pantalla/habilitar`, PIN `4521` del seed).
# yapai
