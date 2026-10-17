export function formatFecha(iso: string | null | undefined): string {
	if (!iso) return '—';
	return new Date(iso).toLocaleString('es-BO', {
		day: '2-digit', month: '2-digit', year: 'numeric',
		hour: '2-digit', minute: '2-digit'
	});
}

export function formatFechaCorta(iso: string | null | undefined): string {
	if (!iso) return '—';
	return new Date(iso).toLocaleDateString('es-BO');
}

export function formatDinero(monto: number, moneda = 'BOB'): string {
	try {
		return new Intl.NumberFormat('es-BO', { style: 'currency', currency: moneda }).format(monto);
	} catch {
		return `${monto.toFixed(2)} ${moneda}`;
	}
}

export const TIPOS_MOVIMIENTO: Record<string, string> = {
	registro: 'Registro',
	ruleta: 'Ruleta',
	bonus_manual: 'Bonus manual',
	canje: 'Canje',
	congelar: 'Congelar',
	liberar: 'Liberar',
	anulacion: 'Anulación'
};
