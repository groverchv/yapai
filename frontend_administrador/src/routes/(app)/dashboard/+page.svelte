<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import KpiCard from '#lib/components/ui/KpiCard.svelte';
	import type { DashboardOut, TransaccionOut } from '#lib/types';
	import { formatDinero, formatFecha, TIPOS_MOVIMIENTO } from '#lib/utils/format';

	let data = $state<DashboardOut | null>(null);
	let error = $state('');

	onMount(async () => {
		try {
			data = await api.get<DashboardOut>('/admin/dashboard');
		} catch {
			error = 'No se pudo cargar el dashboard';
		}
	});

	let maxDia = $derived(Math.max(1, ...(data?.transacciones_30d.map((d) => d.total) ?? [1])));

	const columnas = [
		{ key: 'created_at', label: 'Fecha' },
		{ key: 'socio', label: 'Socio' },
		{ key: 'cliente_nombre', label: 'Cliente' },
		{ key: 'tipo', label: 'Tipo' },
		{ key: 'puntos', label: 'Puntos' }
	];

	function fila(t: TransaccionOut) {
		return { ...t } as unknown as Record<string, unknown>;
	}
</script>

{#if error}
	<p class="rounded-lg bg-red-50 px-4 py-3 text-red-600">{error}</p>
{:else if !data}
	<p class="text-slate-400">Cargando…</p>
{:else}
	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
		<KpiCard titulo="Socios activos" valor={data.kpis.socios_activos}
			subtitulo="{data.kpis.socios_suspendidos} suspendido(s)" color="indigo" />
		<KpiCard titulo="Transacciones hoy" valor={data.kpis.transacciones_hoy} color="green" />
		<KpiCard titulo="Liquidaciones pendientes" valor={data.kpis.liquidaciones_pendientes}
			subtitulo={formatDinero(data.kpis.monto_pendiente)} color="amber" />
		<KpiCard titulo="Clientes totales" valor={data.kpis.clientes_totales} color="sky" />
		<KpiCard titulo="T. medio 1er giro"
			valor={data.kpis.ttfs_medio_h !== null ? `${data.kpis.ttfs_medio_h}h` : '—'}
			subtitulo="activación de socios" color="green" />
		<KpiCard titulo="Monto pendiente" valor={formatDinero(data.kpis.monto_pendiente)} color="red" />
	</div>

	<div class="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
		<div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2">
			<h2 class="mb-4 font-semibold text-slate-700">Transacciones — últimos 30 días</h2>
			<div class="flex h-40 items-end gap-1">
				{#each data.transacciones_30d as d}
					<div class="group relative flex-1 rounded-t bg-indigo-200 hover:bg-indigo-400"
						style="height: {Math.max(2, (d.total / maxDia) * 100)}%">
						<span class="absolute -top-7 left-1/2 hidden -translate-x-1/2 rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-white group-hover:block whitespace-nowrap">
							{d.fecha.slice(5)}: {d.total}
						</span>
					</div>
				{/each}
			</div>
		</div>

		<div class="rounded-xl border border-slate-200 bg-white shadow-sm xl:col-span-1">
			<h2 class="border-b border-slate-200 px-5 py-4 font-semibold text-slate-700">Últimas transacciones</h2>
			<DataTable {columnas} filas={data.ultimas_transacciones.map(fila)}>
				{#snippet celda({ key, fila: f })}
					{@const t = f as unknown as TransaccionOut}
					{#if key === 'created_at'}{formatFecha(t.created_at)}
					{:else if key === 'tipo'}{TIPOS_MOVIMIENTO[t.tipo] ?? t.tipo}
					{:else if key === 'puntos'}
						<span class={t.puntos >= 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
							{t.puntos >= 0 ? '+' : ''}{t.puntos}
						</span>
					{:else}{t[key as keyof TransaccionOut] ?? '—'}{/if}
				{/snippet}
			</DataTable>
		</div>
	</div>
{/if}
