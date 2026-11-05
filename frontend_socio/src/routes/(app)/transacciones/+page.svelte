<script lang="ts">
	import { onMount } from 'svelte';
	import { api, descargarCsv } from '#lib/api/client';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Pagination from '#lib/components/ui/Pagination.svelte';
	import { formatFecha, TIPOS_MOVIMIENTO } from '#lib/utils/format';
	import type { OpcionesFiltro, Pagina, Transaccion } from '#lib/types';

	let datos = $state<Pagina<Transaccion> | null>(null);
	let opciones = $state<OpcionesFiltro | null>(null);
	let cargando = $state(false);
	let error = $state('');

	let desde = $state('');
	let hasta = $state('');
	let sucursalId = $state('');
	let cajeroId = $state('');
	let cliente = $state('');
	let tipo = $state('');
	let page = $state(1);

	const columnas = [
		{ key: 'created_at', label: 'Fecha' },
		{ key: 'sucursal', label: 'Sucursal' },
		{ key: 'cliente_nombre', label: 'Cliente' },
		{ key: 'tipo', label: 'Acción' },
		{ key: 'puntos', label: 'Puntos' },
		{ key: 'ejecutado_por', label: 'Cajero' },
		{ key: 'premio', label: 'Premio' }
	];

	function queryString(p: number): string {
		const params = new URLSearchParams();
		if (desde) params.set('desde', desde);
		if (hasta) params.set('hasta', hasta);
		if (sucursalId) params.set('sucursal_id', sucursalId);
		if (cajeroId) params.set('cajero_id', cajeroId);
		if (cliente) params.set('cliente', cliente);
		if (tipo) params.set('tipo', tipo);
		params.set('page', String(p));
		params.set('size', '10');
		return params.toString();
	}

	async function cargar(p = 1) {
		cargando = true;
		error = '';
		page = p;
		try {
			datos = await api.get<Pagina<Transaccion>>(`/socio/transacciones?${queryString(p)}`);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cargar';
		} finally {
			cargando = false;
		}
	}

	function exportar() {
		descargarCsv(`/socio/transacciones?${queryString(1)}&format=csv`, 'transacciones.csv')
			.catch((e) => (error = e instanceof Error ? e.message : 'Error al exportar'));
	}

	onMount(async () => {
		cargar();
		opciones = await api.get<OpcionesFiltro>('/socio/transacciones/filtros').catch(() => null);
	});
</script>

<div class="space-y-4">
	<div class="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4">
		<div>
			<label for="fd" class="mb-1 block text-xs font-medium text-slate-500">Desde</label>
			<input id="fd" type="date" bind:value={desde} class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
		</div>
		<div>
			<label for="fh" class="mb-1 block text-xs font-medium text-slate-500">Hasta</label>
			<input id="fh" type="date" bind:value={hasta} class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
		</div>
		<div>
			<label for="fs" class="mb-1 block text-xs font-medium text-slate-500">Sucursal</label>
			<select id="fs" bind:value={sucursalId} class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm">
				<option value="">Todas</option>
				{#each opciones?.sucursales ?? [] as s}
					<option value={s.id}>{s.nombre}</option>
				{/each}
			</select>
		</div>
		<div>
			<label for="fc" class="mb-1 block text-xs font-medium text-slate-500">Cajero</label>
			<select id="fc" bind:value={cajeroId} class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm">
				<option value="">Todos</option>
				{#each opciones?.cajeros ?? [] as c}
					<option value={c.id}>{c.nombre}</option>
				{/each}
			</select>
		</div>
		<div>
			<label for="ft" class="mb-1 block text-xs font-medium text-slate-500">Acción</label>
			<select id="ft" bind:value={tipo} class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm">
				<option value="">Todas</option>
				{#each Object.entries(TIPOS_MOVIMIENTO) as [v, label]}
					<option value={v}>{label}</option>
				{/each}
			</select>
		</div>
		<div>
			<label for="fq" class="mb-1 block text-xs font-medium text-slate-500">Cliente (nombre/CI)</label>
			<input id="fq" type="text" bind:value={cliente} placeholder="Buscar…"
				class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
		</div>
		<button onclick={() => cargar(1)}
			class="rounded-lg bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-emerald-700">
			Filtrar
		</button>
		<button onclick={exportar}
			class="rounded-lg border border-slate-300 px-4 py-1.5 text-sm text-slate-600 hover:bg-slate-50">
			Exportar CSV
		</button>
	</div>

	{#if error}
		<p class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
	{/if}

	<div class="rounded-xl border border-slate-200 bg-white">
		<DataTable {columnas} filas={(datos?.items ?? []) as unknown as Record<string, unknown>[]} {cargando}>
			{#snippet celda({ key, fila })}
				{@const t = fila as unknown as Transaccion}
				{#if key === 'created_at'}
					{formatFecha(t.created_at)}
				{:else if key === 'tipo'}
					{TIPOS_MOVIMIENTO[t.tipo] ?? t.tipo}
				{:else if key === 'puntos'}
					<span class={t.puntos >= 0 ? 'font-semibold text-green-600' : 'font-semibold text-red-600'}>
						{t.puntos > 0 ? `+${t.puntos}` : t.puntos}
					</span>
				{:else if key === 'cliente_nombre'}
					{t.cliente_nombre} <span class="text-xs text-slate-500">({t.cliente_ci})</span>
				{:else}
					{t[key as keyof Transaccion] ?? '—'}
				{/if}
			{/snippet}
		</DataTable>
		{#if datos}
			<Pagination total={datos.total} {page} size={datos.size} onchange={cargar} />
		{/if}
	</div>
</div>
