import type { Cliente, FirmaUpload, LoginClienteResponse } from '../types';
import { api, API_BASE, fetchRed } from '../api/client';

const KEY = 'yapai_cliente_sesion';

// Solo se persiste el perfil (dato de UI, no sensible). La sesión vive en
// cookies HttpOnly: nada que robar por XSS y el backend las rota en /refresh.
interface Sesion {
	cliente: Cliente;
}

class AuthStore {
	cliente = $state<Cliente | null>(null);
	// Cuando el login pide OTP, el siguiente paso es verificarOtp()
	otpPendiente = $state(false);
	otpTtlMinutos = $state<number | null>(null);

	constructor() {
		try {
			const raw = localStorage.getItem(KEY);
			if (raw) {
				const s: Sesion = JSON.parse(raw);
				this.cliente = s.cliente;
				// Refresca datos del cliente en segundo plano (igual que la app móvil)
				this.refrescarCliente().catch(() => {});
			}
		} catch {
			this.limpiar();
		}
	}

	get autenticado() {
		return !!this.cliente;
	}

	private persistir() {
		if (this.cliente) {
			localStorage.setItem(KEY, JSON.stringify({
				cliente: this.cliente
			} satisfies Sesion));
		}
	}

	private establecerSesion(cliente: Cliente) {
		this.cliente = cliente;
		this.otpPendiente = false;
		this.persistir();
	}

	/** Devuelve 'otp' si se requiere el código, 'ok' si la sesión ya quedó. */
	async login(telefono: string, ci: string): Promise<'otp' | 'ok'> {
		const res = await fetchRed(`${API_BASE}/auth/cliente/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ telefono, ci })
		});
		const data = await res.json().catch(() => null);
		if (!res.ok) throw new Error(detalle(data) ?? 'Credenciales inválidas');
		const d: LoginClienteResponse = data;
		if (d.otp_requerido) {
			this.otpPendiente = true;
			this.otpTtlMinutos = d.otp_ttl_minutos ?? null;
			return 'otp';
		}
		this.establecerSesion(d.cliente);
		return 'ok';
	}

	async verificarOtp(telefono: string, ci: string, codigo: string) {
		const res = await fetchRed(`${API_BASE}/auth/cliente/otp/verificar`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ telefono, ci, codigo })
		});
		const data = await res.json().catch(() => null);
		if (!res.ok) throw new Error(detalle(data) ?? 'Código incorrecto o expirado');
		const d: LoginClienteResponse = data;
		this.establecerSesion(d.cliente);
	}

	/** Devuelve 'otp' si falta verificar el teléfono, 'ok' si la sesión quedó. */
	async registro(nombre: string, telefono: string, ci: string,
		codigoReferido?: string, codigo?: string): Promise<'otp' | 'ok'> {
		const payload: Record<string, string> = { nombre, telefono, ci };
		if (codigoReferido?.trim()) payload.codigo_referido = codigoReferido.trim().toUpperCase();
		if (codigo?.trim()) payload.codigo = codigo.trim();
		const res = await fetchRed(`${API_BASE}/auth/cliente/registro`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload)
		});
		const data = await res.json().catch(() => null);
		if (!res.ok) throw new Error(detalle(data) ?? 'Error al registrar cliente');
		const d: LoginClienteResponse = data;
		if (d.otp_requerido) {
			this.otpPendiente = true;
			this.otpTtlMinutos = d.otp_ttl_minutos ?? null;
			return 'otp';
		}
		this.establecerSesion(d.cliente);
		return 'ok';
	}

	async cerrarSesion() {
		this.limpiar();
		try {
			await fetchRed(`${API_BASE}/auth/logout`, { method: 'POST' });
		} catch { /* sesión local ya cerrada */ }
	}

	async eliminarCuenta() {
		await api.delete('/cliente/me');
		this.limpiar();
	}

	actualizarCliente(cliente: Cliente) {
		this.cliente = cliente;
		this.persistir();
	}

	async refrescarCliente() {
		if (!this.cliente) return;
		const data = await api.get<Cliente>('/cliente/me');
		this.actualizarCliente(data);
	}

	/** Firma del backend → upload directo a Cloudinary → PATCH /me con la URL. */
	async subirFoto(file: File) {
		const firma = await api.post<FirmaUpload>('/cliente/uploads/firma');
		const fd = new FormData();
		fd.set('api_key', `${firma.api_key}`);
		fd.set('timestamp', `${firma.timestamp}`);
		fd.set('signature', firma.signature);
		fd.set('folder', firma.folder);
		fd.set('file', file);
		const res = await fetchRed(
			`https://api.cloudinary.com/v1_1/${firma.cloud_name}/image/upload`,
			{ method: 'POST', body: fd }
		);
		const body = await res.json().catch(() => null);
		if (!res.ok) {
			throw new Error(body?.error?.message ?? 'Error al subir la imagen');
		}
		const actualizado = await api.patch<Cliente>('/cliente/me', { foto_url: body.secure_url });
		this.actualizarCliente(actualizado);
	}

	limpiar() {
		this.cliente = null;
		this.otpPendiente = false;
		this.otpTtlMinutos = null;
		localStorage.removeItem(KEY);
	}
}

function detalle(body: { detail?: unknown } | null): string | null {
	const d = body?.detail;
	if (d && typeof d === 'object') return String((d as Record<string, unknown>).mensaje ?? '');
	if (typeof d === 'string') return d;
	return null;
}

export const auth = new AuthStore();
