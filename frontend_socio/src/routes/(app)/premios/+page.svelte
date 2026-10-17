<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import type { Premio } from '#lib/types';
	import { formatFecha } from '#lib/utils/format';

	let premios = $state<Premio[]>([]);
	let cargando = $state(true);
	let error = $state('');
	let mensaje = $state('');

	let modal = $state<'crear' | 'editar' | null>(null);
	let seleccionado = $state<Premio | null>(null);
	let formNombre = $state('');
	let formDescripcion = $state('');
	let formCosto = $state(100);
	let formImagen = $state('');
	let formStockLimitado = $state(false);
	let formStock = $state(0);
	let formVigencia = $state('');
	let guardando = $state(false);
	let errorModal = $state('');

	async function cargar() {
		cargando = true;
		error = '';
		try {
			premios = await api.get<Premio[]>('/socio/premios');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cargar';
		} finally {
			cargando = false;
		}
	}

	function abrirCrear() {
		seleccionado = null;
		formNombre = '';
		formDescripcion = '';
		formCosto = 100;
		formImagen = '';
		formStockLimitado = false;
		formStock = 0;
		formVigencia = '';
		errorModal = '';
		modal = 'crear';
	}

	function abrirEditar(p: Premio) {
		seleccionado = p;
		formNombre = p.nombre;
		formDescripcion = p.descripcion ?? '';
		formCosto = p.costo_puntos;
		formImagen = p.imagen_url ?? '';
		formStockLimitado = p.stock_limitado;
		formStock = p.stock ?? 0;
		formVigencia = p.vigencia_hasta ? p.vigencia_hasta.slice(0, 10) : '';
		errorModal = '';
		modal = 'editar';
	}

	async function guardar(e: SubmitEvent) {
		e.preventDefault();
		guardando = true;
		errorModal = '';
		try {
			const body = {
				nombre: formNombre,
				descripcion: formDescripcion || null,
				costo_puntos: formCosto,
				imagen_url: formImagen || null,
				stock_limitado: formStockLimitado,
				stock: formStockLimitado ? formStock : null,
				vigencia_hasta: formVigencia ? new Date(`${formVigencia}T23:59:59`).toISOString() : null
			};
			if (modal === 'crear') await api.post('/socio/premios', body);
			else if (seleccionado) await api.patch(`/socio/premios/${seleccionado.id}`, body);
			modal = null;
			cargar();
		} catch (err) {
			errorModal = err instanceof Error ? err.message : 'Error al guardar';
		} finally {
			guardando = false;
		}
	}

	async function accion(p: Premio, op: 'activar' | 'desactivar') {
		error = '';
		mensaje = '';
		try {
			await api.post(`/socio/premios/${p.id}/${op}`);
			cargar();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error';
		}
	}

	onMount(cargar);
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<p class="text-sm text-slate-500">
			El costo en puntos no puede editarse mientras haya pases digitales activos del premio.
		</p>
		<button onclick={abrirCrear}
			class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
			+ Nuevo premio
		</button>
	</div>

	{#if error}
		<p class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
	{/if}
	{#if mensaje}
		<p class="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{mensaje}</p>
	{/if}

	{#if cargando}
		<p class="text-slate-400">Cargando…</p>
	{:else}
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
			{#each premios as p}
				<div class="rounded-xl border border-slate-200 bg-white p-5">
					<div class="flex items-start justify-between gap-2">
						<div class="flex items-center gap-3">
							{#if p.imagen_url}
								<img src={p.imagen_url} alt={p.nombre} class="h-12 w-12 rounded-lg object-cover" />
							{:else}
								<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 text-slate-400"><Icon name="gift" clase="h-6 w-6" /></div>
							{/if}
							<div>
								<h3 class="font-semibold text-slate-800">{p.nombre}</h3>
								<p class="text-sm font-bold text-emerald-600">{p.costo_puntos} pts</p>
							</div>
						</div>
						<Badge texto={p.estado === 'activo' ? 'Activo' : p.estado === 'agotado' ? 'Agotado' : 'Inactivo'}
							variante={p.estado === 'activo' ? 'ok' : p.estado === 'agotado' ? 'warn' : 'neutral'} />
					</div>

					{#if p.descripcion}
						<p class="mt-2 text-sm text-slate-500">{p.descripcion}</p>
					{/if}

					<div class="mt-3 flex flex-wrap gap-2 text-xs">
						{#if p.stock_limitado}
							<Badge texto="Stock: {p.stock ?? 0}" variante={(p.stock ?? 0) <= 3 ? 'warn' : 'info'} />
						{:else}
							<Badge texto="Stock ilimitado" variante="neutral" />
						{/if}
						{#if p.pases_activos > 0}
							<Badge texto="{p.pases_activos} pase(s) activo(s)" variante="info" />
						{/if}
						{#if p.vigencia_hasta}
							<Badge
								texto={p.vigencia_hasta < new Date().toISOString() ? `Venció ${formatFecha(p.vigencia_hasta)}` : `Vence ${formatFecha(p.vigencia_hasta)}`}
								variante={p.vigencia_hasta < new Date().toISOString() ? 'bad' : 'warn'} />
						{/if}
					</div>

					<div class="mt-4 flex gap-3 text-sm">
						<button onclick={() => abrirEditar(p)} class="text-emerald-600 hover:underline">Editar</button>
						{#if p.estado === 'activo' || p.estado === 'agotado'}
							<button onclick={() => accion(p, 'desactivar')} class="text-red-600 hover:underline">Desactivar</button>
						{:else}
							<button onclick={() => accion(p, 'activar')} class="text-green-600 hover:underline">Activar</button>
						{/if}
					</div>
				</div>
			{:else}
				<p class="text-slate-400">No tienes premios registrados.</p>
			{/each}
		</div>
	{/if}
</div>

<Modal abierto={modal !== null} titulo={modal === 'crear' ? 'Nuevo premio' : 'Editar premio'}
	onclose={() => (modal = null)}>
	<form onsubmit={guardar} class="space-y-4">
		<div>
			<label for="pn" class="mb-1 block text-sm font-medium text-slate-700">Nombre</label>
			<input id="pn" type="text" bind:value={formNombre} required minlength="2"
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
		</div>
		<div>
			<label for="pd" class="mb-1 block text-sm font-medium text-slate-700">Descripción corta</label>
			<input id="pd" type="text" bind:value={formDescripcion}
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
		</div>
		<div class="grid grid-cols-2 gap-3">
			<div>
				<label for="pc" class="mb-1 block text-sm font-medium text-slate-700">Costo en puntos</label>
				<input id="pc" type="number" bind:value={formCosto} required min="1"
					disabled={modal === 'editar' && (seleccionado?.pases_activos ?? 0) > 0}
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100" />
				{#if modal === 'editar' && (seleccionado?.pases_activos ?? 0) > 0}
					<p class="mt-1 text-xs text-amber-600">Bloqueado: hay pases activos pendientes.</p>
				{/if}
			</div>
			<div>
				<label for="pi" class="mb-1 block text-sm font-medium text-slate-700">Imagen (URL)</label>
				<input id="pi" type="url" bind:value={formImagen}
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
			</div>
		</div>
		<label class="flex items-center gap-2 text-sm text-slate-700">
			<input type="checkbox" bind:checked={formStockLimitado} class="rounded" />
			Inventario limitado
		</label>
		{#if formStockLimitado}
			<div>
				<label for="ps" class="mb-1 block text-sm font-medium text-slate-700">Stock disponible</label>
				<input id="ps" type="number" bind:value={formStock} required min="0"
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
				<p class="mt-1 text-xs text-slate-400">Al llegar a 0 el premio se marca "Agotado" y se oculta en la app.</p>
			</div>
		{/if}
		<div>
			<label for="pv" class="mb-1 block text-sm font-medium text-slate-700">Vigencia (opcional)</label>
			<input id="pv" type="date" bind:value={formVigencia}
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
			<p class="mt-1 text-xs text-slate-400">Promoción temporal: tras esa fecha el premio deja de ser canjeable y se oculta en la app.</p>
		</div>
		{#if errorModal}
			<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{errorModal}</p>
		{/if}
		<button type="submit" disabled={guardando}
			class="w-full rounded-lg bg-emerald-600 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
			{guardando ? 'Guardando…' : 'Guardar premio'}
		</button>
	</form>
</Modal>
