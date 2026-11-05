<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import KpiCard from '#lib/components/ui/KpiCard.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import type { KpisSocio, Pagina, SocioListItem } from '#lib/types';

	let socios = $state<SocioListItem[]>([]);
	let tenantId = $state('');
	let desde = $state('');
	let hasta = $state('');
	let kpis = $state<KpisSocio | null>(null);
	let cargando = $state(false);

	let socioSeleccionado = $derived(
		socios.find((s) => String(s.id) === tenantId) ?? null
	);

	async function cargar() {
		if (!tenantId) { kpis = null; return; }
		cargando = true;
		try {
			const p = new URLSearchParams();
			if (desde) p.set('desde', desde);
			if (hasta) p.set('hasta', hasta);
			kpis = await api.get<KpisSocio>(`/admin/socios/${tenantId}/kpis?${p}`);
		} finally {
			cargando = false;
		}
	}

	onMount(async () => {
		const s = await api.get<Pagina<SocioListItem>>('/admin/socios?size=200');
		socios = s.items;
		if (socios.length) {
			tenantId = String(socios[0].id);
			cargar();
		}
	});

	let maxDia = $derived(
		Math.max(1, ...(kpis?.serie_diaria?.map((d) => d.total) ?? [1]))
	);

	let tasaConversion = $derived(
		kpis && kpis.puntos_emitidos > 0
			? Math.min(100, Math.round((kpis.puntos_consumidos / kpis.puntos_emitidos) * 100))
			: 0
	);

	const input = 'rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none bg-white';
</script>

<div class="space-y-6">
	<!-- Encabezado con selector de socio y rango temporal -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight text-slate-800">Rendimiento Operativo por Socio</h1>
			<p class="text-sm text-slate-500">Métricas analíticas, captación de clientes y fidelización de cada comercio.</p>
		</div>
		{#if socioSeleccionado}
			<a
				href="/socios/{socioSeleccionado.id}"
				class="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50"
			>
				<span>Ver ficha del socio</span>
				<Icon name="arrow-right" clase="h-3.5 w-3.5" />
			</a>
		{/if}
	</div>

	<!-- Barra de filtros -->
	<div class="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
		<div class="min-w-64">
			<label for="s" class="mb-1 block text-xs font-semibold text-slate-600">Socio / Comercio</label>
			<select id="s" bind:value={tenantId} onchange={cargar} class="{input} w-full">
				{#each socios as s}
					<option value={String(s.id)}>{s.nombre_comercial} (NIT: {s.nit_rut})</option>
				{/each}
			</select>
		</div>
		<div>
			<label for="d" class="mb-1 block text-xs font-semibold text-slate-600">Fecha desde</label>
			<input id="d" type="date" bind:value={desde} onchange={cargar} class={input} />
		</div>
		<div>
			<label for="h" class="mb-1 block text-xs font-semibold text-slate-600">Fecha hasta</label>
			<input id="h" type="date" bind:value={hasta} onchange={cargar} class={input} />
		</div>
		{#if desde || hasta}
			<button
				type="button"
				onclick={() => { desde = ''; hasta = ''; cargar(); }}
				class="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
			>
				Limpiar fechas
			</button>
		{/if}
	</div>

	{#if cargando}
		<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-6">
			{#each Array(6) as _}
				<div class="h-28 animate-pulse rounded-xl border border-slate-200 bg-white p-5 shadow-xs"></div>
			{/each}
		</div>
	{:else if kpis}
		<!-- 6 KPIs simétricos y completos -->
		<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
			<KpiCard
				titulo="Clientes captados"
				valor={kpis.clientes_nuevos}
				subtitulo="registrados en periodo"
				color="indigo"
				icono="users"
			/>
			<KpiCard
				titulo="Total operaciones"
				valor={kpis.transacciones_totales ?? (kpis.clientes_nuevos + kpis.canjes_exitosos)}
				subtitulo="movimientos registrados"
				color="sky"
				icono="activity"
			/>
			<KpiCard
				titulo="Puntos emitidos"
				valor={kpis.puntos_emitidos.toLocaleString()}
				subtitulo="ruletas y registros"
				color="green"
				icono="sparkles"
			/>
			<KpiCard
				titulo="Puntos consumidos"
				valor={kpis.puntos_consumidos.toLocaleString()}
				subtitulo="redimidos en premios"
				color="amber"
				icono="gift"
			/>
			<KpiCard
				titulo="Canjes exitosos"
				valor={kpis.canjes_exitosos}
				subtitulo="premios entregados"
				color="emerald"
				icono="trophy"
			/>
			<KpiCard
				titulo="Tiempo 1er giro"
				valor={kpis.horas_a_primer_giro !== null ? `${kpis.horas_a_primer_giro}h` : '—'}
				subtitulo="velocidad de activación"
				color="purple"
				icono="clock"
			/>
		</div>

		<!-- Sección analítica: Gráfico de actividad temporal + Resumen de Fidelización -->
		<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
			<!-- Gráfico de actividad -->
			<div class="rounded-xl border border-slate-200 bg-white p-5 shadow-xs lg:col-span-2">
				<div class="flex items-center justify-between border-b border-slate-100 pb-3">
					<div>
						<h2 class="font-semibold text-slate-800 flex items-center gap-2">
							<Icon name="trending-up" clase="h-4 w-4 text-indigo-600" />
							Historial de Actividad del Socio
						</h2>
						<p class="text-xs text-slate-500 mt-0.5">Operaciones registradas día a día</p>
					</div>
					{#if socioSeleccionado?.logo_url}
						<img src={socioSeleccionado.logo_url} alt="" class="h-8 w-8 rounded-lg object-cover border border-slate-200" />
					{/if}
				</div>

				{#if !kpis.serie_diaria || kpis.serie_diaria.length === 0}
					<p class="py-12 text-center text-xs text-slate-500">Sin datos de actividad para el rango seleccionado.</p>
				{:else}
					<div class="mt-6 flex h-44 items-end gap-1.5 pt-4">
						{#each kpis.serie_diaria as d}
							{@const pct = Math.max(6, (d.total / maxDia) * 100)}
							<div class="group relative flex-1 h-full flex flex-col justify-end items-center">
								<!-- Tooltip -->
								<div class="absolute -top-9 hidden flex-col items-center group-hover:flex z-20 pointer-events-none">
									<span class="rounded-md bg-slate-900 px-2 py-0.5 text-[11px] font-semibold text-white whitespace-nowrap shadow-md">
										{d.fecha}: {d.total} tx
									</span>
									<div class="h-1 w-1 rotate-45 bg-slate-900 -mt-0.5"></div>
								</div>
								<!-- Barra -->
								<div
									class="w-full rounded-t-md transition-all duration-300 bg-indigo-500 group-hover:bg-indigo-600"
									style="height: {pct}%"
								></div>
								<span class="mt-1 text-[9px] text-slate-500 truncate w-full text-center">
									{d.fecha.slice(8)}
								</span>
							</div>
						{/each}
					</div>
					<div class="mt-3 flex items-center justify-between border-t border-slate-100 pt-2 text-xs text-slate-500">
						<span>{kpis.serie_diaria[0]?.fecha ?? ''}</span>
						<span>{kpis.serie_diaria[kpis.serie_diaria.length - 1]?.fecha ?? ''}</span>
					</div>
				{/if}
			</div>

			<!-- Resumen de Fidelización y Balance -->
			<div class="rounded-xl border border-slate-200 bg-white p-5 shadow-xs space-y-4 flex flex-col justify-between">
				<div>
					<div class="border-b border-slate-100 pb-3">
						<h2 class="font-semibold text-slate-800 flex items-center gap-2">
							<Icon name="target" clase="h-4 w-4 text-emerald-600" />
							Salud de Fidelización
						</h2>
						<p class="text-xs text-slate-500 mt-0.5">Retención y circulación de puntos</p>
					</div>

					<div class="mt-4 space-y-4">
						<div>
							<div class="flex items-center justify-between text-xs font-medium">
								<span class="text-slate-600">Tasa de redención de puntos</span>
								<span class="font-bold text-slate-800">{tasaConversion}%</span>
							</div>
							<div class="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-100">
								<div class="h-full rounded-full bg-emerald-500" style="width: {tasaConversion}%"></div>
							</div>
							<p class="mt-1 text-[11px] text-slate-500">Puntos canjeados en relación con puntos emitidos.</p>
						</div>

						<div class="rounded-lg bg-slate-50 p-3 space-y-2 text-xs">
							<div class="flex items-center justify-between">
								<span class="text-slate-500">Puntos en circulación:</span>
								<span class="font-bold text-slate-700">
									{Math.max(0, kpis.puntos_emitidos - kpis.puntos_consumidos).toLocaleString()} pts
								</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-slate-500">Clientes únicos atendidos:</span>
								<span class="font-bold text-slate-700">{kpis.total_clientes_unicos ?? '—'}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-slate-500">Promedio puntos por canje:</span>
								<span class="font-bold text-slate-700">
									{kpis.canjes_exitosos > 0 ? Math.round(kpis.puntos_consumidos / kpis.canjes_exitosos) : 0} pts
								</span>
							</div>
						</div>
					</div>
				</div>

				<a
					href="/monitoreo/transacciones?tenant_id={tenantId}"
					class="block text-center rounded-lg bg-indigo-50 px-3 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 transition"
				>
					Ver transacciones de este socio →
				</a>
			</div>
		</div>
	{:else}
		<p class="text-slate-500">Selecciona un socio para ver sus métricas.</p>
	{/if}
</div>
