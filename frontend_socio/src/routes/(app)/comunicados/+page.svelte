<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import ImageUploader from '#lib/components/ui/ImageUploader.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import { toast } from '#lib/stores/toast.svelte';
	import type { Comunicado, Premio } from '#lib/types';
	import { formatFecha } from '#lib/utils/format';

	let comunicados = $state<Comunicado[]>([]);
	let premios = $state<Premio[]>([]);
	let cargando = $state(true);

	let modal = $state(false);
	let editando = $state<Comunicado | null>(null);
	let formTitulo = $state('');
	let formDescripcion = $state('');
	let formImagen = $state<string | null>(null);
	let formPublicId = $state<string | null>(null);
	let formPremio = $state('');
	let formVigencia = $state('');
	let guardando = $state(false);
	let errorModal = $state('');

	const ESTADOS: Record<string, { texto: string; variante: 'ok' | 'warn' | 'bad' | 'info' }> = {
		borrador: { texto: 'Borrador', variante: 'warn' },
		publicado: { texto: 'Publicado', variante: 'ok' },
		archivado: { texto: 'Archivado', variante: 'bad' }
	};

	async function cargar() {
		cargando = true;
		try {
			[comunicados, premios] = await Promise.all([
				api.get<Comunicado[]>('/socio/comunicados'),
				api.get<Premio[]>('/socio/premios')
			]);
		} catch (e) {
			toast.error(e instanceof Error ? e.message : 'Error al cargar');
		} finally {
			cargando = false;
		}
	}

	function abrirNuevo() {
		editando = null;
		formTitulo = ''; formDescripcion = ''; formImagen = null; formPublicId = null;
		formPremio = ''; formVigencia = ''; errorModal = '';
		modal = true;
	}

	function abrirEditar(c: Comunicado) {
		editando = c;
		formTitulo = c.titulo;
		formDescripcion = c.descripcion ?? '';
		formImagen = c.imagen_url;
		formPublicId = c.imagen_public_id;
		formPremio = c.premio_id ? String(c.premio_id) : '';
		formVigencia = c.vigencia_hasta ? c.vigencia_hasta.slice(0, 10) : '';
		errorModal = '';
		modal = true;
	}

	async function guardar(e: SubmitEvent) {
		e.preventDefault();
		if (!formImagen) { errorModal = 'Sube una imagen para la oferta'; return; }
		guardando = true;
		errorModal = '';
		const payload = {
			titulo: formTitulo.trim(),
			descripcion: formDescripcion.trim() || null,
			imagen_url: formImagen,
			imagen_public_id: formPublicId,
			premio_id: formPremio ? Number(formPremio) : null,
			vigencia_hasta: formVigencia ? `${formVigencia}T23:59:59` : null
		};
		try {
			if (editando) {
				await api.patch(`/socio/comunicados/${editando.id}`, payload);
				toast.exito('Oferta actualizada');
			} else {
				await api.post('/socio/comunicados', payload);
				toast.exito('Oferta creada — publícala para que aparezca en la app');
			}
			modal = false;
			await cargar();
		} catch (err) {
			errorModal = err instanceof Error ? err.message : 'Error al guardar';
		} finally {
			guardando = false;
		}
	}

	async function cambiarEstado(c: Comunicado, accion: 'publicar' | 'archivar') {
		try {
			await api.post(`/socio/comunicados/${c.id}/${accion}`);
			toast.exito(accion === 'publicar' ? 'Oferta publicada en la app' : 'Oferta archivada');
			await cargar();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Error');
		}
	}

	async function eliminar(c: Comunicado) {
		if (!confirm(`¿Eliminar "${c.titulo}"?`)) return;
		try {
			await api.delete(`/socio/comunicados/${c.id}`);
			toast.exito('Oferta eliminada');
			await cargar();
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Error');
		}
	}

	onMount(cargar);
</script>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-lg font-semibold text-slate-800">Ofertas y comunicados</h2>
			<p class="text-sm text-slate-500">Aparecen en el feed de la app de tus clientes.</p>
		</div>
		<button onclick={abrirNuevo}
			class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">
			<Icon name="plus" clase="mr-1 inline h-4 w-4" />Nueva oferta
		</button>
	</div>

	{#if cargando}
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
			{#each Array(3) as _}
				<div class="h-64 animate-pulse rounded-xl bg-slate-100"></div>
			{/each}
		</div>
	{:else if comunicados.length === 0}
		<div class="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
			<Icon name="image-plus" clase="mx-auto h-10 w-10 text-slate-300" />
			<p class="mt-3 font-medium text-slate-600">Aún no tienes ofertas</p>
			<p class="mt-1 text-sm text-slate-400">Publica promociones con imagen y tus clientes las verán en la app.</p>
			<button onclick={abrirNuevo}
				class="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">
				Crear mi primera oferta
			</button>
		</div>
	{:else}
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
			{#each comunicados as c (c.id)}
				<div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
					<div class="relative">
						<img src={c.imagen_url} alt={c.titulo} class="h-40 w-full object-cover" />
						<div class="absolute left-2 top-2">
							<Badge texto={ESTADOS[c.estado].texto} variante={ESTADOS[c.estado].variante} />
						</div>
					</div>
					<div class="p-4">
						<h3 class="font-semibold text-slate-800">{c.titulo}</h3>
						{#if c.descripcion}
							<p class="mt-1 line-clamp-2 text-sm text-slate-500">{c.descripcion}</p>
						{/if}
						<p class="mt-2 text-xs text-slate-400">
							{#if c.premio_nombre}Premio: {c.premio_nombre} · {/if}
							{#if c.vigencia_hasta}Hasta {formatFecha(c.vigencia_hasta)}{:else}Sin vencimiento{/if}
						</p>
						<div class="mt-3 flex gap-2 border-t border-slate-100 pt-3">
							{#if c.estado !== 'publicado'}
								<button onclick={() => cambiarEstado(c, 'publicar')}
									class="flex-1 rounded-lg bg-emerald-600 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700">
									Publicar
								</button>
							{:else}
								<button onclick={() => cambiarEstado(c, 'archivar')}
									class="flex-1 rounded-lg border border-slate-300 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50">
									Archivar
								</button>
							{/if}
							<button onclick={() => abrirEditar(c)}
								class="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50">
								Editar
							</button>
							<button onclick={() => eliminar(c)} aria-label="Eliminar"
								class="rounded-lg border border-red-200 px-3 py-1.5 text-xs text-red-500 hover:bg-red-50">
								<Icon name="x" clase="h-3.5 w-3.5" />
							</button>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<Modal abierto={modal} titulo={editando ? 'Editar oferta' : 'Nueva oferta'} onclose={() => (modal = false)}>
	<form onsubmit={guardar} class="space-y-4">
		<div>
			<span class="mb-1 block text-sm font-medium text-slate-700">Imagen (aparece en el feed de la app)</span>
			<ImageUploader bind:value={formImagen} bind:publicId={formPublicId} carpeta="comunicados" />
		</div>
		<div>
			<label for="ct" class="mb-1 block text-sm font-medium text-slate-700">Título</label>
			<input id="ct" type="text" bind:value={formTitulo} required minlength="3" maxlength="160"
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
				placeholder="Ej: 2x1 en pizzas familiares" />
		</div>
		<div>
			<label for="cd" class="mb-1 block text-sm font-medium text-slate-700">Descripción (opcional)</label>
			<textarea id="cd" bind:value={formDescripcion} rows="2" maxlength="2000"
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
				placeholder="Detalle de la promoción"></textarea>
		</div>
		<div class="grid grid-cols-2 gap-3">
			<div>
				<label for="cp" class="mb-1 block text-sm font-medium text-slate-700">Vincular premio</label>
				<select id="cp" bind:value={formPremio}
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
					<option value="">— Ninguno —</option>
					{#each premios as p (p.id)}
						<option value={p.id}>{p.nombre} ({p.costo_puntos} pts)</option>
					{/each}
				</select>
			</div>
			<div>
				<label for="cv" class="mb-1 block text-sm font-medium text-slate-700">Vigente hasta</label>
				<input id="cv" type="date" bind:value={formVigencia}
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
			</div>
		</div>
		{#if errorModal}
			<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{errorModal}</p>
		{/if}
		<button type="submit" disabled={guardando}
			class="w-full rounded-lg bg-emerald-600 py-2.5 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
			{guardando ? 'Guardando…' : editando ? 'Guardar cambios' : 'Crear oferta'}
		</button>
	</form>
</Modal>
