<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import KpiCard from '#lib/components/ui/KpiCard.svelte';
	import type { EstadoCuenta, OnboardingOut, OpcionesFiltro, ResumenSocio, SocioPlan } from '#lib/types';

	let resumen = $state<ResumenSocio | null>(null);
	let opciones = $state<OpcionesFiltro | null>(null);
	let plan = $state<SocioPlan | null>(null);
	let onboarding = $state<OnboardingOut | null>(null);
	let cuenta = $state<EstadoCuenta | null>(null);
	let error = $state('');

	let desde = $state('');
	let hasta = $state('');
	let sucursalId = $state('');

	async function cargar() {
		error = '';
		try {
			const params = new URLSearchParams();
			if (desde) params.set('desde', desde);
			if (hasta) params.set('hasta', hasta);
			if (sucursalId) params.set('sucursal_id', sucursalId);
			const qs = params.toString();
			resumen = await api.get<ResumenSocio>(`/socio/metricas/resumen${qs ? `?${qs}` : ''}`);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cargar';
		}
	}

	onMount(async () => {
		cargar();
		opciones = await api.get<OpcionesFiltro>('/socio/transacciones/filtros').catch(() => null);
		plan = await api.get<SocioPlan>('/socio/plan').catch(() => null);
		onboarding = await api.get<OnboardingOut>('/socio/onboarding').catch(() => null);
		cuenta = await api.get<EstadoCuenta>('/socio/facturacion').catch(() => null);
	});

	const barraUso = (uso: number, limite: number) =>
		limite === 0 ? 0 : Math.min(100, Math.round((uso / limite) * 100));
</script>

<div class="space-y-6">
	{#if cuenta?.estado === 'vencida'}
		<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
			<div class="flex items-center gap-3">
				<Icon name="alert-triangle" clase="h-6 w-6 text-red-600" />
				<div>
					<p class="font-semibold text-red-800">Tienes una factura vencida</p>
					<p class="text-sm text-red-700">Regulariza tu pago para evitar la suspensión del servicio.</p>
				</div>
			</div>
			<a href="/facturacion" class="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700">
				Ver facturación
			</a>
		</div>
	{/if}

	{#if plan?.en_trial}
		<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
			<div class="flex items-center gap-3">
				<Icon name="sparkles" clase="h-6 w-6 text-emerald-600" />
				<div>
					<p class="font-semibold text-emerald-800">
						Período de prueba — te quedan {plan.dias_trial} días
					</p>
					<p class="text-sm text-emerald-700">
						Estás en el plan {plan.plan_nombre}. Al terminar el trial puedes seguir en este plan o mejorar.
					</p>
				</div>
			</div>
		</div>
	{/if}

	{#if onboarding && !onboarding.completado}
		<div class="rounded-xl border border-slate-200 bg-white p-5">
			<div class="flex items-center justify-between">
				<h3 class="font-semibold text-indigo-950">Activa tu programa</h3>
				<span class="text-sm font-medium text-emerald-600">
					{onboarding.completados}/{onboarding.total}
				</span>
			</div>
			<div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
				<div class="h-full rounded-full bg-emerald-500 transition-all"
					style="width: {Math.round((onboarding.completados / onboarding.total) * 100)}%"></div>
			</div>
			<ul class="mt-4 space-y-2">
				{#each onboarding.pasos as paso}
					<li class="flex items-center gap-3 text-sm">
						{#if paso.hecho}
							<span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
								<Icon name="check" clase="h-3 w-3" />
							</span>
							<span class="text-slate-400 line-through">{paso.etiqueta}</span>
						{:else}
							<span class="h-5 w-5 shrink-0 rounded-full border-2 border-slate-300"></span>
							{#if paso.href}
								<a href={paso.href} class="font-medium text-indigo-950 hover:text-emerald-700 hover:underline">
									{paso.etiqueta}
								</a>
							{:else}
								<span class="text-slate-600">{paso.etiqueta}</span>
							{/if}
						{/if}
					</li>
				{/each}
			</ul>
		</div>
	{/if}

	{#if plan?.limites}
		<div class="rounded-xl border border-slate-200 bg-white p-5">
			<div class="flex items-center justify-between">
				<h3 class="font-semibold text-indigo-950">Tu plan — {plan.plan_nombre ?? 'Sin plan'}</h3>
				<span class="text-xs text-slate-400">Uso actual</span>
			</div>
			<div class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				{#each [
					['Sucursales', plan.uso.sucursales, plan.limites.max_sucursales],
					['Pantallas', plan.uso.pantallas, plan.limites.max_pantallas],
					['Clientes', plan.uso.clientes, plan.limites.max_clientes],
					['Empleados', plan.uso.empleados, plan.limites.max_empleados]
				] as [label, uso, limite]}
					<div>
						<div class="flex justify-between text-xs text-slate-500">
							<span>{label}</span>
							<span>{limite === 0 ? 'Ilimitado' : `${uso}/${limite}`}</span>
						</div>
						{#if (limite as number) > 0}
							<div class="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
								<div class="h-full rounded-full {barraUso(uso as number, limite as number) >= 90 ? 'bg-red-500' : 'bg-emerald-500'}"
									style="width: {barraUso(uso as number, limite as number)}%"></div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<div class="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4">
		<div>
			<label for="desde" class="mb-1 block text-xs font-medium text-slate-500">Desde</label>
			<input id="desde" type="date" bind:value={desde} onchange={cargar}
				class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
		</div>
		<div>
			<label for="hasta" class="mb-1 block text-xs font-medium text-slate-500">Hasta</label>
			<input id="hasta" type="date" bind:value={hasta} onchange={cargar}
				class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
		</div>
		<div>
			<label for="suc" class="mb-1 block text-xs font-medium text-slate-500">Sucursal</label>
			<select id="suc" bind:value={sucursalId} onchange={cargar}
				class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm">
				<option value="">Todas</option>
				{#each opciones?.sucursales ?? [] as s}
					<option value={s.id}>{s.nombre}</option>
				{/each}
			</select>
		</div>
	</div>

	{#if error}
		<p class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
	{/if}

	{#if resumen}
		<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
			<KpiCard titulo="Clientes nuevos" valor={resumen.clientes_nuevos} color="green" />
			<KpiCard titulo="Puntos otorgados" valor={resumen.puntos_otorgados} color="indigo" />
			<KpiCard titulo="Puntos consumidos" valor={resumen.puntos_consumidos} color="amber" />
			<KpiCard titulo="Canjes exitosos" valor={resumen.canjes_exitosos} color="sky" />
		</div>

		{#if resumen.stock_critico.length > 0}
			<div class="rounded-xl border border-amber-200 bg-amber-50 p-5">
				<h3 class="flex items-center gap-2 font-semibold text-amber-800"><Icon name="alert-triangle" clase="h-5 w-5" /> Stock crítico</h3>
				<ul class="mt-2 space-y-1 text-sm text-amber-700">
					{#each resumen.stock_critico as p}
						<li>· <strong>{p.nombre}</strong> — quedan {p.stock} unidades</li>
					{/each}
				</ul>
				<a href="/premios" class="mt-3 inline-block text-sm font-medium text-amber-800 underline">
					Revisar inventario <Icon name="arrow-right" clase="inline h-4 w-4 align-middle" />
				</a>
			</div>
		{/if}
	{:else if !error}
		<p class="text-slate-400">Cargando métricas…</p>
	{/if}
</div>
