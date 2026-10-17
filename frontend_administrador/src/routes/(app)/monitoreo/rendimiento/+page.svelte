<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import KpiCard from '#lib/components/ui/KpiCard.svelte';
	import type { KpisSocio, Pagina, SocioListItem } from '#lib/types';

	let socios = $state<SocioListItem[]>([]);
	let tenantId = $state('');
	let desde = $state('');
	let hasta = $state('');
	let kpis = $state<KpisSocio | null>(null);
	let cargando = $state(false);

	async function cargar() {
		if (!tenantId) { kpis = null; return; }
		cargando = true;
		try {
			const p = new URLSearchParams();
			if (desde) p.set('desde', desde);
			if (hasta) p.set('hasta', hasta);
			kpis = await api.get(`/admin/socios/${tenantId}/kpis?${p}`);
		} finally {
			cargando = false;
		}
	}

	onMount(async () => {
		const s = await api.get<Pagina<SocioListItem>>('/admin/socios?size=200');
		socios = s.items;
		if (socios.length) { tenantId = String(socios[0].id); cargar(); }
	});

	const input = 'rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none';
</script>

<div class="mb-6 flex flex-wrap items-end gap-3">
	<div><label for="s" class="mb-1 block text-xs font-medium text-slate-500">Socio</label>
		<select id="s" bind:value={tenantId} onchange={cargar} class={input}>
			{#each socios as s}<option value={s.id}>{s.nombre_comercial}</option>{/each}
		</select></div>
	<div><label for="d" class="mb-1 block text-xs font-medium text-slate-500">Desde</label>
		<input id="d" type="date" bind:value={desde} onchange={cargar} class={input} /></div>
	<div><label for="h" class="mb-1 block text-xs font-medium text-slate-500">Hasta</label>
		<input id="h" type="date" bind:value={hasta} onchange={cargar} class={input} /></div>
</div>

{#if cargando}
	<p class="text-slate-400">Cargando…</p>
{:else if kpis}
	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
		<KpiCard titulo="Clientes nuevos captados" valor={kpis.clientes_nuevos} color="indigo" />
		<KpiCard titulo="Puntos emitidos" valor={kpis.puntos_emitidos} color="green" />
		<KpiCard titulo="Puntos consumidos" valor={kpis.puntos_consumidos} color="amber" />
		<KpiCard titulo="Canjes exitosos" valor={kpis.canjes_exitosos} color="sky" />
	</div>
{:else}
	<p class="text-slate-400">Selecciona un socio para ver sus métricas.</p>
{/if}
