# ADR-0002: Jobs periódicos como proceso separado

- **Fecha:** 2026-11-07
- **Estado:** Aceptado

## Contexto

Los jobs de expiración de pases y facturación corrían como tareas asyncio en el
`lifespan` de la API. Al escalar a N workers/instancias (necesario para HA y
rendimiento), los jobs se ejecutaban N veces: doble facturación, doble email,
doble liberación de saldo.

## Decisión

- La API corre con `JOBS_ENABLED=false` en producción.
- Un servicio `jobs` dedicado (misma imagen, sin puertos) ejecuta
  `python -m app.jobs.runner` con ambos loops.
- En desarrollo/single-instance `JOBS_ENABLED=true` mantiene el comportamiento
  anterior dentro de la API.
- Cada loop sigue disponible standalone: `python -m app.jobs.expiracion`,
  `python -m app.jobs.facturacion` (una pasada, para cron/debug).

## Consecuencias

- Horizontalidad real de la API (stateless, sin jobs duplicados).
- Un único ejecutor de jobs por despliegue; si se necesitan réplicas del runner
  en el futuro, usar advisory lock de Postgres (`pg_advisory_lock`) — no
  implementado aún.
