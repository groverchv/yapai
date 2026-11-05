// @ts-nocheck
/// <reference lib="webworker" />
/* Service worker PWA — requisito de instalabilidad (fetch handler)
   + cache-first solo para assets inmutables e iconos; el resto pasa a red. */
const sw = self;
const CACHE = 'yapai-cliente-v1';

sw.addEventListener('install', () => {
	sw.skipWaiting();
});

sw.addEventListener('activate', (event) => {
	event.waitUntil(sw.clients.claim());
});

// --- Notificaciones push ---
sw.addEventListener('push', (event) => {
	let datos = { titulo: 'YAPAI', cuerpo: '', url: '/' };
	try {
		if (event.data) datos = { ...datos, ...event.data.json() };
	} catch {
		if (event.data) datos.cuerpo = event.data.text();
	}
	event.waitUntil(
		sw.registration.showNotification(datos.titulo, {
			body: datos.cuerpo,
			icon: '/icons/icon-192.png',
			badge: '/icons/icon-192.png',
			data: { url: datos.url }
		})
	);
});

// Click en notificación: enfocar pestaña abierta o abrir la URL destino.
sw.addEventListener('notificationclick', (event) => {
	event.notification.close();
	const url = event.notification.data?.url || '/';
	event.waitUntil(
		sw.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((lista) => {
			for (const c of lista) {
				if (c.url.startsWith(sw.location.origin) && 'focus' in c) {
					c.navigate(url);
					return c.focus();
				}
			}
			return sw.clients.openWindow(url);
		})
	);
});

sw.addEventListener('fetch', (event) => {
	const url = new URL(event.request.url);
	if (event.request.method !== 'GET' || url.origin !== location.origin) return;
	if (url.pathname.startsWith('/api/')) return;

	// Assets versionados de Vite e iconos: cache-first, red como respaldo.
	if (url.pathname.startsWith('/_app/immutable') || url.pathname.startsWith('/icons')) {
		event.respondWith(
			caches.match(event.request).then(
				(hit) =>
					hit ||
					fetch(event.request).then((res) => {
						const copia = res.clone();
						caches.open(CACHE).then((c) => c.put(event.request, copia));
						return res;
					})
			)
		);
	}
});
