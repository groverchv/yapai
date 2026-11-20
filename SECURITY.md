# Política de seguridad — Yapai

## Reportar una vulnerabilidad

Si encuentras una vulnerabilidad, **no abras un issue público**.

- Email: **seguridad@yapai.com**
- Incluye: descripción, pasos para reproducir, impacto estimado y (si aplica) PoC.
- Respondemos en **72 h** y apuntamos a un fix o mitigación en **14 días** según severidad.
- `security.txt` en cada dominio: `/.well-known/security.txt`.

## Alcance

En scope: API (`api.*`), portales (`app.*`, `admin.*`, `*.apex`), kioscos,
backends y despliegue documentado en `deploy/`.

Fuera de scope: denegación de servicio volumétrica, ingeniería social,
vulnerabilidades de terceros sin impacto demostrado en Yapai, y reportes
automáticos sin análisis.

## Postura de seguridad (estado actual)

- Autenticación: JWT corto (15 min) + refresh rotativo hasheado con detección de
  reuso (robo → revoca la familia). Argon2id para passwords y PINs.
- 2FA TOTP disponible para usuarios del sistema.
- Rate limiting por IP real (tras proxy) con Redis en producción.
- Cabeceras de seguridad en API y frontends; CSP estricta.
- Validación de configuración en arranque: `ENV=production` con defaults
  inseguros **aborta el despliegue**.
- Sin endpoints sin autenticar salvo: health, kiosco (device_token), signup/login.
- Imágenes Docker no-root, deps fijadas con lockfile+hashes, auditoría
  semanal en CI (pip-audit, npm audit, gitleaks, Trivy).

## Versiones soportadas

Solo `main` recibe fixes de seguridad. Las releases se etiquetan por fecha.
