<script lang="ts">
	// Subida de imágenes a Cloudinary (vía backend directo o firma fallback)
	import { api } from '#lib/api/client';
	import Icon from './Icon.svelte';

	interface Firma {
		cloud_name: string;
		api_key: string;
		timestamp: number;
		folder: string;
		signature: string;
	}

	let {
		value = $bindable<string | null>(null),
		publicId = $bindable<string | null>(null),
		carpeta = 'logo',
		aspecto = 'square' as 'video' | 'square'
	}: {
		value?: string | null;
		publicId?: string | null;
		carpeta?: string;
		aspecto?: 'video' | 'square';
	} = $props();

	let subiendo = $state(false);
	let arrastrando = $state(false);
	let error = $state('');
	let inputEl: HTMLInputElement;

	async function procesarArchivo(file: File) {
		if (!file.type.startsWith('image/')) {
			error = 'Solo se admiten imágenes (JPG, PNG, WebP, SVG)';
			return;
		}
		if (file.size > 10 * 1024 * 1024) {
			error = 'La imagen no puede superar los 10 MB';
			return;
		}

		error = '';
		subiendo = true;

		try {
			// Subida directa al backend de Yapai con el SDK de Cloudinary
			const form = new FormData();
			form.append('file', file);
			form.append('tipo', carpeta);

			const res = await api.upload<{ url: string; public_id?: string }>('/socio/media/upload', form);
			value = res.url;
			publicId = res.public_id ?? null;
		} catch (errBackend) {
			console.warn('Fallo backend upload, intentando con firma directa a Cloudinary:', errBackend);
			try {
				const firma = await api.post<Firma>(`/socio/comunicados/uploads/firma?carpeta=${carpeta}`);
				const form = new FormData();
				form.append('file', file);
				form.append('api_key', firma.api_key);
				form.append('timestamp', String(firma.timestamp));
				form.append('signature', firma.signature);
				form.append('folder', firma.folder);

				const res = await fetch(
					`https://api.cloudinary.com/v1_1/${firma.cloud_name}/image/upload`,
					{ method: 'POST', body: form }
				);
				const data = await res.json();
				if (!res.ok) throw new Error(data.error?.message ?? 'Error al subir a Cloudinary');
				value = data.secure_url;
				publicId = data.public_id;
			} catch (fallbackErr) {
				error = errBackend instanceof Error ? errBackend.message : 'Error al subir imagen a Cloudinary';
			}
		} finally {
			subiendo = false;
			if (inputEl) inputEl.value = '';
		}
	}

	function onFileChange(e: Event) {
		const file = (e.target as HTMLInputElement).files?.[0];
		if (file) procesarArchivo(file);
	}

	function onDrop(e: DragEvent) {
		e.preventDefault();
		arrastrando = false;
		const file = e.dataTransfer?.files?.[0];
		if (file) procesarArchivo(file);
	}
</script>

<div class="space-y-2">
	<input bind:this={inputEl} type="file" accept="image/*" class="hidden" onchange={onFileChange} />

	{#if value}
		<div class="group relative inline-flex flex-col items-start gap-2">
			<div class="relative overflow-hidden rounded-xl border-2 border-emerald-500/30 bg-slate-900/5 shadow-sm transition hover:shadow-md
				{aspecto === 'video' ? 'h-36 w-64' : 'h-32 w-32'}">
				<img src={value} alt="Imagen" class="h-full w-full object-cover" />
				<div class="absolute inset-0 flex items-center justify-center gap-2 bg-black/40 opacity-0 transition group-hover:opacity-100">
					<button type="button" onclick={() => inputEl.click()} disabled={subiendo}
						class="rounded-lg bg-white/90 p-1.5 text-slate-800 backdrop-blur-sm transition hover:bg-white hover:text-emerald-700"
						title="Cambiar imagen">
						<Icon name="image-plus" clase="h-4 w-4" />
					</button>
					<button type="button" onclick={() => { value = null; publicId = null; }}
						class="rounded-lg bg-red-600/90 p-1.5 text-white backdrop-blur-sm transition hover:bg-red-700"
						title="Eliminar imagen">
						<Icon name="trash" clase="h-4 w-4" />
					</button>
				</div>
			</div>
			<div class="flex items-center gap-1.5 text-[11px] text-emerald-700">
				<span class="inline-block h-2 w-2 rounded-full bg-emerald-500"></span>
				<span class="font-medium">Guardada en Cloudinary</span>
			</div>
		</div>
	{:else}
		<button
			type="button"
			onclick={() => inputEl.click()}
			ondragover={(e) => { e.preventDefault(); arrastrando = true; }}
			ondragleave={() => (arrastrando = false)}
			ondrop={onDrop}
			disabled={subiendo}
			class="flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed
				transition duration-150 disabled:opacity-50
				{arrastrando ? 'border-emerald-500 bg-emerald-50/50 text-emerald-700 scale-[0.99]' : 'border-slate-300 bg-slate-50/60 text-slate-500 hover:border-emerald-500 hover:bg-emerald-50/30 hover:text-emerald-700'}
				{aspecto === 'video' ? 'h-36 w-64' : 'h-32 w-32'}"
		>
			{#if subiendo}
				<Icon name="loader" clase="h-6 w-6 animate-spin text-emerald-600" />
				<span class="text-xs font-medium text-emerald-700">Subiendo a Cloudinary…</span>
			{:else}
				<div class="rounded-full bg-white p-2 shadow-sm border border-slate-200">
					<Icon name="image-plus" clase="h-5 w-5 text-emerald-600" />
				</div>
				<span class="text-xs font-medium">Subir imagen</span>
				<span class="text-[10px] text-slate-400">o arrastra aquí</span>
			{/if}
		</button>
	{/if}

	{#if error}
		<p class="text-xs font-medium text-red-600">{error}</p>
	{/if}
</div>

