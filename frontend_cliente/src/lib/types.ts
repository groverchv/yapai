export interface TokenPair {
	access_token: string;
	refresh_token: string;
}

export interface Cliente {
	id: number;
	nombre: string;
	ci: string;
	telefono: string;
	saldo_puntos: number;
	puntos_congelados: number;
	foto_url: string | null;
	codigo_referido: string | null;
	created_at: string;
}

export interface LoginClienteResponse {
	tokens: TokenPair;
	cliente: Cliente;
}

export interface Wallet {
	saldo: number;
	congelado: number;
	disponible: number;
}

export interface Movimiento {
	id: number;
	created_at: string;
	tipo: string;
	puntos: number;
	comercio: string | null;
	sucursal: string | null;
	premio: string | null;
	detalle: Record<string, unknown> | null;
}

export interface Pagina<T> {
	items: T[];
	total: number;
	page: number;
	size: number;
}

export interface Comercio {
	id: number;
	nombre_comercial: string;
	logo_url: string | null;
	categoria: string | null;
	total_premios: number;
	puntos_ganados: number;
}

export interface Categoria {
	id: number;
	nombre: string;
}

export interface SucursalInfo {
	id: number;
	nombre: string;
	direccion: string | null;
	latitud: number | null;
	longitud: number | null;
}

export interface ComercioDetalle {
	id: number;
	nombre_comercial: string;
	logo_url: string | null;
	categoria: string | null;
	sucursales: SucursalInfo[];
}

export interface Premio {
	id: number;
	nombre: string;
	descripcion: string | null;
	costo_puntos: number;
	imagen_url: string | null;
	alcanzable: boolean;
	vigencia_hasta: string | null;
}

export interface ProximoPremio {
	premio_id: number;
	tenant_id: number;
	nombre: string;
	imagen_url: string | null;
	costo_puntos: number;
	comercio: string;
	logo_url: string | null;
	saldo: number;
	faltante: number;
	alcanzable: boolean;
}

export interface Comunicado {
	id: number;
	titulo: string;
	descripcion: string | null;
	imagen_url: string;
	premio_id: number | null;
	publicado_en: string | null;
	vigencia_hasta: string | null;
	tenant_id: number;
	comercio: string;
	logo_url: string | null;
}

export interface Pase {
	id: number;
	codigo_qr: string;
	pin_corto: string;
	puntos: number;
	estado: string;
	expira_en: string | null;
	premio_nombre: string;
	comercio: string;
	created_at: string;
}

export interface FirmaUpload {
	cloud_name: string;
	api_key: string;
	timestamp: number;
	signature: string;
	folder: string;
}
