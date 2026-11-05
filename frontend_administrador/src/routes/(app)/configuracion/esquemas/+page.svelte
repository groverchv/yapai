<script lang="ts">
	import { onMount } from 'svelte';
	import { api, ApiError } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import type { EsquemaOut } from '#lib/types';
	import { formatDinero } from '#lib/utils/format';

	let items = $state<EsquemaOut[]>([]);
	let cargando = $state(false);
	let mensaje = $state('');
	let modal = $state<EsquemaOut | 'nuevo' | null>(null);
	let f = $state({ nombre: '', costo_registro: 0, costo_canje: 0, moneda: 'BOB' });
	let montosBloqueados = $derived(modal !== null && modal !== 'nuevo' && modal.has_usage);

	const columnas = [
		{ key: 'nombre', label: 'Nombre' },
		{ key: 'costo_registro', label: 'Costo registro' },
		{ key: 'costo_canje', label: 'Costo canje' },
		{ key: 'moneda', label: 'Moneda' },
		{ key: 'activo', label: 'Estado' },
		{ key: 'has_usage', label: 'En uso' }
	];

	async function cargar() {
		cargando = true;
		try { items = await api.get('/admin/esquemas'); }
		finally { cargando = false; }
	}

	function abrirNuevo() { f = { nombre: '', costo_registro: 0, costo_canje: 0, moneda: 'BOB' }; modal = 'nuevo'; }
	function abrirEditar(e: EsquemaOut) {
		f = { nombre: e.nombre, costo_registro: e.costo_registro, costo_canje: e.costo_canje, moneda: e.moneda };
		modal = e;
	}

	async function guardar() {
		try {
			if (modal === 'nuevo') {
				await api.post('/admin/esquemas', { ...f });
			} else if (modal) {
				const body: Record<string, unknown> = { nombre: f.nombre };
				if (!modal.has_usage) Object.assign(body, { costo_registro: f.costo_registro, costo_canje: f.costo_canje, moneda: f.moneda });
				await api.patch(`/admin/esquemas/${modal.id}`, body);
			}
			modal = null;
			cargar();
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error';
		}
	}

	async function toggle(e: EsquemaOut) {
		await api.patch(`/admin/esquemas/${e.id}`, { activo: !e.activo });
		cargar();
	}

	async function eliminar(e: EsquemaOut) {
		try {
			await api.delete(`/admin/esquemas/${e.id}`);
			mensaje = 'Esquema eliminado';
			cargar();
		} catch (err) {
			mensaje = err instanceof ApiError ? err.detail : 'Error';
		}
	}

	onMount(cargar);
	const input = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100 focus:border-indigo-500 focus:outline-none';
</script>

<div class="mb-4 flex flex-wrap items-center justify-between gap-3">
	{#if mensaje}<p class="rounded-lg bg-sky-50 px-4 py-2 text-sm text-sky-700">{mensaje}</p>{:else}<span></span>{/if}
	<button onclick={abrirNuevo}
		class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
		+ Nuevo esquema
	</button>
</div>

<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
	<DataTable {columnas} filas={items as unknown as Record<string, unknown>[]} {cargando}>
		{#snippet celda({ key, fila })}
			{@const e = fila as unknown as EsquemaOut}
			{#if key === 'costo_registro'}{formatDinero(e.costo_registro, e.moneda)}
			{:else if key === 'costo_canje'}{formatDinero(e.costo_canje, e.moneda)}
			{:else if key === 'activo'}<Badge texto={e.activo ? 'activo' : 'inactivo'} variante={e.activo ? 'ok' : 'neutral'} />
			{:else if key === 'has_usage'}
				{#if e.has_usage}<Badge texto="en uso" variante="info" />{:else}<span class="text-slate-400">—</span>{/if}
			{:else}{e[key as keyof EsquemaOut]}{/if}
		{/snippet}
		{#snippet acciones(fila)}
			{@const e = fila as unknown as EsquemaOut}
			<button onclick={() => abrirEditar(e)} class="mr-2 text-xs font-medium text-indigo-600 hover:underline">Editar</button>
			<button onclick={() => toggle(e)} class="mr-2 text-xs font-medium text-amber-600 hover:underline">
				{e.activo ? 'Desactivar' : 'Activar'}
			</button>
			<button onclick={() => eliminar(e)} disabled={e.has_usage}
				title={e.has_usage ? 'No se puede eliminar un esquema en uso' : ''}
				class="text-xs font-medium text-red-600 hover:underline disabled:cursor-not-allowed disabled:text-slate-300">
				Eliminar
			</button>
		{/snippet}
	</DataTable>
</div>

<Modal abierto={modal !== null} titulo={modal === 'nuevo' ? 'Nuevo esquema' : 'Editar esquema'} onclose={() => (modal = null)}>
	<form onsubmit={(e) => { e.preventDefault(); guardar(); }} class="space-y-4">
		{#if montosBloqueados}
			<p class="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
				Este esquema tiene transacciones/liquidaciones asociadas: los montos son inmutables (protección financiera).
			</p>
		{/if}
		<div>
			<label for="n" class="mb-1 block text-sm font-medium text-slate-700">Nombre *</label>
			<input id="n" bind:value={f.nombre} required class={input} />
		</div>
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
			<div>
				<label for="cr" class="mb-1 block text-sm font-medium text-slate-700">Costo registro</label>
				<input id="cr" type="number" step="0.01" min="0" bind:value={f.costo_registro} disabled={montosBloqueados} class={input} />
			</div>
			<div>
				<label for="cc" class="mb-1 block text-sm font-medium text-slate-700">Costo canje</label>
				<input id="cc" type="number" step="0.01" min="0" bind:value={f.costo_canje} disabled={montosBloqueados} class={input} />
			</div>
			<div>
				<label for="m" class="mb-1 block text-sm font-medium text-slate-700">Moneda</label>
				<input id="m" bind:value={f.moneda} disabled={montosBloqueados} class={input} />
			</div>
		</div>
		<div class="flex justify-end gap-2">
			<button type="button" onclick={() => (modal = null)} class="rounded-lg border border-slate-300 px-4 py-2 text-sm">Cancelar</button>
			<button type="submit" class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">Guardar</button>
		</div>
	</form>
</Modal>
