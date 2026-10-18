<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { onMount } from 'svelte';
	import { api, descargarCsv, ApiError } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import Pagination from '#lib/components/ui/Pagination.svelte';
	import type { Pagina, SocioListItem } from '#lib/types';
	import { formatFechaCorta } from '#lib/utils/format';

	let datos = $state<Pagina<SocioListItem> | null>(null);
	let cargando = $state(false);
	let estado = $state('');
	let q = $state('');
	let nit = $state('');
	let page = $state(1);
	let mensaje = $state('');
	let confirmar = $state<{ socio: SocioListItem; accion: 'suspender' | 'reactivar' } | null>(null);
	let debounce: ReturnType<typeof setTimeout>;

	const columnas = [
		{ key: 'nombre_comercial', label: 'Nombre comercial' },
		{ key: 'nit_rut', label: 'NIT/RUT' },
		{ key: 'categoria', label: 'Categoría' },
		{ key: 'esquema', label: 'Esquema' },
		{ key: 'estado', label: 'Estado' },
		{ key: 'created_at', label: 'Alta' }
	];

	function queryString() {
		const p = new URLSearchParams({ page: String(page), size: '10' });
		if (estado) p.set('estado', estado);
		if (q) p.set('q', q);
		if (nit) p.set('nit', nit);
		return p.toString();
	}

	async function cargar() {
		cargando = true;
		try {
			datos = await api.get<Pagina<SocioListItem>>(`/admin/socios?${queryString()}`);
		} finally {
			cargando = false;
		}
	}

	function filtrar() {
		clearTimeout(debounce);
		debounce = setTimeout(() => { page = 1; cargar(); }, 350);
	}

	async function ejecutarEstado() {
		if (!confirmar) return;
		const { socio, accion } = confirmar;
		try {
			await api.post(`/admin/socios/${socio.id}/${accion}`);
			mensaje = `Socio ${accion === 'suspender' ? 'suspendido' : 'reactivado'} correctamente`;
			confirmar = null;
			cargar();
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error';
		}
	}

	async function accionSocio(s: SocioListItem, accion: 'forzar-reset' | 'reenviar-onboarding') {
		try {
			const r = await api.post<{ detail: string }>(`/admin/socios/${s.id}/${accion}`);
			mensaje = r.detail;
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error';
		}
	}

	function exportar() {
		const p = new URLSearchParams({ format: 'csv' });
		if (estado) p.set('estado', estado);
		if (q) p.set('q', q);
		if (nit) p.set('nit', nit);
		descargarCsv(`/admin/socios?${p}`, 'socios.csv');
	}

	onMount(cargar);
</script>

<div class="mb-4 flex flex-wrap items-end gap-3">
	<div>
		<label for="f-q" class="mb-1 block text-xs font-medium text-slate-500">Buscar</label>
		<input id="f-q" bind:value={q} oninput={filtrar} placeholder="Nombre comercial…"
			class="w-56 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none" />
	</div>
	<div>
		<label for="f-nit" class="mb-1 block text-xs font-medium text-slate-500">NIT/RUT</label>
		<input id="f-nit" bind:value={nit} oninput={filtrar} placeholder="NIT…"
			class="w-40 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none" />
	</div>
	<div>
		<label for="f-estado" class="mb-1 block text-xs font-medium text-slate-500">Estado</label>
		<select id="f-estado" bind:value={estado} onchange={filtrar}
			class="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none">
			<option value="">Todos</option>
			<option value="activo">Activo</option>
			<option value="suspendido">Suspendido</option>
		</select>
	</div>
	<div class="ml-auto flex gap-2">
		<button onclick={exportar}
			class="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">
			<Icon name="download" clase="inline h-4 w-4 align-middle" /> Exportar CSV
		</button>
		<a href="/socios/nuevo"
			class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
			+ Nuevo socio
		</a>
	</div>
</div>

{#if mensaje}
	<p class="mb-4 rounded-lg bg-sky-50 px-4 py-2 text-sm text-sky-700">{mensaje}</p>
{/if}

<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
	<DataTable {columnas} filas={(datos?.items ?? []) as unknown as Record<string, unknown>[]} {cargando}>
		{#snippet celda({ key, fila })}
			{@const s = fila as unknown as SocioListItem}
			{#if key === 'nombre_comercial'}
				<div class="flex items-center gap-3">
					{#if s.logo_url}
						<img src={s.logo_url} alt={s.nombre_comercial} class="h-9 w-9 rounded-lg object-cover border border-slate-200 shadow-xs" />
					{:else}
						<div class="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-xs font-bold text-indigo-600 border border-indigo-100">
							{s.nombre_comercial.slice(0, 2).toUpperCase()}
						</div>
					{/if}
					<a href="/socios/{s.id}" class="font-semibold text-slate-800 hover:text-indigo-600 transition">
						{s.nombre_comercial}
					</a>
				</div>
			{:else if key === 'estado'}
				<Badge texto={s.estado} variante={s.estado === 'activo' ? 'ok' : 'bad'} />
			{:else if key === 'created_at'}
				{formatFechaCorta(s.created_at)}
			{:else}
				{s[key as keyof SocioListItem] ?? '—'}
			{/if}
		{/snippet}
		{#snippet acciones(fila)}
			{@const s = fila as unknown as SocioListItem}
			<a href="/socios/{s.id}" class="mr-2 text-xs font-medium text-slate-600 hover:text-indigo-600">Ver</a>
			{#if s.estado === 'activo'}
				<button onclick={() => (confirmar = { socio: s, accion: 'suspender' })}
					class="mr-2 text-xs font-medium text-red-600 hover:underline">Suspender</button>
			{:else}
				<button onclick={() => (confirmar = { socio: s, accion: 'reactivar' })}
					class="mr-2 text-xs font-medium text-green-600 hover:underline">Reactivar</button>
			{/if}
			<button onclick={() => accionSocio(s, 'forzar-reset')}
				class="mr-2 text-xs font-medium text-amber-600 hover:underline">Forzar reset</button>
			<button onclick={() => accionSocio(s, 'reenviar-onboarding')}
				class="text-xs font-medium text-sky-600 hover:underline">Reenviar alta</button>
		{/snippet}
	</DataTable>
	{#if datos}
		<Pagination total={datos.total} page={datos.page} size={datos.size}
			onchange={(p) => { page = p; cargar(); }} />
	{/if}
</div>

<Modal abierto={confirmar !== null} titulo="Confirmar acción" onclose={() => (confirmar = null)}>
	{#if confirmar}
		<p class="text-sm text-slate-600">
			¿{confirmar.accion === 'suspender' ? 'Suspender' : 'Reactivar'} a
			<strong>{confirmar.socio.nombre_comercial}</strong>?
		</p>
		{#if confirmar.accion === 'suspender'}
			<p class="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
				Esto bloquea el acceso al portal de todos sus usuarios y las pantallas físicas del local.
			</p>
		{/if}
		<div class="mt-5 flex justify-end gap-2">
			<button onclick={() => (confirmar = null)}
				class="rounded-lg border border-slate-300 px-4 py-2 text-sm">Cancelar</button>
			<button onclick={ejecutarEstado}
				class="rounded-lg px-4 py-2 text-sm font-semibold text-white
					{confirmar.accion === 'suspender' ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}">
				Confirmar
			</button>
		</div>
	{/if}
</Modal>
