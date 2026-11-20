# Runbook operativo — YAPAI

Procedimientos para operar la plataforma en producción.

## 1. Secretos obligatorios antes de lanzar

| Variable | Dónde | Notas |
|---|---|---|
| `JWT_SECRET` | api + jobs | `python -c "import secrets; print(secrets.token_urlsafe(48))"` — >=32 chars. Si falta, el contenedor **no arranca** (validador de producción) |
| `DATABASE_URL` | api + jobs | `postgresql+psycopg://user:pass@db:5432/yapai` |
| `SENTRY_DSN` | api | Vacío = sin reporte de errores |
| `REDIS_URL` | api | `redis://redis:6379/0` — rate limiting compartido entre workers |
| `SEED_ADMIN_PASSWORD` | api (primer boot) | Obligatorio ≠ default en prod. Cambiar la clave tras el primer login |
| `CORS_ORIGINS` | api | Dominios exactos, sin `*` — el validador lo exige |
| `DOMAIN` | caddy | TLS automático vía Let's Encrypt |

Rotación de `JWT_SECRET`: invalida todos los tokens activos → avisar, rotar en horario
de bajo tráfico, todos re-loguean.

**Fail-fast de producción:** si `ENV=production` y falta configuración segura,
la API aborta el arranque con la lista de problemas. Eso es intencional — nunca
correr prod con defaults.

**IP real del cliente:** la API corre con `--proxy-headers --forwarded-allow-ips '*'`.
El rate limiting y los logs usan la IP del `X-Forwarded-For` de Caddy. Funciona
solo porque `api:8000` **no se publica fuera de la red docker** — si alguna vez
se expone directo, restringir la lista o los limiters quedan bypaseables.

## 2. Deploy

```bash
cd deploy
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
docker compose exec api alembic upgrade head   # migraciones (el CMD ya las corre, idempotente)
docker compose exec api python -m app.seed --no-demo  # base: superadmin+planes (solo primer deploy)
```

Verificación post-deploy: `/health` en api.{$DOMAIN}, login en app./admin., kiosco público,
`docker compose logs jobs` muestra el runner de jobs corriendo.

## 3. Backups

`backup.sh` corre por cron (pg_dump gzip, retención 14 días; con `GPG_PASSPHRASE`
definido cifra AES256). `restore-test.sh` restaura el último backup en una base
temporal y verifica conteo de tablas — correr **semanal por cron** y revisar su
log. Restauración manual documentada en `RESTORE.md`.

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

## 6. Endurecimiento aplicado (auditoría 2026-11 — ver AUDITORIA.md)

- Headers de seguridad: middleware en API + bloque `headers_seguridad` en Caddy para frontends.
- 2FA TOTP disponible para superadmin y owner (perfil → "Verificación en dos pasos").
- Rate limiting por IP real (X-Forwarded-For de Caddy): login 10/min, cliente 5/5min,
  PIN 5/15min, signup 5/h, 2FA 5/5min, recuperación 3/h, refresh/logout 20/min,
  kiosco 30/5min por pantalla.
- Fail-fast de config en producción; `/docs` oculto; seed demo prohibido en prod.
- Refresh tokens con detección de reuso (robo → revoca todas las sesiones del sujeto).
- Uploads: magic bytes + máx 5MB + sin SVG. Ruleta con RNG criptográfico.
- Contenedores no-root; deps fijadas (`==`) + `requirements.lock` con hashes;
  auditoría semanal CI (pip-audit, npm audit, gitleaks, Trivy, dependabot).
- Contraseñas Argon2 (≥12 chars en signup/reset/onboarding), movimientos contables
  y audit_log con triggers anti UPDATE/DELETE.
- Jobs periódicos en servicio `jobs` separado (API escala sin duplicarlos).
