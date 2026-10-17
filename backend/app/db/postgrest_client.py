import httpx
from typing import Any, Dict, List, Optional
from app.core.config import settings

class PostgrestClient:
    """Cliente para interactuar con PostgREST si se utiliza como capa de API sobre PostgreSQL"""
    def __init__(self, base_url: str = settings.POSTGREST_URL):
        self.base_url = base_url.rstrip("/")

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/{endpoint.lstrip('/')}", params=params)
            response.raise_for_status()
            return response.json()

    async def post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/{endpoint.lstrip('/')}", json=data)
            response.raise_for_status()
            return response.json() if response.content else None

postgrest_client = PostgrestClient()
