<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { onMount } from 'svelte';
	import { api, descargarCsv } from '#lib/api/client';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Pagination from '#lib/components/ui/Pagination.svelte';
	import type { Pagina, SocioListItem, TransaccionOut } from '#lib/types';
	import { formatFecha, TIPOS_MOVIMIENTO } from '#lib/utils/format';

	let datos = $state<Pagina<TransaccionOut> | null>(null);
	let socios = $state<SocioListItem[]>([]);
	let cargando = $state(false);
	let f = $state({ desde: '', hasta: '', tenant_id: '', cliente: '', tipo: '' });
	let page = $state(1);

	const columnas = [
		{ key: 'created_at', label: 'Fecha' },
		{ key: 'socio', label: 'Socio' },
		{ key: 'sucursal', label: 'Sucursal' },
		{ key: 'cliente_nombre', label: 'Cliente' },
		{ key: 'tipo', label: 'Tipo' },
		{ key: 'puntos', label: 'Puntos' },
		{ key: 'ejecutado_por', label: 'Ejecutado por' },
		{ key: 'premio', label: 'Premio' }
	];

	function qs() {
		const p = new URLSearchParams({ page: String(page), size: '10' });
		for (const [k, v] of Object.entries(f)) if (v) p.set(k, v);
		return p.toString();
	}

	async function cargar() {
		cargando = true;
		try {
			datos = await api.get(`/admin/transacciones?${qs()}`);
		} finally {
			cargando = false;
		}
	}

	function buscar() { page = 1; cargar(); }
	function exportar() {
		const p = new URLSearchParams({ format: 'csv' });
		for (const [k, v] of Object.entries(f)) if (v) p.set(k, v);
		descargarCsv(`/admin/transacciones?${p}`, 'transacciones.csv');
	}

	onMount(async () => {
		cargar();
		const s = await api.get<Pagina<SocioListItem>>('/admin/socios?size=200');
		socios = s.items;
	});

	const input = 'rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none';
</script>

<div class="mb-4 flex flex-wrap items-end gap-3">
	<div><label for="d" class="mb-1 block text-xs font-medium text-slate-500">Desde</label>
		<input id="d" type="date" bind:value={f.desde} onchange={buscar} class={input} /></div>
	<div><label for="h" class="mb-1 block text-xs font-medium text-slate-500">Hasta</label>
		<input id="h" type="date" bind:value={f.hasta} onchange={buscar} class={input} /></div>
	<div><label for="s" class="mb-1 block text-xs font-medium text-slate-500">Socio</label>
		<select id="s" bind:value={f.tenant_id} onchange={buscar} class={input}>
			<option value="">Todos</option>
			{#each socios as s}<option value={s.id}>{s.nombre_comercial}</option>{/each}
		</select></div>
	<div><label for="t" class="mb-1 block text-xs font-medium text-slate-500">Tipo</label>
		<select id="t" bind:value={f.tipo} onchange={buscar} class={input}>
			<option value="">Todos</option>
			{#each Object.entries(TIPOS_MOVIMIENTO) as [k, v]}<option value={k}>{v}</option>{/each}
		</select></div>
	<div><label for="c" class="mb-1 block text-xs font-medium text-slate-500">Cliente (CI/tel/nombre)</label>
		<input id="c" bind:value={f.cliente} onchange={buscar} placeholder="Buscar…" class={input} /></div>
	<button onclick={exportar} class="ml-auto rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">
		<Icon name="download" clase="inline h-4 w-4 align-middle" /> Exportar CSV
	</button>
</div>

<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
	<DataTable {columnas} filas={(datos?.items ?? []) as unknown as Record<string, unknown>[]} {cargando}>
		{#snippet celda({ key, fila })}
			{@const t = fila as unknown as TransaccionOut}
			{#if key === 'created_at'}{formatFecha(t.created_at)}
			{:else if key === 'tipo'}{TIPOS_MOVIMIENTO[t.tipo] ?? t.tipo}
			{:else if key === 'cliente_nombre'}{t.cliente_nombre} <span class="text-xs text-slate-400">({t.cliente_ci})</span>
			{:else if key === 'puntos'}
				<span class="font-medium {t.puntos >= 0 ? 'text-green-600' : 'text-red-600'}">
					{t.puntos >= 0 ? '+' : ''}{t.puntos}
				</span>
			{:else}{t[key as keyof TransaccionOut] ?? '—'}{/if}
		{/snippet}
	</DataTable>
	{#if datos}
		<Pagination total={datos.total} page={datos.page} size={datos.size}
			onchange={(p) => { page = p; cargar(); }} />
	{/if}
</div>
