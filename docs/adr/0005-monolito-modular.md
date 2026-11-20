# ADR-0005: Monolito modular antes que microservicios

- **Fecha:** 2026-11-07
- **Estado:** Aceptado

## Contexto

Para un proyecto pensado a 50 años se evaluó dividir en microservicios. La
comparación con otro proyecto del entorno (4 backends heterogéneos) mostró el
costo: orquestación, latencia, inconsistencia de datos y carga operativa.

## Decisión

Un solo backend FastAPI organizado por dominios:

- `routers/{admin,socio,cliente,caja,kiosco}` — superficie por rol
- `services/` — lógica de negocio reutilizable
- `models/` — esquema único, `tenant_id` como frontera de aislamiento
- `jobs/` — proceso separado (única pieza "distribuida" justificada)

## Consecuencias

- Deploy y rollback atómicos; una sola versión de esquema; tests de punta a
  punta triviales.
- Escalamiento horizontal por réplicas stateless; el cuello de botella futuro
  será la DB (escalar Postgres, no fragmentar la app).
- Si un dominio crece demasiado (p. ej. push/media), extraerlo es posible:
  los límites de módulo ya existen.
