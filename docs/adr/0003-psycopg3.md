# ADR-0003: Migrar de psycopg2-binary a psycopg 3

- **Fecha:** 2026-11-07
- **Estado:** Aceptado

## Contexto

`psycopg2-binary` está oficialmente desaconsejado para producción (binarios
empaquetados con libpq estático que puede desactualizarse). psycopg 3 es la
rama activa: mejor soporte de tipos, pipeline mode, y es la vía con soporte
largo.

## Decisión

`psycopg[binary]==3.3.8` reemplaza a `psycopg2-binary` y al `asyncpg` sin uso.
URLs: `postgresql+psycopg://…` (config y compose prod actualizados).

## Consecuencias

- SQLAlchemy 2.x soporta psycopg 3 nativamente; los tests corren sobre SQLite
  y no dependen del driver.
- En upgrades futuros de libpq, psycopg 3 binary se mantiene al día con
  frecuencia mayor que psycopg2-binary.
