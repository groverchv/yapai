<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import Icon from '#lib/components/ui/Icon.svelte';
	import { formatFecha, formatFechaCorta, formatDinero, TIPOS_MOVIMIENTO } from '#lib/utils/format';
	import type {
		EstadoCuenta,
		OnboardingOut,
		OpcionesFiltro,
		Pagina,
		Perfil,
		Premio,
		ResumenSocio,
		SocioPlan,
		Sucursal,
		Transaccion
	} from '#lib/types';

	let cargando = $state(true);
	let error = $state('');

	let resumen = $state<ResumenSocio | null>(null);
	let opciones = $state<OpcionesFiltro | null>(null);
	let plan = $state<SocioPlan | null>(null);
	let onboarding = $state<OnboardingOut | null>(null);
	let cuenta = $state<EstadoCuenta | null>(null);
	let perfil = $state<Perfil | null>(null);
	let transacciones = $state<Transaccion[]>([]);
	let sucursales = $state<Sucursal[]>([]);
	let premios = $state<Premio[]>([]);
	let inactivos = $state(0);

	// Filtros
	let desde = $state('');
	let hasta = $state('');
	let sucursalId = $state('');
	let rangoDias = $state<7 | 14 | 30>(14);

	// Tooltip del gráfico
	let puntoHover = $state<{ fecha: string; total: number; x: number; y: number } | null>(null);

	async function cargarMetricas() {
		error = '';
		try {
			const params = new URLSearchParams();
			if (desde) params.set('desde', desde);
			if (hasta) params.set('hasta', hasta);
			if (sucursalId) params.set('sucursal_id', sucursalId);
			const qs = params.toString();

			resumen = await api.get<ResumenSocio>(`/socio/metricas/resumen${qs ? `?${qs}` : ''}`);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cargar métricas';
		}
	}

	async function cargarTodo() {
		cargando = true;
		try {
			await Promise.allSettled([
				cargarMetricas(),
				api.get<Pagina<Transaccion>>('/socio/transacciones?size=6').then((res) => {
					transacciones = res.items;
				}),
				api.get<Sucursal[]>('/socio/sucursales').then((res) => {
					sucursales = res;
				}),
				api.get<Premio[]>('/socio/premios').then((res) => {
					premios = res;
				}),
				api.get<OpcionesFiltro>('/socio/transacciones/filtros').then((res) => {
					opciones = res;
				}),
				api.get<SocioPlan>('/socio/plan').then((res) => {
					plan = res;
				}),
				api.get<OnboardingOut>('/socio/onboarding').then((res) => {
					onboarding = res;
				}),
				api.get<EstadoCuenta>('/socio/facturacion').then((res) => {
					cuenta = res;
				}),
				api.get<Perfil>('/socio/perfil').then((res) => {
					perfil = res;
				}),
				api.get<unknown[]>('/socio/campanas/inactivos?dias=30').then((res) => {
					inactivos = res.length;
				})
			]);
		} finally {
			cargando = false;
		}
	}

	onMount(() => {
		cargarTodo();
	});

	function establecerRangoPredefinido(dias: number) {
		const h = new Date();
		const d = new Date();
		d.setDate(h.getDate() - dias);

		hasta = h.toISOString().split('T')[0];
		desde = d.toISOString().split('T')[0];
		cargarMetricas();
	}

	function limpiarFiltros() {
		desde = '';
		hasta = '';
		sucursalId = '';
		cargarMetricas();
	}

	// Serie filtrada del gráfico de barras
	let serieFiltrada = $derived(
		(resumen?.transacciones_30d ?? []).slice(-rangoDias)
	);

	let maxDia = $derived(
		Math.max(1, ...(serieFiltrada.map((d) => d.total) ?? [1]))
	);

	let totalSerie = $derived(
		serieFiltrada.reduce((acc, d) => acc + d.total, 0)
	);

	let promedioSerie = $derived(
		serieFiltrada.length > 0 ? (totalSerie / serieFiltrada.length).toFixed(1) : '0'
	);

	const barraUso = (uso: number, limite: number) =>
		limite === 0 ? 0 : Math.min(100, Math.round((uso / limite) * 100));

	// Δ% vs período espejo anterior (solo presente cuando hay rango desde/hasta)
	const pct = (actual: number, prev: number) =>
		prev === 0 ? null : Math.round(((actual - prev) / prev) * 100);

	let dClientes = $derived(
		resumen?.previos ? pct(resumen.clientes_nuevos, resumen.previos.clientes_nuevos) : null
	);
	let dEmitidos = $derived(
		resumen?.previos ? pct(resumen.puntos_otorgados, resumen.previos.puntos_otorgados) : null
	);
	let dConsumidos = $derived(
		resumen?.previos ? pct(resumen.puntos_consumidos, resumen.previos.puntos_consumidos) : null
	);
	let dCanjes = $derived(
		resumen?.previos ? pct(resumen.canjes_exitosos, resumen.previos.canjes_exitosos) : null
	);

	// Alertas accionables del dashboard ("Requiere tu atención")
	let atencion = $derived.by(() => {
		const items: { texto: string; accion: string; href: string }[] = [];
		if (cuenta?.estado === 'pendiente')
			items.push({ texto: 'Tienes una factura de tu plan pendiente de pago', accion: 'Ver facturación', href: '/facturacion' });
		if ((resumen?.pases_activos ?? 0) > 0)
			items.push({
				texto: `${resumen!.pases_activos} pase(s) esperando canje en caja`,
				accion: 'Ir a la terminal', href: '/terminal',
			});
		for (const p of resumen?.stock_critico ?? [])
			items.push({
				texto: `Stock bajo: "${p.nombre}" — quedan ${p.stock}`,
				accion: 'Revisar premios', href: '/premios',
			});
		if (inactivos > 0)
			items.push({
				texto: `${inactivos} clientes llevan 30+ días sin volver`,
				accion: 'Reactivarlos', href: '/campanas',
			});
		return items;
	});

	const coloresTipos: Record<string, { bg: string; text: string; dot: string; icon: string }> = {
		registro: { bg: 'bg-blue-50 border-blue-200', text: 'text-blue-700', dot: 'bg-blue-500', icon: 'users' },
		ruleta: { bg: 'bg-amber-50 border-amber-200', text: 'text-amber-700', dot: 'bg-amber-500', icon: 'ruleta' },
		bonus_manual: { bg: 'bg-purple-50 border-purple-200', text: 'text-purple-700', dot: 'bg-purple-500', icon: 'sparkles' },
		canje: { bg: 'bg-emerald-50 border-emerald-200', text: 'text-emerald-700', dot: 'bg-emerald-500', icon: 'gift' },
		congelar: { bg: 'bg-slate-50 border-slate-200', text: 'text-slate-700', dot: 'bg-slate-500', icon: 'lock' },
		liberar: { bg: 'bg-teal-50 border-teal-200', text: 'text-teal-700', dot: 'bg-teal-500', icon: 'lock-open' },
		anulacion: { bg: 'bg-rose-50 border-rose-200', text: 'text-rose-700', dot: 'bg-rose-500', icon: 'alert-triangle' }
	};
</script>

{#snippet delta(d: number | null)}
	{#if d !== null}
		<span
			class="rounded px-1.5 py-0.5 text-[10px] font-bold {d >= 0
				? 'bg-emerald-100 text-emerald-700'
				: 'bg-rose-100 text-rose-700'}"
			title="vs período anterior"
		>
			{d >= 0 ? '↑' : '↓'} {Math.abs(d)}%
		</span>
	{/if}
{/snippet}

<div class="space-y-6">
	<!-- ENCABEZADO PRINCIPAL CON ACCIONES RÁPIDAS -->
	<div class="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200/80 bg-gradient-to-r from-white via-slate-50/60 to-emerald-50/30 p-6 shadow-xs lg:flex-row lg:items-center">
		<div class="flex items-center gap-4">
			{#if perfil?.logo_url}
				<div class="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-white p-1 shadow-sm ring-1 ring-slate-200/80">
					<img src={perfil.logo_url} alt={perfil.tenant_nombre} class="h-full w-full object-cover rounded-xl" />
				</div>
			{/if}
			<div>
				<div class="flex items-center gap-2.5">
					<h1 class="text-2xl font-extrabold tracking-tight text-slate-900">
						Dashboard del Socio
					</h1>
					<span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-100/90 px-3 py-0.5 text-xs font-semibold text-emerald-800 shadow-2xs">
						<span class="h-2 w-2 animate-pulse rounded-full bg-emerald-500"></span>
						Comercio Activo
					</span>
				</div>
				<p class="mt-1 text-sm text-slate-600">
					Bienvenido, <strong class="text-slate-800">{perfil?.nombre ?? 'Socio'}</strong> ·
					<span class="font-medium text-emerald-700">{perfil?.tenant_nombre ?? 'Tu Negocio'}</span>
				</p>
			</div>
		</div>

		<!-- Acciones Rápidas -->
		<div class="flex flex-wrap items-center gap-2.5">
			<button
				onclick={cargarTodo}
				disabled={cargando}
				class="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-2xs transition hover:bg-slate-50 hover:text-slate-900 disabled:opacity-50"
				title="Refrescar datos"
			>
				<Icon name="refresh-cw" clase="h-3.5 w-3.5 text-slate-500 {cargando ? 'animate-spin' : ''}" />
				<span>Actualizar</span>
			</button>

			<a
				href="/terminal"
				class="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-2 text-xs font-bold text-white shadow-sm transition hover:from-emerald-700 hover:to-teal-700"
			>
				<Icon name="credit-card" clase="h-4 w-4" />
				<span>Terminal de Caja</span>
			</a>

			{#if sucursales.length > 0 && sucursales[0].pantallas.length > 0}
				<a
					href="/kiosco/{sucursales[0].pantallas[0].device_token}"
					target="_blank"
					class="inline-flex items-center gap-1.5 rounded-xl border border-emerald-300 bg-emerald-50/80 px-3.5 py-2 text-xs font-semibold text-emerald-800 shadow-2xs transition hover:bg-emerald-100"
				>
					<Icon name="monitor" clase="h-3.5 w-3.5" />
					<span>Abrir Kiosco ↗</span>
				</a>
			{/if}

			<a
				href="/premios"
				class="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-2xs transition hover:bg-slate-50"
			>
				<Icon name="gift" clase="h-3.5 w-3.5 text-slate-500" />
				<span>Premios</span>
			</a>
		</div>
	</div>

	<!-- ALERTA DE FACTURA VENCIDA (SI APLICA) -->
	{#if cuenta?.estado === 'vencida'}
		<div class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-rose-200 bg-rose-50/90 p-4 shadow-xs">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-600">
					<Icon name="alert-triangle" clase="h-5 w-5" />
				</div>
				<div>
					<p class="font-bold text-rose-900">Tienes una factura de tu plan SaaS vencida</p>
					<p class="text-xs text-rose-700">Por favor regulariza tu pago para mantener la emisión de puntos activa.</p>
				</div>
			</div>
			<a href="/facturacion" class="rounded-xl bg-rose-600 px-4 py-2 text-xs font-bold text-white shadow-xs transition hover:bg-rose-700">
				Ver facturas y pagar
			</a>
		</div>
	{/if}

	<!-- PERÍODO DE PRUEBA -->
	{#if plan?.en_trial}
		<div class="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-emerald-200 bg-gradient-to-r from-emerald-50 via-teal-50 to-white p-4 shadow-xs">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-xs">
					<Icon name="sparkles" clase="h-5 w-5" />
				</div>
				<div>
					<p class="font-bold text-emerald-950">
						Período de prueba activo — te quedan <span class="text-emerald-700">{plan.dias_trial} días</span>
					</p>
					<p class="text-xs text-emerald-800">
						Disfrutas de todas las funcionalidades del plan <strong>{plan.plan_nombre}</strong>. Al finalizar puedes continuar o actualizar tu plan.
					</p>
				</div>
			</div>
			<a href="/facturacion" class="rounded-xl border border-emerald-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-emerald-800 transition hover:bg-emerald-50">
				Gestionar plan
			</a>
		</div>
	{/if}

	<!-- ONBOARDING: ACTIVA TU PROGRAMA (PASO A PASO) -->
	{#if onboarding && !onboarding.completado}
		<div class="overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2">
					<div class="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
						<Icon name="target" clase="h-4 w-4" />
					</div>
					<div>
						<h3 class="font-bold text-slate-800">Guía de Inicio: Activa tu Programa de Puntos</h3>
						<p class="text-xs text-slate-500">Completa estos pasos para comenzar a fidelizar clientes en tu local.</p>
					</div>
				</div>
				<span class="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800">
					{onboarding.completados} de {onboarding.total} completados
				</span>
			</div>

			<div class="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
				<div
					class="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-500"
					style="width: {Math.round((onboarding.completados / onboarding.total) * 100)}%"
				></div>
			</div>

			<div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
				{#each onboarding.pasos as paso, i}
					<div class="flex items-center gap-2.5 rounded-xl border border-slate-100 p-2.5 transition {paso.hecho ? 'bg-slate-50/70 opacity-75' : 'bg-white hover:border-emerald-200'}">
						{#if paso.hecho}
							<span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-white shadow-2xs">
								<Icon name="check" clase="h-3.5 w-3.5" />
							</span>
							<span class="text-xs font-medium text-slate-500 line-through truncate">{paso.etiqueta}</span>
						{:else}
							<span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 border-slate-300 text-xs font-bold text-slate-500">
								{i + 1}
							</span>
							{#if paso.href}
								<a href={paso.href} class="text-xs font-bold text-slate-800 hover:text-emerald-700 hover:underline truncate">
									{paso.etiqueta} →
								</a>
							{:else}
								<span class="text-xs text-slate-600 truncate">{paso.etiqueta}</span>
							{/if}
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- REQUIERE TU ATENCIÓN: alertas accionables -->
	{#if atencion.length > 0}
		<div class="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 shadow-xs">
			<div class="flex items-center gap-2">
				<div class="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
					<Icon name="alert-triangle" clase="h-4 w-4" />
				</div>
				<h3 class="font-bold text-amber-950">Requiere tu atención</h3>
				<span class="rounded-full bg-amber-200/80 px-2 py-0.5 text-xs font-bold text-amber-900">
					{atencion.length}
				</span>
			</div>
			<ul class="mt-3 space-y-2">
				{#each atencion as a}
					<li>
						<a
							href={a.href}
							class="flex items-center justify-between gap-3 rounded-xl bg-white px-4 py-2.5 text-sm text-slate-700 ring-1 ring-amber-200/60 transition hover:ring-amber-400"
						>
							<span>{a.texto}</span>
							<span class="shrink-0 text-xs font-bold text-amber-700">{a.accion} →</span>
						</a>
					</li>
				{/each}
			</ul>
		</div>
	{/if}

	<!-- FILTROS Y PERÍODOS DE ANÁLISIS -->
	<div class="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs sm:flex-row sm:items-center sm:justify-between">
		<!-- Filtros rápidos por botones -->
		<div class="flex items-center gap-1.5">
			<span class="text-xs font-medium text-slate-500 mr-1">Rango:</span>
			<button
				onclick={() => { rangoDias = 7; establecerRangoPredefinido(7); }}
				class="rounded-lg px-2.5 py-1 text-xs font-semibold transition {rangoDias === 7 ? 'bg-emerald-600 text-white shadow-2xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}"
			>
				7 Días
			</button>
			<button
				onclick={() => { rangoDias = 14; establecerRangoPredefinido(14); }}
				class="rounded-lg px-2.5 py-1 text-xs font-semibold transition {rangoDias === 14 ? 'bg-emerald-600 text-white shadow-2xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}"
			>
				14 Días
			</button>
			<button
				onclick={() => { rangoDias = 30; establecerRangoPredefinido(30); }}
				class="rounded-lg px-2.5 py-1 text-xs font-semibold transition {rangoDias === 30 ? 'bg-emerald-600 text-white shadow-2xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}"
			>
				30 Días
			</button>
			<button
				onclick={limpiarFiltros}
				class="rounded-lg px-2 py-1 text-xs text-slate-500 hover:text-slate-800 transition underline ml-1"
			>
				Todo el histórico
			</button>
		</div>

		<!-- Selector de Sucursal y Fechas específicas -->
		<div class="flex flex-wrap items-center gap-2">
			{#if opciones?.sucursales && opciones.sucursales.length > 1}
				<div class="flex items-center gap-1">
					<label for="suc" class="text-xs text-slate-500">Sucursal:</label>
					<select
						id="suc"
						bind:value={sucursalId}
						onchange={cargarMetricas}
						class="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 shadow-2xs focus:border-emerald-500 focus:outline-none"
					>
						<option value="">Todas las sucursales</option>
						{#each opciones.sucursales as s}
							<option value={s.id}>{s.nombre}</option>
						{/each}
					</select>
				</div>
			{/if}

			<div class="flex items-center gap-1">
				<input
					type="date"
					bind:value={desde}
					onchange={cargarMetricas}
					class="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 shadow-2xs focus:border-emerald-500 focus:outline-none"
					title="Fecha inicial"
				/>
				<span class="text-xs text-slate-500">a</span>
				<input
					type="date"
					bind:value={hasta}
					onchange={cargarMetricas}
					class="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 shadow-2xs focus:border-emerald-500 focus:outline-none"
					title="Fecha final"
				/>
			</div>
		</div>
	</div>

	{#if error}
		<div class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-700">
			{error}
		</div>
	{/if}

	<!-- 6 TARJETAS KPI PRINCIPALES -->
	<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
		<!-- Clientes Totales -->
		<div class="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition hover:border-blue-300 hover:shadow-md">
			<div class="flex items-center justify-between">
				<span class="text-xs font-semibold text-slate-500">Clientes Afiliados</span>
				<div class="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-50 text-blue-600 transition group-hover:scale-110">
					<Icon name="users" clase="h-4 w-4" />
				</div>
			</div>
			<p class="mt-2 text-2xl font-black text-slate-900">
				{resumen?.clientes_totales ?? 0}
			</p>
			<div class="mt-1 flex items-center gap-1 text-xs font-medium text-blue-700">
				<span class="font-bold">+{resumen?.clientes_nuevos ?? 0}</span>
				<span class="text-slate-500">en período</span>
				{@render delta(dClientes)}
			</div>
		</div>

		<!-- Puntos Otorgados -->
		<div class="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition hover:border-indigo-300 hover:shadow-md">
			<div class="flex items-center justify-between">
				<span class="text-xs font-semibold text-slate-500">Puntos Emitidos</span>
				<div class="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 transition group-hover:scale-110">
					<Icon name="sparkles" clase="h-4 w-4" />
				</div>
			</div>
			<p class="mt-2 text-2xl font-black text-indigo-900">
				{resumen?.puntos_otorgados?.toLocaleString() ?? 0}
			</p>
			<div class="mt-1 flex items-center gap-1 text-xs">
				<span class="text-slate-500">Regalados a clientes</span>
				{@render delta(dEmitidos)}
			</div>
		</div>

		<!-- Puntos Consumidos -->
		<div class="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition hover:border-amber-300 hover:shadow-md">
			<div class="flex items-center justify-between">
				<span class="text-xs font-semibold text-slate-500">Puntos Canjeados</span>
				<div class="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-50 text-amber-600 transition group-hover:scale-110">
					<Icon name="gift" clase="h-4 w-4" />
				</div>
			</div>
			<p class="mt-2 text-2xl font-black text-amber-900">
				{resumen?.puntos_consumidos?.toLocaleString() ?? 0}
			</p>
			<div class="mt-1 flex items-center gap-1 text-xs">
				<span class="text-slate-500">Puntos en premios</span>
				{@render delta(dConsumidos)}
			</div>
		</div>

		<!-- Tasa de Fidelización -->
		<div class="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition hover:border-emerald-300 hover:shadow-md">
			<div class="flex items-center justify-between">
				<span class="text-xs font-semibold text-slate-500">Tasa Fidelización</span>
				<div class="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 transition group-hover:scale-110">
					<Icon name="trending-up" clase="h-4 w-4" />
				</div>
			</div>
			<p class="mt-2 text-2xl font-black text-emerald-900">
				{resumen?.tasa_redencion ?? 0}%
			</p>
			<p class="mt-1 text-xs text-slate-500">Retención de clientes</p>
		</div>

		<!-- Canjes Exitosos -->
		<div class="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition hover:border-sky-300 hover:shadow-md">
			<div class="flex items-center justify-between">
				<span class="text-xs font-semibold text-slate-500">Premios Canjeados</span>
				<div class="flex h-8 w-8 items-center justify-center rounded-xl bg-sky-50 text-sky-600 transition group-hover:scale-110">
					<Icon name="trophy" clase="h-4 w-4" />
				</div>
			</div>
			<p class="mt-2 text-2xl font-black text-sky-900">
				{resumen?.canjes_exitosos ?? 0}
			</p>
			<div class="mt-1 flex items-center gap-1 text-xs">
				<span class="text-slate-500">Canjes en mostrador</span>
				{@render delta(dCanjes)}
			</div>
		</div>

		<!-- Pases Activos en Espera -->
		<div class="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs transition hover:border-purple-300 hover:shadow-md">
			<div class="flex items-center justify-between">
				<span class="text-xs font-semibold text-slate-500">Pases en Caja</span>
				<div class="flex h-8 w-8 items-center justify-center rounded-xl bg-purple-50 text-purple-600 transition group-hover:scale-110">
					<Icon name="qr-code" clase="h-4 w-4" />
				</div>
			</div>
			<p class="mt-2 text-2xl font-black text-purple-900">
				{resumen?.pases_activos ?? 0}
			</p>
			<a href="/terminal" class="mt-1 block text-xs font-bold text-purple-700 hover:underline">
				Ver en Terminal →
			</a>
		</div>
	</div>

	<!-- GRÁFICO DE BARRAS DE ACTIVIDAD DIARIA -->
	<div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
		<div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
			<div>
				<h3 class="font-bold text-slate-900 flex items-center gap-2">
					<Icon name="activity" clase="h-4 w-4 text-emerald-600" />
					Flujo de Visitas y Actividad ({rangoDias} días)
				</h3>
				<p class="text-xs text-slate-500">Movimientos de puntos y registros generados en tus locales.</p>
			</div>

			<div class="flex items-center gap-3 text-xs">
				<div class="flex items-center gap-1.5">
					<span class="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
					<span class="text-slate-600 font-medium">Total: <strong class="text-slate-900">{totalSerie}</strong></span>
				</div>
				<div class="flex items-center gap-1.5">
					<span class="h-2.5 w-2.5 rounded-full bg-teal-400"></span>
					<span class="text-slate-600 font-medium">Promedio: <strong class="text-slate-900">{promedioSerie}/día</strong></span>
				</div>
			</div>
		</div>

		<!-- Contenedor del gráfico SVG -->
		<div class="relative mt-6">
			<div class="flex h-40 w-full items-end gap-1 sm:gap-2">
				{#each serieFiltrada as d}
					{@const altura = Math.max(8, Math.round((d.total / maxDia) * 100))}
					<div
						role="presentation"
						class="group relative flex flex-1 flex-col items-center h-full justify-end cursor-pointer"
						onmouseenter={(e) => {
							const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
							puntoHover = { fecha: d.fecha, total: d.total, x: rect.left + rect.width / 2, y: rect.top };
						}}
						onmouseleave={() => { puntoHover = null; }}
					>
						<div
							class="w-full rounded-t-lg transition-all duration-300 {d.total > 0 ? 'bg-gradient-to-t from-emerald-600 to-teal-400 group-hover:from-emerald-500 group-hover:to-teal-300 group-hover:shadow-md' : 'bg-slate-100'}"
							style="height: {altura}%"
						></div>

						<span class="mt-2 text-[10px] font-medium text-slate-500 group-hover:text-slate-800">
							{d.fecha.split('-')[2]}
						</span>
					</div>
				{/each}
			</div>

			<!-- Tooltip flotante interactivo -->
			{#if puntoHover}
				<div
					class="pointer-events-none fixed z-50 -translate-x-1/2 -translate-y-12 rounded-lg bg-slate-900 px-2.5 py-1 text-xs text-white shadow-lg"
					style="left: {puntoHover.x}px; top: {puntoHover.y}px"
				>
					<p class="font-bold">{formatFechaCorta(puntoHover.fecha)}</p>
					<p class="text-[11px] text-emerald-300">{puntoHover.total} {puntoHover.total === 1 ? 'operación' : 'operaciones'}</p>
				</div>
			{/if}
		</div>
	</div>

	<!-- GRID DE 2 COLUMNAS: ACTIVIDAD EN VIVO Y PREMIOS TOP -->
	<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
		<!-- Columna 1: Transacciones Recientes en Vivo -->
		<div class="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
			<div>
				<div class="flex items-center justify-between pb-3 border-b border-slate-100">
					<div class="flex items-center gap-2">
						<div class="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-50 text-purple-600">
							<Icon name="sparkles" clase="h-4 w-4" />
						</div>
						<h3 class="font-bold text-slate-900">Actividad Reciente en Caja</h3>
					</div>
					<a href="/transacciones" class="text-xs font-semibold text-emerald-700 hover:underline">
						Ver todas →
					</a>
				</div>

				<div class="mt-3 divide-y divide-slate-100">
					{#if transacciones.length === 0}
						<div class="py-10 text-center">
							<Icon name="inbox" clase="mx-auto h-8 w-8 text-slate-300" />
							<p class="mt-2 text-xs text-slate-500">Aún no hay transacciones en este comercio.</p>
							<p class="text-[11px] text-slate-500">Registra clientes en el kiosco o canjea puntos en la terminal de caja.</p>
						</div>
					{:else}
						{#each transacciones as tx}
							{@const estilo = coloresTipos[tx.tipo] ?? coloresTipos.bonus_manual}
							<div class="flex items-center justify-between py-3 hover:bg-slate-50/50 rounded-lg px-1 transition">
								<div class="flex items-center gap-3 min-w-0">
									<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full {estilo.bg} {estilo.text}">
										<Icon name={estilo.icon} clase="h-4 w-4" />
									</div>
									<div class="min-w-0 truncate">
										<p class="text-xs font-bold text-slate-800 truncate">
											{tx.cliente_nombre}
										</p>
										<p class="text-[11px] text-slate-500 flex items-center gap-1.5">
											<span>CI: {tx.cliente_ci}</span>
											<span>·</span>
											<span>{formatFecha(tx.created_at)}</span>
										</p>
									</div>
								</div>

								<div class="text-right shrink-0">
									<span class="text-xs font-extrabold {tx.puntos >= 0 ? 'text-emerald-600' : 'text-amber-600'}">
										{tx.puntos >= 0 ? `+${tx.puntos}` : tx.puntos} pts
									</span>
									<span class="block text-[10px] uppercase font-semibold text-slate-500">
										{TIPOS_MOVIMIENTO[tx.tipo] ?? tx.tipo}
									</span>
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>

			<div class="pt-3 border-t border-slate-100">
				<a
					href="/terminal"
					class="flex items-center justify-center gap-2 rounded-xl bg-slate-50 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition"
				>
					<Icon name="tap" clase="h-3.5 w-3.5" />
					<span>Ir al Punto de Venta / Terminal de Caja</span>
				</a>
			</div>
		</div>

		<!-- Columna 2: Catálogo de Premios y Stock -->
		<div class="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
			<div>
				<div class="flex items-center justify-between pb-3 border-b border-slate-100">
					<div class="flex items-center gap-2">
						<div class="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
							<Icon name="gift" clase="h-4 w-4" />
						</div>
						<h3 class="font-bold text-slate-900">Premios Populares e Inventario</h3>
					</div>
					<a href="/premios" class="text-xs font-semibold text-emerald-700 hover:underline">
						Gestionar →
					</a>
				</div>

				<!-- Alerta de stock crítico si aplica -->
				{#if resumen?.stock_critico && resumen.stock_critico.length > 0}
					<div class="mt-3 rounded-xl border border-amber-200 bg-amber-50/80 p-3">
						<p class="text-xs font-bold text-amber-900 flex items-center gap-1.5">
							<Icon name="alert-triangle" clase="h-4 w-4 text-amber-600" />
							Stock Crítico ({resumen.stock_critico.length} {resumen.stock_critico.length === 1 ? 'premio' : 'premios'})
						</p>
						<p class="mt-0.5 text-[11px] text-amber-800">
							{#each resumen.stock_critico as sc, i}
								<span><strong>{sc.nombre}</strong> ({sc.stock} unid){i < resumen.stock_critico.length - 1 ? ', ' : ''}</span>
							{/each}
						</p>
					</div>
				{/if}

				<!-- Lista de premios -->
				<div class="mt-3 divide-y divide-slate-100">
					{#if premios.length === 0}
						<div class="py-10 text-center">
							<Icon name="gift" clase="mx-auto h-8 w-8 text-slate-300" />
							<p class="mt-2 text-xs text-slate-500">No has creado premios todavía.</p>
							<a href="/premios" class="mt-2 inline-block text-xs font-bold text-emerald-700 underline">
								Crear primer premio canjeable
							</a>
						</div>
					{:else}
						{#each premios.slice(0, 5) as p}
							<div class="flex items-center justify-between py-2.5 hover:bg-slate-50/50 rounded-lg px-1 transition">
								<div class="flex items-center gap-3 min-w-0">
									{#if p.imagen_url}
										<img src={p.imagen_url} alt={p.nombre} class="h-10 w-10 shrink-0 rounded-lg object-cover border border-slate-200" />
									{:else}
										<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
											<Icon name="gift" clase="h-5 w-5" />
										</div>
									{/if}

									<div class="min-w-0 truncate">
										<p class="text-xs font-bold text-slate-800 truncate">{p.nombre}</p>
										<span class="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700">
											{p.costo_puntos} pts
										</span>
									</div>
								</div>

								<div class="text-right shrink-0">
									{#if p.stock_limitado}
										<span class="rounded-full px-2 py-0.5 text-[10px] font-bold {(p.stock ?? 0) <= 3 ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-700'}">
											{p.stock} disponibles
										</span>
									{:else}
										<span class="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
											Ilimitado
										</span>
									{/if}
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>

			<div class="pt-3 border-t border-slate-100">
				<a
					href="/premios"
					class="flex items-center justify-center gap-2 rounded-xl bg-slate-50 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition"
				>
					<Icon name="plus" clase="h-3.5 w-3.5" />
					<span>Agregar un nuevo premio al catálogo</span>
				</a>
			</div>
		</div>
	</div>

	<!-- SUCURSALES Y PANTALLAS DE KIOSCO EN VIVO -->
	{#if sucursales.length > 0}
		<div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
			<div class="flex items-center justify-between pb-3 border-b border-slate-100">
				<div class="flex items-center gap-2">
					<div class="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-50 text-teal-600">
						<Icon name="store" clase="h-4 w-4" />
					</div>
					<div>
						<h3 class="font-bold text-slate-900">Sucursales y Kioscos Físicos</h3>
						<p class="text-xs text-slate-500">Puntos de contacto donde tus clientes se registran y giran la ruleta.</p>
					</div>
				</div>
				<a href="/sucursales" class="text-xs font-semibold text-emerald-700 hover:underline">
					Gestionar sucursales →
				</a>
			</div>

			<div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
				{#each sucursales as suc}
					<div class="flex flex-col justify-between rounded-xl border border-slate-200/80 bg-slate-50/50 p-4 transition hover:border-emerald-300 hover:bg-white hover:shadow-sm">
						<div>
							<div class="flex items-center justify-between">
								<h4 class="font-bold text-slate-800 text-sm">{suc.nombre}</h4>
								<span class="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
									Activa
								</span>
							</div>
							<p class="mt-1 text-xs text-slate-500">{suc.direccion ?? 'Sin dirección especificada'}</p>
							{#if suc.encargado_nombre}
								<p class="mt-0.5 text-[11px] text-slate-500">Encargado: {suc.encargado_nombre}</p>
							{/if}
						</div>

						<div class="mt-4 pt-3 border-t border-slate-200/60">
							{#if suc.pantallas.length > 0}
								{@const pantalla = suc.pantallas[0]}
								<div class="flex items-center justify-between">
									<div class="flex items-center gap-1.5 text-xs text-slate-600">
										<Icon name="monitor" clase="h-3.5 w-3.5 text-slate-500" />
										<span>{pantalla.nombre}</span>
									</div>
									<a
										href="/kiosco/{pantalla.device_token}"
										target="_blank"
										class="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-2.5 py-1 text-[11px] font-bold text-white transition hover:bg-emerald-700 shadow-2xs"
									>
										<span>Abrir</span>
										<Icon name="external-link" clase="h-3 w-3" />
									</a>
								</div>
							{:else}
								<p class="text-xs text-slate-500 italic">Sin pantalla registrada</p>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- CONSUMO DE LÍMITES DEL PLAN SAAS -->
	{#if plan?.limites}
		<div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
			<div class="flex items-center justify-between pb-3 border-b border-slate-100">
				<div>
					<h3 class="font-bold text-slate-900">Capacidad de tu Plan — {plan.plan_nombre ?? 'Starter'}</h3>
					<p class="text-xs text-slate-500">Límites permitidos en tu suscripción actual.</p>
				</div>
				<a href="/facturacion" class="text-xs font-semibold text-emerald-700 hover:underline">
					Mejorar plan →
				</a>
			</div>

			<div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
				{#each [
					['Sucursales habilitadas', plan.uso.sucursales, plan.limites.max_sucursales, 'store'],
					['Pantallas de Kiosco', plan.uso.pantallas, plan.limites.max_pantallas, 'monitor'],
					['Clientes registrados', plan.uso.clientes, plan.limites.max_clientes, 'users'],
					['Cajeros y Empleados', plan.uso.empleados, plan.limites.max_empleados, 'user-round']
				] as [label, uso, limite, iconName]}
					{@const porcentaje = barraUso(uso as number, limite as number)}
					<div class="rounded-xl border border-slate-100 bg-slate-50/50 p-3.5">
						<div class="flex items-center justify-between">
							<span class="text-xs font-semibold text-slate-600">{label}</span>
							<Icon name={iconName as string} clase="h-3.5 w-3.5 text-slate-500" />
						</div>
						<p class="mt-2 text-lg font-black text-slate-800">
							{uso} <span class="text-xs font-normal text-slate-500">/ {limite === 0 ? 'Ilimitado' : limite}</span>
						</p>

						{#if (limite as number) > 0}
							<div class="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200">
								<div
									class="h-full rounded-full transition-all duration-300 {porcentaje >= 90 ? 'bg-rose-500' : 'bg-emerald-500'}"
									style="width: {porcentaje}%"
								></div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
