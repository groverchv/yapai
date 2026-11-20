# ADR-0001: Eliminar PostgREST del stack

- **Fecha:** 2026-11-07
- **Estado:** Aceptado

## Contexto

El proyecto incluía PostgREST como "capa REST alternativa" sobre PostgreSQL.
En desarrollo corría con `PGRST_DB_ANON_ROLE: postgres` (superusuario) y puerto
publicado, y un endpoint `/api/v1/dev/postgrest-proxy/{tabla}` lo exponía
**sin autenticación**. En producción el servicio ni siquiera existía en el
compose — FastAPI/SQLAlchemy cubre todas las necesidades.

## Decisión

Eliminar PostgREST por completo: servicio del compose dev, router `dev.py`,
cliente `db/postgrest_client.py` y variable `POSTGREST_URL`.

## Consecuencias

- Superficie de ataque reducida: no hay una segunda vía de acceso a la DB.
- Una sola fuente de verdad de acceso a datos: SQLAlchemy + Alembic.
- Si en el futuro se necesita una API auto-generada sobre la DB, evaluar con
  roles dedicados read-only y auth — nunca superusuario.

## Alternativas consideradas

- Mantener PostgREST con rol read-only: rechazada — sin consumidores reales,
  complejidad y riesgo sin beneficio.
