// Web Push: suscripción del navegador a las notificaciones del cliente.
// Flujo: permiso nativo → pushManager.subscribe → POST /cliente/push/suscripcion.
// La clave pública VAPID viene del backend (no se embebe en el build).
import { api } from './api/client';

export type EstadoPush =
	| 'no-soportado'
	| 'no-configurado'
	| 'denegado'
	| 'desactivado'
	| 'activado';

function urlBase64ABytes(b64: string): Uint8Array {
	const pad = '='.repeat((4 - (b64.length % 4)) % 4);
	const bin = atob((b64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
	return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

export function pushSoportado(): boolean {
	return (
		typeof window !== 'undefined' &&
		'Notification' in window &&
		'serviceWorker' in navigator &&
		'PushManager' in window
	);
}

export async function estadoPush(): Promise<EstadoPush> {
	if (!pushSoportado()) return 'no-soportado';
	if (Notification.permission === 'denied') return 'denegado';
	const { public_key } = await api.get<{ public_key: string | null }>('/cliente/push/vapid');
	if (!public_key) return 'no-configurado';
	const reg = await navigator.serviceWorker.ready;
	return (await reg.pushManager.getSubscription()) ? 'activado' : 'desactivado';
}

/** Pide permiso, suscribe en el SW y registra en el backend. Devuelve el estado final. */
export async function activarPush(): Promise<EstadoPush> {
	if (!pushSoportado()) return 'no-soportado';
	const permiso = await Notification.requestPermission();
	if (permiso !== 'granted') return 'denegado';

	const { public_key } = await api.get<{ public_key: string | null }>('/cliente/push/vapid');
	if (!public_key) return 'no-configurado';

	const reg = await navigator.serviceWorker.ready;
	const sub = await reg.pushManager.subscribe({
		userVisibleOnly: true,
		applicationServerKey: urlBase64ABytes(public_key).buffer as ArrayBuffer
	});
	const json = sub.toJSON();
	await api.post('/cliente/push/suscripcion', {
		endpoint: json.endpoint,
		keys: { p256dh: json.keys?.p256dh ?? '', auth: json.keys?.auth ?? '' }
	});
	return 'activado';
}

/** Baja la suscripción del navegador y del backend. */
export async function desactivarPush(): Promise<void> {
	const reg = await navigator.serviceWorker.ready;
	const sub = await reg.pushManager.getSubscription();
	if (!sub) return;
	const qs = encodeURIComponent(sub.endpoint);
	await api.delete(`/cliente/push/suscripcion?endpoint=${qs}`).catch(() => {});
	await sub.unsubscribe().catch(() => {});
}
