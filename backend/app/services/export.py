import csv
import io
from collections.abc import Iterable

from fastapi.responses import StreamingResponse


def csv_response(filename: str, headers: list[str], rows: Iterable[Iterable]) -> StreamingResponse:
    """Genera un CSV en streaming a partir de filas ya materializadas."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
