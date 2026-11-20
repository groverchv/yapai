import unicodedata
from datetime import datetime, timezone


def slugify(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace(" ", "-")


def aware_utc(dt: datetime | None) -> datetime | None:
    """Normaliza un datetime posiblemente naive (SQLite) a UTC aware. None pasa tal cual."""
    return dt if dt is None or dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
