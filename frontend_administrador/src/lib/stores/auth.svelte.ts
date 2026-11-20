import type { UsuarioMe } from '../types';

const KEY = 'yapai_admin_sesion';

// Solo se persiste el perfil (dato de UI, no sensible). La sesión vive en
// cookies HttpOnly: nada que robar por XSS y el backend las rota en /refresh.
interface Sesion {
	usuario: UsuarioMe;
}

class AuthStore {
	usuario = $state<UsuarioMe | null>(null);

	constructor() {
		try {
			const raw = localStorage.getItem(KEY);
			if (raw) {
				const s: Sesion = JSON.parse(raw);
				this.usuario = s.usuario;
			}
		} catch {
			this.limpiar();
		}
	}

	get autenticado() {
		return !!this.usuario;
	}

	guardar(usuario: UsuarioMe) {
		this.usuario = usuario;
		localStorage.setItem(KEY, JSON.stringify({ usuario } satisfies Sesion));
	}

	actualizarUsuario(usuario: UsuarioMe) {
		this.guardar(usuario);
	}

	limpiar() {
		this.usuario = null;
		localStorage.removeItem(KEY);
	}
}

export const auth = new AuthStore();
