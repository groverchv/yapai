<script lang="ts">
	import { onMount } from 'svelte';
	import { api, ApiError } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import type { CategoriaOut } from '#lib/types';

	let items = $state<CategoriaOut[]>([]);
	let cargando = $state(false);
	let mensaje = $state('');
	let modal = $state<CategoriaOut | 'nueva' | null>(null);
	let f = $state({ nombre: '', icono_url: '' });

	const columnas = [
		{ key: 'nombre', label: 'Nombre' },
		{ key: 'slug', label: 'Slug' },
		{ key: 'socios_vinculados', label: 'Socios' },
		{ key: 'activa', label: 'Estado' }
	];

	async function cargar() {
		cargando = true;
		try { items = await api.get('/admin/categorias'); }
		finally { cargando = false; }
	}

	function abrirNueva() { f = { nombre: '', icono_url: '' }; modal = 'nueva'; }
	function abrirEditar(c: CategoriaOut) { f = { nombre: c.nombre, icono_url: c.icono_url ?? '' }; modal = c; }

	async function guardar() {
		try {
			if (modal === 'nueva') {
				await api.post('/admin/categorias', { nombre: f.nombre, icono_url: f.icono_url || null });
			} else if (modal) {
				await api.patch(`/admin/categorias/${modal.id}`, { nombre: f.nombre, icono_url: f.icono_url || null });
			}
			modal = null;
			cargar();
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error';
		}
	}

	async function toggle(c: CategoriaOut) {
		await api.patch(`/admin/categorias/${c.id}`, { activa: !c.activa });
		cargar();
	}

	async function eliminar(c: CategoriaOut) {
		try {
			await api.delete(`/admin/categorias/${c.id}`);
			mensaje = 'Categoría eliminada';
			cargar();
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error';
		}
	}

	onMount(cargar);
	const input = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none';
</script>

<div class="mb-4 flex items-center justify-between">
	{#if mensaje}<p class="rounded-lg bg-sky-50 px-4 py-2 text-sm text-sky-700">{mensaje}</p>{:else}<span></span>{/if}
	<button onclick={abrirNueva}
		class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
		+ Nueva categoría
	</button>
</div>

<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
	<DataTable {columnas} filas={items as unknown as Record<string, unknown>[]} {cargando}>
		{#snippet celda({ key, fila })}
			{@const c = fila as unknown as CategoriaOut}
			{#if key === 'activa'}
				<Badge texto={c.activa ? 'activa' : 'inactiva'} variante={c.activa ? 'ok' : 'neutral'} />
			{:else}{c[key as keyof CategoriaOut]}{/if}
		{/snippet}
		{#snippet acciones(fila)}
			{@const c = fila as unknown as CategoriaOut}
			<button onclick={() => abrirEditar(c)} class="mr-2 text-xs font-medium text-indigo-600 hover:underline">Editar</button>
			<button onclick={() => toggle(c)} class="mr-2 text-xs font-medium text-amber-600 hover:underline">
				{c.activa ? 'Desactivar' : 'Activar'}
			</button>
			<button onclick={() => eliminar(c)} disabled={c.socios_vinculados > 0}
				title={c.socios_vinculados > 0 ? 'No se puede eliminar: tiene socios vinculados' : ''}
				class="text-xs font-medium text-red-600 hover:underline disabled:cursor-not-allowed disabled:text-slate-300">
				Eliminar
			</button>
		{/snippet}
	</DataTable>
</div>

<Modal abierto={modal !== null} titulo={modal === 'nueva' ? 'Nueva categoría' : 'Editar categoría'} onclose={() => (modal = null)}>
	<form onsubmit={(e) => { e.preventDefault(); guardar(); }} class="space-y-4">
		<div>
			<label for="n" class="mb-1 block text-sm font-medium text-slate-700">Nombre *</label>
			<input id="n" bind:value={f.nombre} required class={input} />
		</div>
		<div>
			<label for="i" class="mb-1 block text-sm font-medium text-slate-700">URL de ícono</label>
			<input id="i" bind:value={f.icono_url} class={input} placeholder="https://…" />
		</div>
		<div class="flex justify-end gap-2">
			<button type="button" onclick={() => (modal = null)} class="rounded-lg border border-slate-300 px-4 py-2 text-sm">Cancelar</button>
			<button type="submit" class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">Guardar</button>
		</div>
	</form>
</Modal>
