# ADR-0004: Login de cliente con teléfono + CI — riesgo aceptado con mitigaciones

- **Fecha:** 2026-11-07
- **Estado:** Aceptado (con mitigaciones; OTP en roadmap)

## Contexto

El cliente final (app/PWA) entra con **teléfono + cédula de identidad**, sin
contraseña ni OTP. Decisión de producto para minimizar fricción en kioscos y
registro (personas no técnicas, contexto Bolivia).

El CI y el teléfono son datos semi-públicos → el riesgo real es account
takeover para robar puntos o datos personales del cliente.

## Decisión

Mantener el flujo por ahora con mitigaciones:

- `cliente_login_limiter`: 5 intentos / 5 min por IP (más estricto que el login
  de usuarios).
- Respuesta genérica 401 sin revelar cuál campo falló.
- Saldo/transacciones quedan auditadas en `audit_log` y el ledger es
  append-only — un robo queda trazado y reversible.

## Pendiente (roadmap alta prioridad)

- PIN opcional de 4-6 dígitos o OTP por WhatsApp/SMS para cuentas que lo
  activen; obligatorio si el cliente tiene saldo alto.
- Alerta de "login desde dispositivo nuevo" por push.
