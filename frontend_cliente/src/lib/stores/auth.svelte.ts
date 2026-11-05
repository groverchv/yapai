import type { Cliente, FirmaUpload, LoginClienteResponse, TokenPair } from '../types';
import { api, API_BASE, fetchRed } from '../api/client';

const KEY = 'yapai_cliente_sesion';

interface Sesion {
	access: string;
	refresh: string;
	cliente: Cliente;
}

class AuthStore {
	cliente = $state<Cliente | null>(null);
	accessToken = $state<string | null>(null);
	refreshToken = $state<string | null>(null);

	constructor() {
		try {
			const raw = localStorage.getItem(KEY);
			if (raw) {
				const s: Sesion = JSON.parse(raw);
				this.cliente = s.cliente;
				this.accessToken = s.access;
				this.refreshToken = s.refresh;
				// Refresca datos del cliente en segundo plano (igual que la app móvil)
				this.refrescarCliente().catch(() => {});
			}
		} catch {
			this.limpiar();
		}
	}

	get autenticado() {
		return !!this.accessToken && !!this.cliente;
	}

	private persistir() {
		if (this.cliente && this.accessToken && this.refreshToken) {
			localStorage.setItem(KEY, JSON.stringify({
				access: this.accessToken,
				refresh: this.refreshToken,
				cliente: this.cliente
			} satisfies Sesion));
		}
	}

	private establecerSesion(tokens: TokenPair, cliente: Cliente) {
		this.cliente = cliente;
		this.accessToken = tokens.access_token;
		this.refreshToken = tokens.refresh_token;
		this.persistir();
	}

	async login(telefono: string, ci: string) {
		const res = await fetchRed(`${API_BASE}/auth/cliente/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ telefono, ci })
		});
		const data = await res.json().catch(() => null);
		if (!res.ok) throw new Error(detalle(data) ?? 'Credenciales inválidas');
		const d: LoginClienteResponse = data;
		this.establecerSesion(d.tokens, d.cliente);
	}

	async registro(nombre: string, telefono: string, ci: string, codigoReferido?: string) {
		const payload: Record<string, string> = { nombre, telefono, ci };
		if (codigoReferido?.trim()) payload.codigo_referido = codigoReferido.trim().toUpperCase();
		const res = await fetchRed(`${API_BASE}/auth/cliente/registro`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload)
		});
		const data = await res.json().catch(() => null);
		if (res.status !== 201) throw new Error(detalle(data) ?? 'Error al registrar cliente');
		const d: LoginClienteResponse = data;
		this.establecerSesion(d.tokens, d.cliente);
	}

	async cerrarSesion() {
		const refresh = this.refreshToken;
		this.limpiar();
		if (refresh) {
			try {
				await fetchRed(`${API_BASE}/auth/logout`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ refresh_token: refresh })
				});
			} catch { /* sesión local ya cerrada */ }
		}
	}

	async eliminarCuenta() {
		await api.delete('/cliente/me');
		this.limpiar();
	}

	actualizarTokens(tokens: TokenPair) {
		if (this.cliente) {
			this.accessToken = tokens.access_token;
			this.refreshToken = tokens.refresh_token;
			this.persistir();
		}
	}

	actualizarCliente(cliente: Cliente) {
		this.cliente = cliente;
		this.persistir();
	}

	async refrescarCliente() {
		if (!this.accessToken) return;
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
		this.accessToken = null;
		this.refreshToken = null;
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
