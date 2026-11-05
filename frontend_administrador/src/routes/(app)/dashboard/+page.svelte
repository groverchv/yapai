<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import KpiCard from '#lib/components/ui/KpiCard.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import type { DashboardOut, TransaccionOut } from '#lib/types';
	import { formatDinero, formatFecha, TIPOS_MOVIMIENTO } from '#lib/utils/format';

	let data = $state<DashboardOut | null>(null);
	let error = $state('');
	let cargando = $state(true);

	// Filtro de rango de días para el gráfico
	let rangoDias = $state<7 | 14 | 30>(30);

	async function cargarDashboard() {
		cargando = true;
		try {
			data = await api.get<DashboardOut>('/admin/dashboard');
			error = '';
		} catch {
			error = 'No se pudo cargar la información del dashboard';
		} finally {
			cargando = false;
		}
	}

	onMount(() => {
		cargarDashboard();
	});

	// Filtrado reactivo de días según selección
	let serieFiltrada = $derived(
		data?.transacciones_30d.slice(-rangoDias) ?? []
	);

	let totalPeriodo = $derived(
		serieFiltrada.reduce((acc, d) => acc + d.total, 0)
	);

	let promedioPeriodo = $derived(
		serieFiltrada.length > 0 ? Math.round(totalPeriodo / serieFiltrada.length) : 0
	);

	let maxDia = $derived(Math.max(1, ...(serieFiltrada.map((d) => d.total) ?? [1])));

	const columnas = [
		{ key: 'created_at', label: 'Fecha / Hora' },
		{ key: 'socio', label: 'Socio' },
		{ key: 'cliente_nombre', label: 'Cliente' },
		{ key: 'tipo', label: 'Tipo de Operación' },
		{ key: 'puntos', label: 'Puntos' }
	];

	function fila(t: TransaccionOut) {
		return { ...t } as unknown as Record<string, unknown>;
	}

	const coloresTipos: Record<string, { bg: string; text: string; dot: string }> = {
		registro: { bg: 'bg-blue-50', text: 'text-blue-700', dot: 'bg-blue-500' },
		ruleta: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500' },
		bonus_manual: { bg: 'bg-purple-50', text: 'text-purple-700', dot: 'bg-purple-500' },
		canje: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500' },
		congelar: { bg: 'bg-slate-100', text: 'text-slate-700', dot: 'bg-slate-500' },
		liberar: { bg: 'bg-teal-50', text: 'text-teal-700', dot: 'bg-teal-500' },
		anulacion: { bg: 'bg-rose-50', text: 'text-rose-700', dot: 'bg-rose-500' }
	};
</script>

<div class="space-y-6">
	<!-- Encabezado con bienvenida y acciones rápidas -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight text-slate-800">Panel de Control General</h1>
			<p class="text-sm text-slate-500">Supervisión en tiempo real de socios, clientes, transacciones y facturación SaaS.</p>
		</div>
		<div class="flex items-center gap-2">
			<button
				onclick={cargarDashboard}
				disabled={cargando}
				class="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
				title="Actualizar datos"
			>
				<Icon name="activity" clase="h-4 w-4 text-slate-500 {cargando ? 'animate-spin' : ''}" />
				<span>Actualizar</span>
			</button>
			<a
				href="/socios/nuevo"
				class="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700"
			>
				<Icon name="plus" clase="h-4 w-4" />
				<span>Nuevo socio</span>
			</a>
		</div>
	</div>

	{#if error}
		<div class="flex items-center justify-between rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
			<div class="flex items-center gap-2">
				<Icon name="alert-triangle" clase="h-5 w-5 text-red-500" />
				<p class="text-sm font-medium">{error}</p>
			</div>
			<button onclick={cargarDashboard} class="text-xs font-semibold underline hover:text-red-900">
				Reintentar
			</button>
		</div>
	{:else if !data}
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
			{#each Array(6) as _}
				<div class="h-28 animate-pulse rounded-xl border border-slate-200 bg-white p-5 shadow-sm"></div>
			{/each}
		</div>
	{:else}
		<!-- Cuadrícula simétrica de 6 KPIs clave -->
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
			<KpiCard
				titulo="Socios activos"
				valor={data.kpis.socios_activos}
				subtitulo="{data.kpis.socios_suspendidos} suspendido(s)"
				color="indigo"
				icono="building"
				href="/socios"
			/>
			<KpiCard
				titulo="Transacciones hoy"
				valor={data.kpis.transacciones_hoy}
				subtitulo="movimientos totales"
				color="emerald"
				icono="trending-up"
				href="/monitoreo/transacciones"
			/>
			<KpiCard
				titulo="Clientes fidelizados"
				valor={data.kpis.clientes_totales}
				subtitulo="registrados en la red"
				color="sky"
				icono="users"
			/>
			<KpiCard
				titulo="T. activación (1er giro)"
				valor={data.kpis.ttfs_medio_h !== null ? `${data.kpis.ttfs_medio_h}h` : '—'}
				subtitulo="promedio nuevos socios"
				color="purple"
				icono="clock"
				href="/monitoreo/rendimiento"
			/>
			<KpiCard
				titulo="Liquidaciones pend."
				valor={data.kpis.liquidaciones_pendientes}
				subtitulo={formatDinero(data.kpis.monto_pendiente)}
				color="amber"
				icono="banknote"
				href="/liquidaciones"
			/>
			<KpiCard
				titulo="Facturación SaaS pend."
				valor={data.kpis.facturas_pendientes}
				subtitulo={formatDinero(data.kpis.monto_facturacion_pendiente)}
				color="red"
				icono="receipt"
				href="/facturacion"
			/>
		</div>

		<!-- Sección Intermedia: Gráfico de Tendencia con Filtros + Desglose de Tipos de Operación -->
		<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
			<!-- Gráfico de Transacciones -->
			<div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
				<div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
					<div>
						<h2 class="font-semibold text-slate-800 flex items-center gap-2">
							<Icon name="trending-up" clase="h-4 w-4 text-indigo-600" />
							Volumen Transaccional
						</h2>
						<p class="text-xs text-slate-400 mt-0.5">
							{totalPeriodo} transacciones en el periodo • Promedio diario: {promedioPeriodo}
						</p>
					</div>

					<div class="flex items-center gap-1 rounded-lg bg-slate-100 p-1 text-xs">
						<button
							onclick={() => (rangoDias = 7)}
							class="rounded-md px-2.5 py-1 font-medium transition {rangoDias === 7 ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'}"
						>
							7 días
						</button>
						<button
							onclick={() => (rangoDias = 14)}
							class="rounded-md px-2.5 py-1 font-medium transition {rangoDias === 14 ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'}"
						>
							14 días
						</button>
						<button
							onclick={() => (rangoDias = 30)}
							class="rounded-md px-2.5 py-1 font-medium transition {rangoDias === 30 ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'}"
						>
							30 días
						</button>
					</div>
				</div>

				<!-- Visualización de Barras con escala y tooltips -->
				<div class="mt-6 flex h-48 items-end gap-1.5 pt-4">
					{#each serieFiltrada as d}
						{@const pct = Math.max(4, (d.total / maxDia) * 100)}
						<div class="group relative flex-1 h-full flex flex-col justify-end items-center">
							<!-- Tooltip flotante al pasar el mouse -->
							<div class="absolute -top-10 hidden flex-col items-center group-hover:flex z-20 pointer-events-none">
								<span class="rounded-md bg-slate-900 px-2 py-1 text-[11px] font-semibold text-white whitespace-nowrap shadow-lg">
									{d.fecha}: {d.total} tx
								</span>
								<div class="h-1.5 w-1.5 rotate-45 bg-slate-900 -mt-1"></div>
							</div>

							<!-- Barra -->
							<div
								class="w-full rounded-t-md transition-all duration-300 {d.total > 0 ? 'bg-indigo-500 group-hover:bg-indigo-600' : 'bg-slate-100'}"
								style="height: {pct}%"
							></div>
							
							<!-- Etiqueta de día si hay espacio -->
							{#if rangoDias <= 14}
								<span class="mt-1 text-[9px] text-slate-400 group-hover:text-slate-700 truncate w-full text-center">
									{d.fecha.slice(8)}
								</span>
							{/if}
						</div>
					{/each}
				</div>

				<div class="mt-3 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-400">
					<span>{serieFiltrada[0]?.fecha ?? ''}</span>
					<span class="flex items-center gap-1.5">
						<span class="h-2 w-2 rounded-full bg-indigo-500"></span>
						Días con transacciones
					</span>
					<span>{serieFiltrada[serieFiltrada.length - 1]?.fecha ?? ''}</span>
				</div>
			</div>

			<!-- Desglose por tipo de operación -->
			<div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
				<div class="border-b border-slate-100 pb-4">
					<h2 class="font-semibold text-slate-800 flex items-center gap-2">
						<Icon name="chart-pie" clase="h-4 w-4 text-emerald-600" />
						Distribución de Actividad
					</h2>
					<p class="text-xs text-slate-400 mt-0.5">Operaciones registradas en los últimos 30 días</p>
				</div>

				<div class="mt-4 space-y-3.5">
					{#if data.distribucion_tipos.length === 0}
						<p class="py-8 text-center text-xs text-slate-400">Sin movimientos registrados recientemente</p>
					{:else}
						{#each data.distribucion_tipos as item}
							{@const conf = coloresTipos[item.tipo] ?? { bg: 'bg-slate-50', text: 'text-slate-700', dot: 'bg-slate-400' }}
							<div>
								<div class="flex items-center justify-between text-xs font-medium">
									<span class="flex items-center gap-1.5 text-slate-700">
										<span class="h-2 w-2 rounded-full {conf.dot}"></span>
										{TIPOS_MOVIMIENTO[item.tipo] ?? item.tipo}
									</span>
									<span class="text-slate-500">
										<strong class="text-slate-800">{item.cantidad}</strong> ({item.porcentaje}%)
									</span>
								</div>
								<div class="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-100">
									<div class="h-full rounded-full {conf.dot}" style="width: {item.porcentaje}%"></div>
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>
		</div>

		<!-- Sección Inferior: Top Socios Más Activos + Tabla de Últimas Transacciones -->
		<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
			<!-- Top Socios -->
			<div class="rounded-xl border border-slate-200 bg-white shadow-sm lg:col-span-1 flex flex-col">
				<div class="border-b border-slate-200 px-5 py-4 flex items-center justify-between">
					<div>
						<h2 class="font-semibold text-slate-800 flex items-center gap-2">
							<Icon name="trophy" clase="h-4 w-4 text-amber-500" />
							Socios Más Activos
						</h2>
						<p class="text-xs text-slate-400 mt-0.5">Comercios líderes por volumen de transacciones</p>
					</div>
					<a href="/socios" class="text-xs font-medium text-indigo-600 hover:text-indigo-800">Ver todos →</a>
				</div>

				<div class="divide-y divide-slate-100 p-3 flex-1">
					{#if data.top_socios.length === 0}
						<p class="py-8 text-center text-xs text-slate-400">No hay socios con actividad aún</p>
					{:else}
						{#each data.top_socios as s, idx}
							<div class="flex items-center justify-between p-2.5 rounded-lg hover:bg-slate-50 transition">
								<div class="flex items-center gap-3">
									<span class="flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold {idx === 0 ? 'bg-amber-100 text-amber-800' : idx === 1 ? 'bg-slate-200 text-slate-700' : 'bg-orange-100 text-orange-800'}">
										{idx + 1}
									</span>
									<div>
										<a href="/socios/{s.id}" class="text-sm font-semibold text-slate-800 hover:text-indigo-600">
											{s.nombre}
										</a>
										<p class="text-[11px] text-slate-400">
											{s.clientes} clientes registrados
										</p>
									</div>
								</div>
								<div class="text-right">
									<span class="inline-flex items-center rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-bold text-indigo-700">
										{s.transacciones} tx
									</span>
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>

			<!-- Últimas Transacciones en Tiempo Real -->
			<div class="rounded-xl border border-slate-200 bg-white shadow-sm lg:col-span-2">
				<div class="border-b border-slate-200 px-5 py-4 flex items-center justify-between">
					<div>
						<h2 class="font-semibold text-slate-800 flex items-center gap-2">
							<Icon name="trending-up" clase="h-4 w-4 text-indigo-600" />
							Últimas Transacciones en Vivo
						</h2>
						<p class="text-xs text-slate-400 mt-0.5">Movimientos registrados en comercios afiliados</p>
					</div>
					<a href="/monitoreo/transacciones" class="text-xs font-medium text-indigo-600 hover:text-indigo-800">
						Ver monitor completo →
					</a>
				</div>

				<DataTable {columnas} filas={data.ultimas_transacciones.map(fila)}>
					{#snippet celda({ key, fila: f })}
						{@const t = f as unknown as TransaccionOut}
						{#if key === 'created_at'}
							<span class="text-xs text-slate-600">{formatFecha(t.created_at)}</span>
						{:else if key === 'socio'}
							<span class="font-medium text-slate-800">{t.socio ?? '—'}</span>
						{:else if key === 'cliente_nombre'}
							<span class="text-slate-700">{t.cliente_nombre}</span>
						{:else if key === 'tipo'}
							{@const conf = coloresTipos[t.tipo] ?? { bg: 'bg-slate-100', text: 'text-slate-700', dot: 'bg-slate-400' }}
							<span class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium {conf.bg} {conf.text}">
								<span class="h-1.5 w-1.5 rounded-full {conf.dot}"></span>
								{TIPOS_MOVIMIENTO[t.tipo] ?? t.tipo}
							</span>
						{:else if key === 'puntos'}
							<span class="inline-flex items-center font-bold {t.puntos >= 0 ? 'text-emerald-600' : 'text-rose-600'}">
								{t.puntos >= 0 ? `+${t.puntos}` : t.puntos}
							</span>
						{:else}
							{t[key as keyof TransaccionOut] ?? '—'}
						{/if}
					{/snippet}
				</DataTable>
			</div>
		</div>
	{/if}
</div>
