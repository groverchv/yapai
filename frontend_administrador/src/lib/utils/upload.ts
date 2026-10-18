import { api, ApiError } from '../api/client';
import type { FirmaUploadOut } from '../types';

export interface UploadOptions {
	carpeta?: string;
	tenantId?: number;
}

/**
 * Sube una imagen a Cloudinary usando parámetros firmados del backend.
 * 1) Solicita la firma al endpoint `/admin/socios/uploads/firma`.
 * 2) Sube el archivo vía FormData a `https://api.cloudinary.com/v1_1/<cloud_name>/image/upload`.
 * 3) Retorna la URL segura HTTPS del recurso alojado.
 */
export async function subirImagenCloudinary(archivo: File, opciones: UploadOptions = {}): Promise<string> {
	const params = new URLSearchParams();
	if (opciones.carpeta) params.set('carpeta', opciones.carpeta);
	if (opciones.tenantId) params.set('tenant_id', String(opciones.tenantId));

	// 1. Obtener firma
	const firma = await api.post<FirmaUploadOut>(`/admin/socios/uploads/firma?${params.toString()}`);

	// 2. Preparar FormData para Cloudinary
	const formData = new FormData();
	formData.append('file', archivo);
	formData.append('api_key', firma.api_key);
	formData.append('timestamp', String(firma.timestamp));
	formData.append('folder', firma.folder);
	formData.append('signature', firma.signature);

	// 3. Subir a la API de Cloudinary
	const urlCloudinary = `https://api.cloudinary.com/v1_1/${firma.cloud_name}/image/upload`;
	const res = await fetch(urlCloudinary, {
		method: 'POST',
		body: formData
	});

	if (!res.ok) {
		const errData = await res.json().catch(() => null);
		throw new ApiError(res.status, errData?.error?.message ?? 'Error al subir la imagen a Cloudinary');
	}

	const data = await res.json();
	return data.secure_url ?? data.url;
}
