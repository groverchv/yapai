FROM python:3.13-slim

# Usuario no-root para el proceso de la app
RUN groupadd -r yapai && useradd -r -g yapai yapai

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
USER yapai

EXPOSE 8000

# Migraciones + server. El seed es manual/intencional:
#   docker exec <api> python -m app.seed          (base: admin+planes+categorías)
#   docker exec <api> python -m app.seed --demo   (solo fuera de producción)
#
# --proxy-headers + forwarded-allow-ips='*': la IP real del cliente llega por
# X-Forwarded-For del proxy (Caddy). Seguro solo porque este puerto NO se
# publica fuera de la red docker — si se expone directo, restringir la lista.
CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*'"]
