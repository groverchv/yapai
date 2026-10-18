export interface UsuarioMe {
	id: number;
	email: string;
	nombre: string;
	rol: 'superadmin' | 'owner' | 'cajero';
	tenant_id: number | null;
	totp_habilitado: boolean;
	tenant_nombre?: string | null;
	tenant_logo?: string | null;
}

export interface TokenPair {
	access_token: string;
	refresh_token: string;
	token_type: string;
	expires_in: number;
}

export interface Pagina<T> {
	items: T[];
	total: number;
	page: number;
	size: number;
}

// --- Perfil ---
export interface Perfil {
	id: number;
	nombre: string;
	email: string;
	rol: string;
	tenant_id: number;
	tenant_nombre: string;
	logo_url: string | null;
}

// --- Empleados ---
export interface Empleado {
	id: number;
	nombre: string;
	email: string;
	estado: 'activo' | 'suspendido';
	onboarding_pendiente: boolean;
	sucursales: string[];
	ultimo_login: string | null;
}

// --- Sucursales ---
export interface Pantalla {
	id: number;
	nombre: string;
	device_token: string;
	estado: 'activa' | 'bloqueada';
	habilitada_hasta: string | null;
}

export interface Sucursal {
	id: number;
	nombre: string;
	direccion: string | null;
	encargado_nombre: string | null;
	estado: 'activa' | 'suspendida';
	pin_set: boolean;
	pantallas: Pantalla[];
}

// --- PIN de caja ---
export interface PinConfig {
	modo: 'por_sucursal' | 'por_cajero';
	sucursales: { id: number; nombre: string; pin_set: boolean }[];
	cajeros: { id: number; nombre: string; pin_set: boolean }[];
}

// --- Premios ---
export interface Premio {
	id: number;
	nombre: string;
	descripcion: string | null;
	costo_puntos: number;
	imagen_url: string | null;
	stock_limitado: boolean;
	stock: number | null;
	estado: 'activo' | 'agotado' | 'inactivo';
	pases_activos: number;
	vigencia_hasta: string | null;
}

// --- Campañas ---
export interface Campana {
	id: number;
	nombre: string;
	multiplicador: number;
	inicio: string;
	fin: string;
	sucursal_id: number | null;
	sucursal_nombre: string | null;
	activa: boolean;
	vigente: boolean;
}

export interface Inactivo {
	cliente_id: number;
	nombre: string;
	telefono: string;
	ult_actividad: string;
	dias_inactivo: number;
	saldo: number;
}

// --- Ruleta ---
export interface Segmento {
	id: number;
	etiqueta: string;
	puntos: number;
	peso: number;
	color: string | null;
	activo: boolean;
}

export interface TopPremioSocio {
	id: number;
	nombre: string;
	costo_puntos: number;
	stock: number | null;
	imagen_url: string | null;
	total_canjes: number;
}

export interface ResumenSocio {
	clientes_nuevos: number;
	puntos_otorgados: number;
	puntos_consumidos: number;
	canjes_exitosos: number;
	stock_critico: { id: number; nombre: string; stock: number }[];
	clientes_totales: number;
	tasa_redencion: number;
	transacciones_hoy: number;
	pases_activos: number;
	transacciones_30d: { fecha: string; total: number }[];
	top_premios: TopPremioSocio[];
}

// --- Transacciones ---
export interface Transaccion {
	id: number;
	created_at: string;
	tenant_id: number;
	socio: string;
	sucursal: string | null;
	cliente_id: number;
	cliente_nombre: string;
	cliente_ci: string;
	tipo: string;
	puntos: number;
	ejecutado_por: string | null;
	premio: string | null;
	detalle: string | null;
}

export interface OpcionesFiltro {
	sucursales: { id: number; nombre: string }[];
	cajeros: { id: number; nombre: string }[];
}

export interface PlanPublico {
	id: number;
	slug: string;
	nombre: string;
	descripcion: string | null;
	precio_mensual: number;
	moneda: string;
	max_sucursales: number;
	max_pantallas: number;
	max_clientes: number;
	max_empleados: number;
	ruleta_habilitada: boolean;
}

export interface SocioPlan {
	plan_id: number | null;
	plan_nombre: string | null;
	plan_slug: string | null;
	precio_mensual: number | null;
	moneda: string;
	limites: {
		max_sucursales: number;
		max_pantallas: number;
		max_clientes: number;
		max_empleados: number;
		ruleta_habilitada: boolean;
	} | null;
	uso: { sucursales: number; pantallas: number; clientes: number; empleados: number };
	en_trial: boolean;
	dias_trial: number;
	trial_fin: string | null;
}

export interface SignupResponse {
	aprobado: boolean;
	tokens: TokenPair | null;
	usuario: UsuarioMe | null;
}

export interface PasoOnboarding {
	clave: string;
	etiqueta: string;
	hecho: boolean;
	href: string | null;
}

export interface OnboardingOut {
	pasos: PasoOnboarding[];
	completados: number;
	total: number;
	completado: boolean;
}

export interface FacturaSocio {
	id: number;
	plan_nombre: string;
	periodo: string;
	monto: number;
	moneda: string;
	estado: 'pendiente' | 'pagada' | 'vencida';
	emitida_en: string;
	vence_en: string;
	pagada_en: string | null;
	metodo: string | null;
}

export interface EstadoCuenta {
	estado: 'al_dia' | 'pendiente' | 'vencida';
	facturas: FacturaSocio[];
}

export interface Comunicado {
	id: number;
	tenant_id: number;
	titulo: string;
	descripcion: string | null;
	imagen_url: string;
	imagen_public_id: string | null;
	premio_id: number | null;
	premio_nombre: string | null;
	estado: 'borrador' | 'publicado' | 'archivado';
	publicado_en: string | null;
	vigencia_hasta: string | null;
	created_at: string;
}
