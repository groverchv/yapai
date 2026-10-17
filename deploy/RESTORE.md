# Restore de Postgres — YAPAI

Un backup que nunca se restauró no es un backup. Procedimiento probado:

## Restore completo (misma infra)

1. Parar la API para que no escriba durante el restore:
   ```bash
   docker compose -f deploy/docker-compose.prod.yml stop api
   ```
2. Restaurar el dump (incluye `--clean --if-exists`, recrea el esquema):
   ```bash
   gunzip -c /opt/yapai/backups/yapai_FECHA.sql.gz | \
     docker exec -i deploy-db-1 psql -U yapai -d yapai_db
   ```
3. Levantar la API (re-corre migraciones por si el dump es de otra versión):
   ```bash
   docker compose -f deploy/docker-compose.prod.yml up -d api
   docker compose -f deploy/docker-compose.prod.yml logs -f api
   ```
4. Verificar: `GET /health` → 200, login admin, listar socios.

## Restore de validación (sin tocar producción)

```bash
# Base temporal en el mismo host
docker run -d --name pg-restore-test -e POSTGRES_PASSWORD=x -e POSTGRES_DB=test postgres:16-alpine
gunzip -c backup.sql.gz | docker exec -i pg-restore-test psql -U postgres -d test
docker exec pg-restore-test psql -U postgres -d test -c "SELECT count(*) FROM tenants;"
docker rm -f pg-restore-test
```

## DR (disaster recovery) — objetivo

- Copiar `/opt/yapai/backups/` fuera del servidor (S3/B2/rclone) — pendiente de credenciales.
- RPO objetivo: 24h (backup diario) · RTO objetivo: < 1h con este runbook.
