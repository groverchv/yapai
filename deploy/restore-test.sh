#!/bin/sh
# Test de restauración: verifica que el último backup es restaurable.
# Corre contra una base TEMPORAL en el mismo contenedor — no toca yapai_db.
#
# Uso:  ./restore-test.sh [archivo_backup]     (default: el más reciente)
# Cron semanal recomendado:  15 4 * * 0  /opt/yapai/deploy/restore-test.sh
set -eu

CONTAINER="${CONTAINER:-yapai-db-1}"
DESTINO="${DESTINO:-/opt/yapai/backups}"
USER="${POSTGRES_USER:-yapai}"
DB_TMP="yapai_restore_test"

FILE="${1:-$(ls -t "$DESTINO"/yapai_*.sql.gz* 2>/dev/null | head -1)}"
[ -n "$FILE" ] || { echo "[restore-test] no hay backups en $DESTINO"; exit 1; }
echo "[restore-test] probando $FILE"

case "$FILE" in
	*.gpg) DUMP="gpg --batch --yes --decrypt --passphrase \"$GPG_PASSPHRASE\" \"$FILE\" | gunzip" ;;
	*)     DUMP="gunzip -c \"$FILE\"" ;;
esac

docker exec "$CONTAINER" psql -U "$USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_TMP" >/dev/null
docker exec "$CONTAINER" psql -U "$USER" -d postgres -c "CREATE DATABASE $DB_TMP" >/dev/null

if eval "$DUMP" | docker exec -i "$CONTAINER" psql -U "$USER" -d "$DB_TMP" -v ON_ERROR_STOP=1 -q; then
	TABLAS=$(docker exec "$CONTAINER" psql -U "$USER" -d "$DB_TMP" -tAc \
		"SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
	echo "[restore-test] OK — $TABLAS tablas restauradas"
	docker exec "$CONTAINER" psql -U "$USER" -d postgres -c "DROP DATABASE $DB_TMP" >/dev/null
else
	echo "[restore-test] FALLÓ la restauración de $FILE" >&2
	docker exec "$CONTAINER" psql -U "$USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_TMP" >/dev/null
	exit 1
fi
