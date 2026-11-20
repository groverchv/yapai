<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { onMount } from 'svelte';
	import { api, descargarCsv } from '#lib/api/client';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Pagination from '#lib/components/ui/Pagination.svelte';
	import type { AuditItem, Pagina } from '#lib/types';
	import { formatFecha } from '#lib/utils/format';

	let datos = $state<Pagina<AuditItem> | null>(null);
	let cargando = $state(false);
	let f = $state({ desde: '', hasta: '', accion: '', entidad: '' });
	let page = $state(1);

	const columnas = [
		{ key: 'created_at', label: 'Fecha' },
		{ key: 'actor', label: 'Actor' },
		{ key: 'accion', label: 'Acción' },
		{ key: 'entidad', label: 'Entidad' },
		{ key: 'detalle', label: 'Detalle' },
		{ key: 'registro_hash', label: 'Hash' }
	];

	function qs() {
		const p = new URLSearchParams({ page: String(page), size: '20' });
		for (const [k, v] of Object.entries(f)) if (v) p.set(k, v);
		return p.toString();
	}

	async function cargar() {
		cargando = true;
		try {
			datos = await api.get(`/admin/audit?${qs()}`);
		} finally {
			cargando = false;
		}
	}

	function buscar() { page = 1; cargar(); }
	function exportar() {
		const p = new URLSearchParams({ format: 'csv' });
		for (const [k, v] of Object.entries(f)) if (v) p.set(k, v);
		descargarCsv(`/admin/audit?${p}`, 'audit_log.csv');
	}

	onMount(cargar);

	const input = 'rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none';
</script>

<div class="mb-4 rounded-xl border border-indigo-100 bg-indigo-50/60 px-4 py-3 text-xs text-indigo-800">
	El registro está encadenado criptográficamente (cada fila firma a la anterior).
	La integridad puede verificarse con <code>scripts/verify_audit_chain.py</code>.
</div>

<div class="mb-4 flex flex-wrap items-end gap-3">
	<div><label for="d" class="mb-1 block text-xs font-medium text-slate-500">Desde</label>
		<input id="d" type="date" bind:value={f.desde} onchange={buscar} class={input} /></div>
	<div><label for="h" class="mb-1 block text-xs font-medium text-slate-500">Hasta</label>
		<input id="h" type="date" bind:value={f.hasta} onchange={buscar} class={input} /></div>
	<div><label for="a" class="mb-1 block text-xs font-medium text-slate-500">Acción</label>
		<input id="a" bind:value={f.accion} onchange={buscar} placeholder="login, crear_premio…" class={input} /></div>
	<div><label for="e" class="mb-1 block text-xs font-medium text-slate-500">Entidad</label>
		<input id="e" bind:value={f.entidad} onchange={buscar} placeholder="tenant, premio…" class={input} /></div>
	<button onclick={exportar} class="ml-auto rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">
		<Icon name="download" clase="inline h-4 w-4 align-middle" /> Exportar CSV
	</button>
</div>

<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
	<DataTable {columnas} filas={(datos?.items ?? []) as unknown as Record<string, unknown>[]} {cargando}>
		{#snippet celda({ key, fila })}
			{@const a = fila as unknown as AuditItem}
			{#if key === 'created_at'}{formatFecha(a.created_at)}
			{:else if key === 'actor'}
				{a.actor_email ?? (a.actor_id ? `usuario #${a.actor_id}` : 'sistema')}
			{:else if key === 'entidad'}
				{a.entidad}{a.entidad_id ? ` #${a.entidad_id}` : ''}
			{:else if key === 'detalle'}
				<span class="text-xs text-slate-500">{a.detalle ? JSON.stringify(a.detalle) : '—'}</span>
			{:else if key === 'registro_hash'}
				<code class="text-xs text-slate-400">{(a.registro_hash ?? '').slice(0, 12) || '—'}</code>
			{:else}{a[key as keyof AuditItem] ?? '—'}{/if}
		{/snippet}
	</DataTable>
	{#if datos}
		<Pagination total={datos.total} page={datos.page} size={datos.size}
			onchange={(p) => { page = p; cargar(); }} />
	{/if}
</div>
