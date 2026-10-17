// Base i18n — YAPAI. Hoy: es + en (navegación, acciones comunes, login).
// Uso: i18n.t('nav.dashboard') en templates; i18n.set('en') para cambiar idioma.
const browser = typeof window !== 'undefined';

export type Locale = 'es' | 'en';

const ES = {
	// Secciones de navegación
	'nav.general': 'General',
	'nav.operacion': 'Operación',
	'nav.negocio': 'Mi negocio',
	'nav.socios': 'Socios',
	'nav.configuracion': 'Configuración',
	'nav.cuenta': 'Cuenta',
	// Items de menú
	'nav.dashboard': 'Dashboard',
	'nav.transacciones': 'Transacciones',
	'nav.rendimiento': 'Rendimiento',
	'nav.premios': 'Premios',
	'nav.ruleta': 'Ruleta',
	'nav.campanas': 'Campañas',
	'nav.sucursales': 'Sucursales',
	'nav.empleados': 'Empleados',
	'nav.accesos': 'PIN de caja',
	'nav.perfil': 'Mi perfil',
	'nav.facturacion': 'Facturación',
	'nav.listado_socios': 'Listado de socios',
	'nav.nuevo_socio': 'Nuevo socio',
	'nav.liquidaciones': 'Liquidaciones',
	'nav.facturacion_saas': 'Facturación SaaS',
	'nav.categorias': 'Categorías',
	'nav.esquemas': 'Esquemas comisión',
	'nav.planes': 'Planes SaaS',
	// Acciones comunes
	'accion.cerrar_sesion': 'Cerrar sesión',
	'accion.cerrar': 'Cerrar',
	'accion.guardar': 'Guardar',
	'accion.cancelar': 'Cancelar',
	'accion.cargando': 'Cargando…',
	// Login
	'login.correo': 'Correo',
	'login.contrasena': 'Contraseña',
	'login.ingresar': 'Ingresar',
	'login.ingresando': 'Ingresando…',
	'login.verificar': 'Verificar',
	'login.verificando': 'Verificando…',
	'login.volver': '← Volver',
	'login.codigo': 'Código de verificación',
	'login.ayuda_2fa':
		'Tu cuenta tiene verificación en dos pasos. Ingresa el código de 6 dígitos de tu app de autenticación.',
	'login.olvidaste': '¿Olvidaste tu contraseña?',
	'login.sin_cuenta': '¿Aún no tienes cuenta?',
	'login.registrate': 'Regístrate gratis',
	'login.error_auth': 'Error de autenticación',
	'login.error_conexion': 'Error de conexión'
} as const;

export type Clave = keyof typeof ES;

const EN: Record<Clave, string> = {
	'nav.general': 'General',
	'nav.operacion': 'Operations',
	'nav.negocio': 'My business',
	'nav.socios': 'Partners',
	'nav.configuracion': 'Settings',
	'nav.cuenta': 'Account',
	'nav.dashboard': 'Dashboard',
	'nav.transacciones': 'Transactions',
	'nav.rendimiento': 'Performance',
	'nav.premios': 'Rewards',
	'nav.ruleta': 'Roulette',
	'nav.campanas': 'Campaigns',
	'nav.sucursales': 'Branches',
	'nav.empleados': 'Employees',
	'nav.accesos': 'Cashier PIN',
	'nav.perfil': 'My profile',
	'nav.facturacion': 'Billing',
	'nav.listado_socios': 'Partner list',
	'nav.nuevo_socio': 'New partner',
	'nav.liquidaciones': 'Settlements',
	'nav.facturacion_saas': 'SaaS billing',
	'nav.categorias': 'Categories',
	'nav.esquemas': 'Commission schemes',
	'nav.planes': 'SaaS plans',
	'accion.cerrar_sesion': 'Sign out',
	'accion.cerrar': 'Close',
	'accion.guardar': 'Save',
	'accion.cancelar': 'Cancel',
	'accion.cargando': 'Loading…',
	'login.correo': 'Email',
	'login.contrasena': 'Password',
	'login.ingresar': 'Sign in',
	'login.ingresando': 'Signing in…',
	'login.verificar': 'Verify',
	'login.verificando': 'Verifying…',
	'login.volver': '← Back',
	'login.codigo': 'Verification code',
	'login.ayuda_2fa':
		'Your account has two-step verification. Enter the 6-digit code from your authenticator app.',
	'login.olvidaste': 'Forgot your password?',
	'login.sin_cuenta': "Don't have an account yet?",
	'login.registrate': 'Sign up free',
	'login.error_auth': 'Authentication error',
	'login.error_conexion': 'Connection error'
};

const DICTS: Record<Locale, Record<Clave, string>> = { es: ES, en: EN };
const CLAVE_STORAGE = 'yapai-locale';

class I18n {
	locale = $state<Locale>('es');

	constructor() {
		if (browser) {
			const saved = localStorage.getItem(CLAVE_STORAGE);
			if (saved === 'en' || saved === 'es') this.locale = saved;
			document.documentElement.lang = this.locale;
		}
	}

	t(clave: Clave): string {
		return DICTS[this.locale][clave] ?? clave;
	}

	set(l: Locale) {
		this.locale = l;
		if (browser) {
			localStorage.setItem(CLAVE_STORAGE, l);
			document.documentElement.lang = l;
		}
	}
}

export const i18n = new I18n();
