import { env } from '$env/dynamic/public';
import { auth } from '../stores/auth.svelte';
import type { TokenPair } from '../types';

// PUBLIC_API_BASE en runtime (adapter-node); default: backend local en dev
export const API_BASE = env.PUBLIC_API_BASE ?? 'http://localhost:8000/api/v1';

export class ApiError extends Error {
	constructor(
		public status: number,
		public detail: string,
		public code?: string,
		public recurso?: string
	) {
		super(detail);
	}
}

function detalleDe(body: { detail?: unknown } | null, fallback: string): ApiError {
	const d = body?.detail;
	if (d && typeof d === 'object') {
		const o = d as Record<string, unknown>;
		return new ApiError(0, String(o.mensaje ?? fallback), o.code as string | undefined, o.recurso as string | undefined);
	}
	return new ApiError(0, (d as string) ?? fallback);
}

let refreshPromise: Promise<boolean> | null = null;

async function intentarRefresh(): Promise<boolean> {
	if (!auth.refreshToken) return false;
	refreshPromise ??= (async () => {
		try {
			const res = await fetch(`${API_BASE}/auth/refresh`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ refresh_token: auth.refreshToken })
			});
			if (!res.ok) return false;
			const tokens: TokenPair = await res.json();
			auth.actualizarTokens(tokens);
			return true;
		} catch {
			return false;
		} finally {
			refreshPromise = null;
		}
	})();
	return refreshPromise;
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
	const headers = new Headers(init.headers);
	if (!headers.has('Content-Type') && init.body) headers.set('Content-Type', 'application/json');
	if (auth.accessToken) headers.set('Authorization', `Bearer ${auth.accessToken}`);

	const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

	if (res.status === 401 && retry && (await intentarRefresh())) {
		return request<T>(path, init, false);
	}
	if (res.status === 401) {
		auth.limpiar();
		location.href = '/login';
		throw new ApiError(401, 'Sesión expirada');
	}
	if (!res.ok) {
		const body = await res.json().catch(() => null);
		const err = detalleDe(body, `Error ${res.status}`);
		err.status = res.status;
		throw err;
	}
	if (res.status === 204) return undefined as T;
	return res.json();
}

export const api = {
	get: <T>(path: string) => request<T>(path),
	post: <T>(path: string, body?: unknown) =>
		request<T>(path, { method: 'POST', body: body !== undefined ? JSON.stringify(body) : undefined }),
	patch: <T>(path: string, body: unknown) =>
		request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
	delete: <T>(path: string) => request<T>(path, { method: 'DELETE' })
};

export async function descargarCsv(path: string, filename: string) {
	const headers = new Headers();
	if (auth.accessToken) headers.set('Authorization', `Bearer ${auth.accessToken}`);
	const res = await fetch(`${API_BASE}${path}`, { headers });
	if (!res.ok) throw new ApiError(res.status, 'Error al exportar');
	const blob = await res.blob();
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	a.click();
	URL.revokeObjectURL(url);
}
