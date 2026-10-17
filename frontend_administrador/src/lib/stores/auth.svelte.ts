import type { TokenPair, UsuarioMe } from '../types';

const KEY = 'yapai_admin_sesion';

interface Sesion {
	access: string;
	refresh: string;
	usuario: UsuarioMe;
}

class AuthStore {
	usuario = $state<UsuarioMe | null>(null);
	accessToken = $state<string | null>(null);
	refreshToken = $state<string | null>(null);

	constructor() {
		try {
			const raw = localStorage.getItem(KEY);
			if (raw) {
				const s: Sesion = JSON.parse(raw);
				this.usuario = s.usuario;
				this.accessToken = s.access;
				this.refreshToken = s.refresh;
			}
		} catch {
			this.limpiar();
		}
	}

	get autenticado() {
		return !!this.accessToken;
	}

	guardar(tokens: TokenPair, usuario: UsuarioMe) {
		this.usuario = usuario;
		this.accessToken = tokens.access_token;
		this.refreshToken = tokens.refresh_token;
		localStorage.setItem(KEY, JSON.stringify({
			access: tokens.access_token,
			refresh: tokens.refresh_token,
			usuario
		} satisfies Sesion));
	}

	actualizarTokens(tokens: TokenPair) {
		if (this.usuario) this.guardar(tokens, this.usuario);
	}

	limpiar() {
		this.usuario = null;
		this.accessToken = null;
		this.refreshToken = null;
		localStorage.removeItem(KEY);
	}
}

export const auth = new AuthStore();
