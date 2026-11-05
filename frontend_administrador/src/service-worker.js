// @ts-nocheck
/// <reference lib="webworker" />
/* Service worker PWA — requisito de instalabilidad (fetch handler)
   + cache-first solo para assets inmutables e iconos; el resto pasa a red. */
const sw = self;
const CACHE = 'yapai-admin-v1';

sw.addEventListener('install', () => {
	sw.skipWaiting();
});

sw.addEventListener('activate', (event) => {
	event.waitUntil(sw.clients.claim());
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
