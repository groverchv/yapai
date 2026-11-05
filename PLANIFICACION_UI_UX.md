# Super Planificación UI/UX — YAPAI

> Estado base: sesión de optimización completada (responsive nativo, PWA ×3,
> Web Push, errores en español, scrollbars ocultos, grids adaptativos,
> deploy prod + CI). Este documento planifica el **siguiente nivel**: de
> "funcional y correcto" a "producto que se siente premium y retiene".

---

## 1. Auditoría del estado actual

| Superficie | Estado | Gaps detectados (auditoría de código) |
|---|---|---|
| **Cliente** (`frontend_cliente`) | Responsive, PWA, push, grids adaptativos | ❌ Sin skeletons (solo `Spinner` centrado) · ❌ Sin micro-interacciones · ❌ Sin celebración al ganar puntos/canjear · ❌ Sin estado offline · ❌ Sin onboarding del cliente |
| **Socio** (`frontend_socio`) | Drawer móvil, KPIs, i18n es/en, 7 skeletons | ❌ Sin checklist de activación post-registro · ❌ Empty states sin CTA clara · ❌ Terminal POS sin modo "atención rápida" · ❌ Formularios largos sin progreso |
| **Admin** (`frontend_administrador`) | Drawer móvil, KPIs 2-col, 4 skeletons | ❌ Tablas densas sin acciones bulk · ❌ Sin filtros guardados · ❌ Detalle de socio lineal sin quick actions |
| **Kiosco** (`/kiosco/[token]`) | QR + registro + consentimiento | ❌ Sin modo attract-loop (screensaver) · ❌ Sin recuperación si cae internet · ❌ Tipografía no optimizada para distancia |
| **Transversal** | — | ❌ Dark mode inexistente · ❌ Sin auditoría a11y (WCAG AA) · ❌ Sin motion design consistente · ❌ i18n solo en socio/admin (cliente hardcoded ES — decisión OK por ahora) |

---

## 2. Principios rectores

1. **El cliente nunca espera** — skeletons, optimistic UI, cache en SW.
2. **El socio vende en 30 segundos** — el flujo caja→otorgar puntos debe ser
   ciego-táctil: números grandes, mínimo de campos, confirmación física.
3. **Todo estado vacío enseña** — cada empty state explica QUÉ es, POR QUÉ
   importa y QUÉ hacer (CTA).
4. **Movimiento con propósito** — animar solo lo que comunica (éxito,
   progreso, cambio de estado); nunca decorar.
5. **Accesible por defecto** — contraste AA, foco visible, targets ≥44px.

---

## 3. Fases

### Fase A — Fundamentos visuales compartidos (S)

> Objetivo: una sola "marca YAPAI" reconocible en los 3 portales.

| # | Tarea | Esfuerzo | Criterio de aceptación |
|---|---|---|---|
| A1 | **Design tokens centralizados**: documentar paleta real (navy `#1B2A63`, indigo cliente, emerald socio, admin indigo), radios (`rounded-xl`), sombras, spacing 4px-grid en `DESIGN.md` | S | Doc + variables Tailwind alineadas en los 3 `app.css` |
| A2 | **Familia tipográfica única**: una fuente con escala definida (hoy cada app usa system-ui implícito) — candidata: Inter o Outfit (self-hosted, sin Google Fonts en prod por CSP) | S | Misma escala tipográfica en 3 apps |
| A3 | **Set de iconos consistente**: los 3 `Icon.svelte` tienen mapas distintos → unificar en un solo archivo fuente copiado (o paquete compartido) | S | Mismo nombre de ícono = mismo dibujo en las 3 apps |
| A4 | **Componente `EmptyState` compartido**: ícono + título + descripción + CTA opcional | S | Usado en todas las listas vacías |

**Entregable**: `docs/DESIGN.md` + componentes `EmptyState`, `Icon` unificados.

---

### Fase B — App Cliente: sentirse viva (M)

> La app del cliente es el producto. Hoy es correcta pero "plana":
> carga con spinner, canjea sin celebrar, no perdona estar offline.

| # | Tarea | Esfuerzo | Detalle |
|---|---|---|---|
| B1 | **Skeletons en todas las pantallas** | M | `BilleteraSkeleton` (card saldo + 3 tiles), `ExplorarSkeleton` (grid de cards), `ComercioSkeleton`, `PasesSkeleton`. Reemplazar `<Spinner>` por skeleton con forma del contenido — percepción de velocidad +40% |
| B2 | **Celebración al ganar/canjear** | S | Al escanear y ganar puntos (deep-link de retorno del kiosco) y al canjear un pase: overlay con puntos animados contando (count-up), confetti sutil CSS-only (sin dep, `@keyframes`), haptic `navigator.vibrate?.(50)` en móvil |
| B3 | **Barra de progreso al próximo premio animada** | S | `ProximoPremioCard` ya existe — animar el fill con `transition` al montar + micro-bounce al llegar a 100% |
| B4 | **Pull-to-refresh** en Billetera/Explorar | M | Touch handler en layout: pull >70px dispara reload con indicador; solo `touchstart` en `scrollTop===0` |
| B5 | **Estado offline digno** | M | Banner persistente "Sin conexión" cuando `navigator.onLine===false` + `online/offline` listeners; el saldo/pases ya cargados siguen visibles (datos en `$state` sobreviven) — reemplazar el error genérico |
| B6 | **Swipe en tarjeta de pase** | S | En `/pases/[id]` permitir swipe lateral entre pases activos (gestos del QR para mostrar rápido al cajero) |
| B7 | **Onboarding de primera visita** | S | Tras registro: 3 slides (escanea→gana→canjea) con ilustraciones del logo; guardar `onboarding_visto` en localStorage |
| B8 | **Historial con filtros** | S | Movimientos: chips Todo/Ganados/Canjeados/Vencidos — el endpoint ya devuelve `tipo` |

**Prioridad**: B1 > B2 > B5 > B3 > B4 > B7 > B8 > B6.

---

### Fase C — Portal Socio: vender más rápido (M)

| # | Tarea | Esfuerzo | Detalle |
|---|---|---|---|
| C1 | **Checklist de activación** en dashboard | M | Card persistente hasta completar: ✓registro → ☐sucursal con GPS → ☐empleado cajero → ☐primer premio → ☐kiosco activo → ☐primera venta. Cada item linkea a su página. **Backend**: 1 endpoint `/socio/progreso` devolviendo qué falta (5 queries baratas) |
| C2 | **Empty states con CTA** | S | Premios vacío → "Crea tu primer premio" + botón; Comunicados vacío → "Publica tu primera oferta"; Sucursales → "Agrega tu local con GPS". Todos usando `EmptyState` de A4 |
| C3 | **Terminal POS modo cajero** | M | Hoy es un formulario estándar. Convertir en: búsqueda de cliente por CI/tel/QR con input gigante, teclado numérico on-screen opcional, últimas 3 ventas visibles, botón "Otorgar" full-width ≥64px, confirmación con toast grande y sonido corto opcional. Flujo completo en ≤15s |
| C4 | **Wizard de creación de premio** | M | El form actual muestra todos los campos a la vez. Wizard de 3 pasos: ①qué es (nombre/foto/puntos) ②reglas (stock/vencimiento) ③preview de cómo se ve en la app cliente. Barra de progreso arriba |
| C5 | **Preview "así lo ve tu cliente"** | S | En Premios/Comunicados: modal con el mockup del `PremioCard`/`OfertaTile` real renderizado con los datos del form — vende la feature |
| C6 | **Acciones rápidas en dashboard** | S | Los KPI cards ya existen — agregar links contextuales: "X pases por vencer" → /transacciones?filtro=vence |
| C7 | **i18n completar** | S | Auditar strings hardcodeados en español dentro de páginas (la plantilla i18n existe pero hay textos sueltos) |

---

### Fase D — Portal Admin: operar en volumen (S)

| # | Tarea | Esfuerzo | Detalle |
|---|---|---|---|
| D1 | **Selección múltiple en DataTable** | M | Checkbox por fila + barra de acciones flotante ("Suspender 3 socios", "Exportar selección") — aparece al seleccionar ≥1 |
| D2 | **Vistas guardadas / filtros URL** | S | Los filtros de socios/transacciones/liquidaciones deben vivir en `?params` — compartible, sobrevive refresh, botón "guardar vista" |
| D3 | **Detalle de socio con quick actions** | S | Cabecera sticky con estado + acciones directas (suspender, cambiar plan, ver liquidaciones) sin scrollear al fondo |
| D4 | **Tabla → cards en móvil** | M | En <640px las DataTable con scroll horizontal son incómodas — render alternativo de cards apiladas (componente `DataTable` acepta slot `fila-movil`) |

---

### Fase E — Kiosco: la pantalla que se ve a 3 metros (S)

| # | Tarea | Esfuerzo | Detalle |
|---|---|---|---|
| E1 | **Attract loop** | S | Tras 45s sin interacción: slideshow de ofertas publicadas del tenant a pantalla completa ("¡Escanea y gana!") — cualquier touch lo cancela. Usa datos ya cargados |
| E2 | **Modo offline del kiosco** | M | Si fetch falla: mostrar QR estático cacheado + mensaje "Modo sin conexión — acumularás puntos al volver internet" (el QR del tenant es constante) |
| E3 | **Escala para distancia** | S | QR mínimo 320px, fuentes base 20px+, alto contraste; hoy está pensado para tablet de cerca |
| E4 | **Confirmación visual de registro** | S | Tras registrarse: pantalla de éxito gigante "+N pts de bienvenida" durante 8s, luego auto-volver al attract loop |

---

### Fase F — Accesibilidad transversal (M)

Auditoría WCAG 2.1 AA rápida (mientras el producto es joven es barato):

| # | Tarea | Esfuerzo |
|---|---|---|
| F1 | Contraste: verificar `text-gray-400/500` sobre blanco (suele fallar AA 4.5:1 en texto <18px) — subir a `gray-600` donde aplique | S |
| F2 | Foco visible: `focus-visible:ring` en todos los botones/inputs/links (Tailwind lo hace trivial) | S |
| F3 | Targets táctiles ≥44×44px (los icon-buttons de 32px en cards/tablas incumplen) | S |
| F4 | `aria-label` en icon-only buttons (hoy hay pocos), `role="dialog"`+`aria-modal` en modales, `alt` real en fotos (hoy `alt=""` genérico) | M |
| F5 | Test con teclado completo: login→dashboard→crear premio sin mouse | S |

---

### Fase G — Dark mode (evaluación)

**Recomendación honesta: NO implementarlo aún.**

Costo real: ~200 lugares con clases light-only en 3 apps (`bg-white`, `text-gray-*`, `ring-black/5`), QA ×3, y el navy del brand no oscurece bien. Beneficio: cosmético en un producto B2B/B2C diurno (tiendas, cajeros, kioscos). **Posponer hasta que un usuario lo pida.** Cuando llegue: hacerlo SOLO en `frontend_cliente` primero (es la app que un usuario usaría de noche).

---

### Fase H — Motion design system (S)

| # | Tarea | Detalle |
|---|---|---|
| H1 | Tokens de animación en CSS: `--dur-rapida 150ms`, `--dur-normal 250ms`, `--ease-salida cubic-bezier(.2,.8,.2,1)` | Una línea por `app.css` |
| H2 | Transiciones Svelte estándar: `fly` en toasts (ya), `fade` en modales, `scale(.95)` en aparecer de cards nuevas | Patrón único documentado |
| H3 | `prefers-reduced-motion`: media query global que neutraliza animaciones — requisito a11y (F) y buen gusto | ~10 líneas CSS |

---

## 4. Quick wins (< medio día c/u — empezar aquí)

| Orden | Item | Impacto |
|---|---|---|
| 1 | B1 skeletons en Billetera + Explorar | La app se siente 2× más rápida |
| 2 | C2 empty states con CTA en socio | Activa features dormidas |
| 3 | E1 attract loop kiosco | El kiosco se vende solo parado |
| 4 | F1+F2 contraste + foco | AA casi gratis ahora |
| 5 | B5 banner offline | Elimina la peor UX (app "rota" sin señal) |
| 6 | B2 celebración al ganar puntos | El momento de dopamina del producto |

---

## 5. Métricas de éxito (medibles hoy)

| Métrica | Cómo medirla | Meta |
|---|---|---|
| Tiempo percibido de carga | `performance.now()` hasta contenido visible (skeleton ≠ spinner) | LCP <2.5s en 4G |
| Activación socio | % socios que completan checklist C1 en primera semana | >60% |
| Tiempo en terminal (cajero) | Logs backend timestamp entre `buscar` y `otorgar` | <15s p50 |
| Push opt-in | `push_suscripciones` / clientes activos | >30% |
| Errores de tasa de rebote móvil | Analytics (agregar Plausible/Umami — liviano, self-hostable) | baseline primero |

---

## 6. Roadmap sugerido

```
Semana 1:  Quick wins 1-4 + A1/A4 (tokens + EmptyState)
Semana 2:  B1 skeletons completos + B5 offline + C1 checklist socio
Semana 3:  C3 terminal cajero + B2/B3 celebración + E1/E4 kiosco
Semana 4:  D1/D4 admin + F accesibilidad + B7 onboarding cliente
Después:   C4/C5 wizard+preview, B4 pull-refresh, H motion, i18n restante
```

**No hacer (todavía):** dark mode (G), animaciones decorativas, re-skin
total — el lenguaje visual split-login + navy + cards ya es coherente;
el ROI está en velocidad percibida, activación y momentos de celebración.

---

## 7. Decisiones que necesito de ti

1. ¿Quick wins primero o fase completa en orden?
2. ¿La fuente nueva (A2) — Inter/Outfit self-hosted, o system-ui y listo?
3. ¿Checklist de socio (C1) con endpoint `/socio/progreso` nuevo, ok?
4. ¿Analytics (métricas §5): Plausible self-hosted en el compose, o sin analytics por ahora?
