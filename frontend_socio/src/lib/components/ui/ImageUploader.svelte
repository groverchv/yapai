<script lang="ts">
	// Subida de imágenes a Cloudinary (firma del backend → upload directo).
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
		carpeta = 'comunicados',
		aspecto = 'video' as 'video' | 'square'
	}: {
		value?: string | null;
		publicId?: string | null;
		carpeta?: string;
		aspecto?: 'video' | 'square';
	} = $props();

	let subiendo = $state(false);
	let error = $state('');
	let inputEl: HTMLInputElement;

	async function subir(e: Event) {
		const file = (e.target as HTMLInputElement).files?.[0];
		if (!file) return;
		if (!file.type.startsWith('image/')) {
			error = 'Solo imágenes (jpg, png, webp)';
			return;
		}
		if (file.size > 5 * 1024 * 1024) {
			error = 'La imagen no puede superar 5 MB';
			return;
		}
		error = '';
		subiendo = true;
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
			if (!res.ok) throw new Error(data.error?.message ?? 'Error al subir');
			value = data.secure_url;
			publicId = data.public_id;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error al subir';
		} finally {
			subiendo = false;
			if (inputEl) inputEl.value = '';
		}
	}
</script>

<div>
	<input bind:this={inputEl} type="file" accept="image/*" class="hidden" onchange={subir} />
	{#if value}
		<div class="relative inline-block">
			<img src={value} alt="Imagen subida"
				class="rounded-lg border border-slate-200 object-cover
					{aspecto === 'video' ? 'h-32 w-56' : 'h-32 w-32'}" />
			<button type="button" onclick={() => { value = null; publicId = null; }}
				class="absolute -right-2 -top-2 rounded-full bg-red-600 p-1 text-white shadow hover:bg-red-700"
				aria-label="Quitar imagen">
				<Icon name="x" clase="h-3.5 w-3.5" />
			</button>
		</div>
	{:else}
		<button type="button" onclick={() => inputEl.click()} disabled={subiendo}
			class="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed
				border-slate-300 text-slate-400 transition hover:border-emerald-400 hover:text-emerald-600
				disabled:opacity-50 {aspecto === 'video' ? 'h-32 w-56' : 'h-32 w-32'}">
			{#if subiendo}
				<Icon name="loader" clase="h-6 w-6 animate-spin" />
				<span class="text-xs">Subiendo…</span>
			{:else}
				<Icon name="image-plus" clase="h-6 w-6" />
				<span class="text-xs">Subir imagen</span>
			{/if}
		</button>
	{/if}
	{#if error}
		<p class="mt-2 text-xs text-red-600">{error}</p>
	{/if}
</div>
