#!/usr/bin/env bash
# Dev local: corre la API contra la SQLite de demo (yapai_dev.db)
# con hot-reload. Uso: ./dev.sh (desde la carpeta backend)
export DATABASE_URL="sqlite:///./yapai_dev.db"
exec python -m uvicorn app.main:app --reload --port 8000
