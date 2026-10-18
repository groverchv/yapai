export interface UsuarioMe {
	id: number;
	email: string;
	nombre: string;
	rol: 'superadmin' | 'owner' | 'cajero';
	tenant_id: number | null;
	totp_habilitado: boolean;
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

export interface SocioListItem {
	id: number;
	nombre_comercial: string;
	nit_rut: string;
	logo_url: string | null;
	categoria: string | null;
	esquema: string | null;
	estado: 'activo' | 'suspendido';
	created_at: string;
}

export interface FirmaUploadOut {
	cloud_name: string;
	api_key: string;
	timestamp: number;
	folder: string;
	signature: string;
}

export interface OwnerOut {
	id: number;
	nombre: string;
	email: string;
	estado: string;
	onboarding_pendiente: boolean;
}

export interface SocioDetalle {
	id: number;
	nombre_comercial: string;
	razon_social: string | null;
	nit_rut: string;
	email_contacto: string | null;
	telefono: string | null;
	logo_url: string | null;
	categoria_id: number | null;
	categoria: string | null;
	esquema_comision_id: number | null;
	esquema: string | null;
	estado: 'activo' | 'suspendido';
	created_at: string;
	suspendido_en: string | null;
	owner: OwnerOut | null;
	total_sucursales: number;
	total_empleados: number;
	total_clientes: number;
	total_premios_activos: number;
	plan_id: number | null;
	plan: string | null;
	trial_fin: string | null;
	facturacion_estado: 'al_dia' | 'pendiente' | 'vencida';
}

export interface PlanOut {
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
	orden: number;
	activo: boolean;
	tenants_asignados: number;
}

export interface KpisSocio {
	clientes_nuevos: number;
	puntos_emitidos: number;
	puntos_consumidos: number;
	canjes_exitosos: number;
	horas_a_primer_giro: number | null;
}

export interface UsuarioListItem {
	id: number;
	nombre: string;
	email: string;
	rol: string;
	estado: string;
	ultimo_login: string | null;
}

export interface SucursalListItem {
	id: number;
	nombre: string;
	direccion: string | null;
	encargado_nombre: string | null;
	estado: string;
}

export interface ClienteListItem {
	id: number;
	nombre: string;
	ci: string;
	telefono: string;
	estado: string;
	created_at: string;
}

export interface CategoriaOut {
	id: number;
	nombre: string;
	slug: string;
	icono_url: string | null;
	activa: boolean;
	socios_vinculados: number;
}

export interface EsquemaOut {
	id: number;
	nombre: string;
	costo_registro: number;
	costo_canje: number;
	moneda: string;
	activo: boolean;
	has_usage: boolean;
}

export interface TransaccionOut {
	id: number;
	created_at: string;
	tenant_id: number | null;
	socio: string | null;
	sucursal: string | null;
	cliente_id: number;
	cliente_nombre: string;
	cliente_ci: string;
	tipo: string;
	puntos: number;
	ejecutado_por: string | null;
	premio: string | null;
	detalle: Record<string, unknown> | null;
}

export interface LiquidacionOut {
	id: number;
	tenant_id: number;
	socio: string;
	periodo: string;
	clientes_nuevos: number;
	canjes_validados: number;
	costo_registro_unit: number;
	costo_canje_unit: number;
	monto_total: number;
	moneda: string;
	estado: 'pendiente' | 'pagada';
	pagada_en: string | null;
	aprobada_por: string | null;
	created_at: string;
}

export interface KpisGlobales {
	socios_activos: number;
	socios_suspendidos: number;
	transacciones_hoy: number;
	liquidaciones_pendientes: number;
	monto_pendiente: number;
	clientes_totales: number;
	ttfs_medio_h: number | null;
	facturas_pendientes: number;
	monto_facturacion_pendiente: number;
}

export interface SerieDia {
	fecha: string;
	total: number;
}

export interface TopSocioItem {
	id: number;
	nombre: string;
	logo_url: string | null;
	transacciones: number;
	clientes: number;
}

export interface DistribucionTipoItem {
	tipo: string;
	cantidad: number;
	porcentaje: number;
}

export interface DashboardOut {
	kpis: KpisGlobales;
	transacciones_30d: SerieDia[];
	ultimas_transacciones: TransaccionOut[];
	top_socios: TopSocioItem[];
	distribucion_tipos: DistribucionTipoItem[];
}

export interface FacturaOut {
	id: number;
	tenant_id: number;
	socio_nombre: string;
	plan_nombre: string;
	periodo: string;
	monto: number;
	moneda: string;
	estado: 'pendiente' | 'pagada' | 'vencida' | 'anulada';
	emitida_en: string;
	vence_en: string;
	pagada_en: string | null;
	metodo: string | null;
	referencia: string | null;
}
