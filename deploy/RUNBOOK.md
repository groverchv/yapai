# Runbook operativo — YAPAI

Procedimientos para operar la plataforma en producción.

## 1. Secretos obligatorios antes de lanzar

| Variable | Dónde | Notas |
|---|---|---|
| `JWT_SECRET` | api | Generar: `openssl rand -hex 32`. El default de dev **no** sirve para prod |
| `DATABASE_URL` | api | `postgresql+psycopg://user:pass@db:5432/yapai` |
| `SENTRY_DSN` | api + build Flutter | Vacío = sin reporte de errores |
| `REDIS_URL` | api | `redis://redis:6379/0` — rate limiting compartido entre workers |
| `SEED_ADMIN_*` | api (primer boot) | Cambiar la clave tras el primer login |
| `DOMAIN` | caddy | TLS automático vía Let's Encrypt |

Rotación de `JWT_SECRET`: invalida todos los tokens activos → avisar, rotar en horario
de bajo tráfico, todos re-loguean.

## 2. Deploy

```bash
cd deploy
docker compose -f docker-compose.prod.yml up -d --build
docker compose exec api alembic upgrade head   # migraciones
```

Verificación post-deploy: `/health` en api.{$DOMAIN}, login en app./admin., kiosco público.

## 3. Backups

`backup.sh` corre por cron (pg_dump gzip, retención 14 días). Restauración probada
documentada en `RESTORE.md`. **Probar un restore en staging cada mes.**

## 4. Monitoreo

- Métricas: `api:8000/metrics` (solo red interna — Caddy devuelve 404 al público).
  Scrapear con Prometheus: `yapai_http_requests_total`, latencias por ruta.
- Logs: JSON con `request_id` cuando `LOG_JSON=true` → correlacionar con el header
  `X-Request-ID` que devuelve cada respuesta.
- Errores: Sentry (backend + app Flutter con `--dart-define SENTRY_DSN`).
- Alertas mínimas recomendadas: tasa de 5xx > 1%, p95 > 1s, disco del host de DB > 80%.

## 5. Incidentes frecuentes

### Socio bloqueado por 2FA (perdió el teléfono)
```sql
UPDATE usuarios SET totp_habilitado=false, totp_secret=NULL
WHERE email='owner@negocio.com';
```
Verificar identidad del solicitante antes (regla: que responda desde el correo registrado
o valide datos del tenant). La acción queda en audit_log si se hace por admin.

### Rate limiter bloquea legítimos
Con `REDIS_URL` vacío los límites son por instancia — con N workers el límite efectivo
es N×el configurado. Solución: definir `REDIS_URL`. Si Redis cae, el limiter degrada
a "permitir" (fail-open) y loguea el error — no tumba el servicio.

### Tenant suspendido por impago
Revisar `facturas_plan` del tenant. Tras registrar el pago
(`POST /admin/facturacion/{id}/pagar`), reactivar con
`POST /admin/socios/{id}/reactivar`.

### Migración fallida en deploy
`alembic downgrade -1`, restaurar backup si hay corrupción, fix, re-subir.
Nunca correr `upgrade head` contra una DB sin backup reciente.

## 6. Endurecimiento aplicado

- Headers de seguridad: middleware en API + bloque `headers_seguridad` en Caddy para frontends.
- 2FA TOTP disponible para superadmin y owner (perfil → "Verificación en dos pasos").
- Rate limiting: login 10/min, PIN 5/15min, signup 5/h, código 2FA 5/5min — por IP, Redis-ready.
- Contraseñas Argon2, movimientos contables y audit_log con triggers anti UPDATE/DELETE.
