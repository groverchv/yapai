<script lang="ts">
	import { onMount } from 'svelte';
	import { api, ApiError } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import Pagination from '#lib/components/ui/Pagination.svelte';
	import type { LiquidacionOut, Pagina } from '#lib/types';
	import { formatDinero, formatFecha } from '#lib/utils/format';

	let datos = $state<Pagina<LiquidacionOut> | null>(null);
	let cargando = $state(false);
	let periodo = $state(new Date().toISOString().slice(0, 7));
	let estado = $state('');
	let page = $state(1);
	let mensaje = $state('');
	let confirmar = $state<LiquidacionOut | null>(null);

	const columnas = [
		{ key: 'socio', label: 'Socio' },
		{ key: 'periodo', label: 'Periodo' },
		{ key: 'clientes_nuevos', label: 'Clientes nuevos' },
		{ key: 'canjes_validados', label: 'Canjes' },
		{ key: 'desglose', label: 'Cálculo' },
		{ key: 'monto_total', label: 'Monto' },
		{ key: 'estado', label: 'Estado' },
		{ key: 'aprobada_por', label: 'Aprobada por' }
	];

	async function cargar() {
		cargando = true;
		try {
			const p = new URLSearchParams({ page: String(page), size: '10' });
			if (periodo) p.set('periodo', periodo);
			if (estado) p.set('estado', estado);
			datos = await api.get(`/admin/liquidaciones?${p}`);
		} finally {
			cargando = false;
		}
	}

	async function generar() {
		mensaje = '';
		try {
			const r = await api.post<{ generadas: number; actualizadas: number; omitidas_pagadas: number }>(
				'/admin/liquidaciones/generar', { periodo }
			);
			mensaje = `Generadas: ${r.generadas} · Actualizadas: ${r.actualizadas} · Omitidas (ya pagadas): ${r.omitidas_pagadas}`;
			page = 1;
			cargar();
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error al generar';
		}
	}

	async function pagar() {
		if (!confirmar) return;
		try {
			await api.post(`/admin/liquidaciones/${confirmar.id}/pagar`);
			mensaje = `Liquidación #${confirmar.id} marcada como pagada`;
			confirmar = null;
			cargar();
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error';
		}
	}

	onMount(cargar);
	const input = 'rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none';
</script>

<div class="mb-4 flex flex-wrap items-end gap-3">
	<div><label for="p" class="mb-1 block text-xs font-medium text-slate-500">Periodo</label>
		<input id="p" type="month" bind:value={periodo} onchange={() => { page = 1; cargar(); }} class={input} /></div>
	<div><label for="e" class="mb-1 block text-xs font-medium text-slate-500">Estado</label>
		<select id="e" bind:value={estado} onchange={() => { page = 1; cargar(); }} class={input}>
			<option value="">Todos</option>
			<option value="pendiente">Pendiente</option>
			<option value="pagada">Pagada</option>
		</select></div>
	<button onclick={generar}
		class="ml-auto rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
		Generar liquidaciones del periodo
	</button>
</div>

{#if mensaje}
	<p class="mb-4 rounded-lg bg-sky-50 px-4 py-2 text-sm text-sky-700">{mensaje}</p>
{/if}

<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
	<DataTable {columnas} filas={(datos?.items ?? []) as unknown as Record<string, unknown>[]} {cargando}>
		{#snippet celda({ key, fila })}
			{@const l = fila as unknown as LiquidacionOut}
			{#if key === 'desglose'}
				<span class="text-xs text-slate-500">
					{l.clientes_nuevos}×{formatDinero(l.costo_registro_unit, l.moneda)} + {l.canjes_validados}×{formatDinero(l.costo_canje_unit, l.moneda)}
				</span>
			{:else if key === 'monto_total'}
				<strong>{formatDinero(l.monto_total, l.moneda)}</strong>
			{:else if key === 'estado'}
				<Badge texto={l.estado} variante={l.estado === 'pagada' ? 'ok' : 'warn'} />
			{:else if key === 'aprobada_por'}
				{l.aprobada_por ?? '—'}{#if l.pagada_en} <span class="block text-xs text-slate-400">{formatFecha(l.pagada_en)}</span>{/if}
			{:else}{l[key as keyof LiquidacionOut]}{/if}
		{/snippet}
		{#snippet acciones(fila)}
			{@const l = fila as unknown as LiquidacionOut}
			{#if l.estado === 'pendiente'}
				<button onclick={() => (confirmar = l)}
					class="text-xs font-medium text-green-600 hover:underline">Marcar pagada</button>
			{:else}
				<span class="text-xs text-slate-300">—</span>
			{/if}
		{/snippet}
	</DataTable>
	{#if datos}
		<Pagination total={datos.total} page={datos.page} size={datos.size}
			onchange={(p) => { page = p; cargar(); }} />
	{/if}
</div>

<Modal abierto={confirmar !== null} titulo="Marcar liquidación como pagada" onclose={() => (confirmar = null)}>
	{#if confirmar}
		<p class="text-sm text-slate-600">
			¿Confirmar el pago de <strong>{formatDinero(confirmar.monto_total, confirmar.moneda)}</strong> a
			<strong>{confirmar.socio}</strong> ({confirmar.periodo})?
		</p>
		<p class="mt-2 text-xs text-slate-500">Tu usuario quedará registrado como aprobador.</p>
		<div class="mt-5 flex justify-end gap-2">
			<button onclick={() => (confirmar = null)} class="rounded-lg border border-slate-300 px-4 py-2 text-sm">Cancelar</button>
			<button onclick={pagar} class="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700">
				Confirmar pago
			</button>
		</div>
	{/if}
</Modal>
