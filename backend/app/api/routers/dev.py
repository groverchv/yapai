from fastapi import APIRouter

from app.db.postgrest_client import postgrest_client

router = APIRouter()


@router.get("/postgrest-proxy/{table_name}")
async def proxy_postgrest(table_name: str):
    """Consulta de prueba a través del cliente PostgREST."""
    try:
        data = await postgrest_client.get(table_name)
        return {"source": "postgrest", "table": table_name, "data": data}
    except Exception as e:
        return {"status": "error", "message": f"PostgREST no disponible o error: {str(e)}"}
