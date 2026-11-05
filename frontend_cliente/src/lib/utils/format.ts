/** Genera una URL de Cloudinary con transformación on-the-fly (miniaturas).
 *  Deja intactas URLs que no son de Cloudinary. */
export function cloudinaryThumb(url: string, w = 400): string {
	if (url.includes('res.cloudinary.com') && url.includes('/image/upload/')) {
		return url.replace('/image/upload/', `/image/upload/w_${w},c_fill,q_auto,f_auto/`);
	}
	return url;
}

const fmtFecha = new Intl.DateTimeFormat('es-BO', {
	day: '2-digit', month: '2-digit', year: '2-digit',
	hour: '2-digit', minute: '2-digit'
});
const fmtCorta = new Intl.DateTimeFormat('es-BO', { day: '2-digit', month: '2-digit' });

/** dd/MM/yy HH:mm (equivalente a DateFormat de la app móvil). */
export function fecha(iso: string | null | undefined): string {
	if (!iso) return '—';
	try {
		return fmtFecha.format(new Date(iso));
	} catch {
		return iso;
	}
}

/** dd/MM para vigencias. */
export function vence(iso: string | null | undefined): string {
	if (!iso) return '';
	try {
		return fmtCorta.format(new Date(iso));
	} catch {
		return '';
	}
}

/** Badge "NUEVA": publicado hace menos de 72 h. */
export function esNueva(publicadoEn: string | null | undefined): boolean {
	if (!publicadoEn) return false;
	const t = Date.parse(publicadoEn);
	if (Number.isNaN(t)) return false;
	return Date.now() - t < 72 * 3600 * 1000;
}

export function iniciales(nombre: string | null | undefined): string {
	const partes = (nombre ?? '?').trim().split(/\s+/);
	return partes.slice(0, 2).map((p) => p[0]?.toUpperCase() ?? '').join('');
}

/** Compartir vía Web Share API; en desktop copia al portapapeles. */
export async function compartir(texto: string): Promise<'shared' | 'copied'> {
	if (navigator.share) {
		try {
			await navigator.share({ text: texto });
			return 'shared';
		} catch {
			// usuario canceló o no soportado → fallback a copiar
		}
	}
	await navigator.clipboard.writeText(texto);
	return 'copied';
}

export function debounce<T extends (...args: Parameters<T>) => void>(fn: T, ms: number) {
	let t: ReturnType<typeof setTimeout> | undefined;
	return (...args: Parameters<T>) => {
		clearTimeout(t);
		t = setTimeout(() => fn(...args), ms);
	};
}
