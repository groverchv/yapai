# Despliegue de producción — YAPAI

## Arquitectura

```
Internet ──TLS──> Caddy (443)
                    ├── yapai.com          → cliente:3000 (PWA cliente, SvelteKit node)
                    ├── app.yapai.com      → socio:3000   (SvelteKit node)
                    ├── admin.yapai.com    → admin:3000   (SvelteKit node)
                    ├── api.yapai.com      → api:8000     (FastAPI)
                    └── www.yapai.com      → redirect apex
api ──> db (postgres:16, volumen pgdata)
api ──> redis (rate limiting distribuido, volumen redisdata)
```

`/metrics` queda bloqueado en el proxy (solo accesible dentro de la red Docker
para Prometheus/Grafana futuro).

## Puesta en marcha

1. **DNS**: registros A para `api.`, `app.`, `admin.`, `@` y `www` apuntando al servidor.
2. **Secretos**: `cp deploy/.env.production.example deploy/.env.production` y completar
   (generar `JWT_SECRET` con `secrets.token_urlsafe(48)`; el par `VAPID_*` con
   `py-vapid --gen` — sin él las notificaciones push simplemente no se envían).
3. **Arranque**:
   ```bash
   docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.production up -d --build
   ```
   El contenedor `api` corre `alembic upgrade head` + seed idempotente antes de servir.
4. **Verificación**:
   ```bash
   curl https://api.yapai.com/health
   docker compose -f deploy/docker-compose.prod.yml logs -f api
   ```
   Caddy emite los certificados TLS automáticamente al primer acceso.

## Backups

`deploy/backup.sh` hace `pg_dump` comprimido con retención de 14 días. Cron en el host:

```cron
0 3 * * * POSTGRES_DB=yapai_db POSTGRES_USER=yapai CONTAINER=deploy-db-1 /opt/yapai/deploy/backup.sh >> /var/log/yapai-backup.log 2>&1
```

**Probar el restore trimestralmente** — ver `RESTORE.md`.

## Observabilidad

- **Logs**: `LOG_JSON=true` en prod → cada request emite una línea JSON con
  `request_id`, método, ruta, status, ms e IP. Ver con `docker compose logs api`.
- **Métricas**: `GET /metrics` formato Prometheus (conteo y latencia por ruta) —
  scraping solo desde la red interna.
- **Sentry**: definir `SENTRY_DSN` y se activa automáticamente (errores 5xx + tracing).
- **Healthcheck**: `GET /health` sin auth para el balanceador/monitor de uptime.

## Escalado posterior (cuando haga falta)

- Postgres gestionado (RDS/Neon) elimina la necesidad de backups propios.
- CDN delante de los 3 frontends para assets estáticos.
- Worker separado para envío de push masivo (hoy se envía en hilo por evento).
