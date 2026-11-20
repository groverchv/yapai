#!/bin/sh
# Backup diario de Postgres — correr vía cron en el host:
#   0 3 * * * /opt/yapai/deploy/backup.sh >> /var/log/yapai-backup.log 2>&1
# Genera /backups/yapai_YYYYMMDD_HHMMSS.sql.gz y retiene 14 días.
#
# Si GPG_PASSPHRASE está definido, el dump se cifra simétricamente
# (yapai_*.sql.gz.gpg) — recomendado: el backup contiene PII de clientes.
set -eu

CONTAINER="${CONTAINER:-yapai-db-1}"
DESTINO="${DESTINO:-/opt/yapai/backups}"
RETENCION_DIAS="${RETENCION_DIAS:-14}"
DB="${POSTGRES_DB:-yapai_db}"
USER="${POSTGRES_USER:-yapai}"

mkdir -p "$DESTINO"
STAMP=$(date +%Y%m%d_%H%M%S)

if [ -n "${GPG_PASSPHRASE:-}" ]; then
	FILE="$DESTINO/yapai_$STAMP.sql.gz.gpg"
	docker exec "$CONTAINER" pg_dump -U "$USER" -d "$DB" --clean --if-exists \
		| gzip | gpg --batch --yes --symmetric \
			--passphrase "$GPG_PASSPHRASE" --cipher-algo AES256 -o "$FILE"
else
	FILE="$DESTINO/yapai_$STAMP.sql.gz"
	docker exec "$CONTAINER" pg_dump -U "$USER" -d "$DB" --clean --if-exists | gzip > "$FILE"
fi
echo "[backup] $FILE ($(du -h "$FILE" | cut -f1))"

find "$DESTINO" -name 'yapai_*.sql.gz*' -mtime +"$RETENCION_DIAS" -delete
echo "[backup] retención ${RETENCION_DIAS}d aplicada"
