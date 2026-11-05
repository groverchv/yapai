# Dev local: corre la API contra la SQLite de demo (yapai_dev.db)
# con hot-reload. Uso: .\dev.ps1  (desde la carpeta backend)
$env:DATABASE_URL = "sqlite:///./yapai_dev.db"
python -m uvicorn app.main:app --reload --port 8000
