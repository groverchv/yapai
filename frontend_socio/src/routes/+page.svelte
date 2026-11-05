<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { API_BASE, fetchRed } from '#lib/api/client';
	import { auth } from '#lib/stores/auth.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import type { PlanPublico } from '#lib/types';

	let planes = $state<PlanPublico[]>([]);
	let errorPlanes = $state('');

	onMount(async () => {
		if (auth.autenticado) {
			goto(auth.usuario?.rol === 'cajero' ? '/terminal' : '/dashboard');
			return;
		}
		try {
			const res = await fetchRed(`${API_BASE}/auth/planes`);
			planes = await res.json();
		} catch {
			errorPlanes = 'No se pudieron cargar los planes';
		}
	});

	const features = [
		{ icon: 'gift', titulo: 'Puntos y premios', texto: 'Tus clientes acumulan puntos y los canjean por premios reales en tu local.' },
		{ icon: 'monitor', titulo: 'Kiosco en tu local', texto: 'Una pantalla táctil donde el cliente se registra y gira la ruleta sin ayuda.' },
		{ icon: 'qr-code', titulo: 'Canje con QR', texto: 'El cliente genera un pase digital y tu cajero lo valida en segundos.' },
		{ icon: 'trending-up', titulo: 'Métricas reales', texto: 'Clientes nuevos, puntos emitidos y canjes por sucursal y por día.' }
	];

	const fmtLimite = (v: number, singular: string, plural?: string) =>
		v === 0 ? `${plural ?? singular + 's'} ilimitados` : `${v} ${v === 1 ? singular : (plural ?? singular + 's')}`;
</script>

<svelte:head><title>YAPAI — Fideliza a tus clientes</title></svelte:head>

<div class="min-h-screen bg-white">
	<!-- Header -->
	<header class="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
		<img src="/logo.png" alt="YAPAI" class="h-9" />
		<div class="flex items-center gap-4">
			<a href="/login" class="text-sm font-medium text-slate-600 hover:text-indigo-700">Ingresar</a>
			<a href="/registro" class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">
				Empezar gratis
			</a>
		</div>
	</header>

	<!-- Hero -->
	<section class="mx-auto max-w-6xl px-6 pb-16 pt-14 text-center">
		<span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
			<Icon name="sparkles" clase="h-3.5 w-3.5" /> Programa de fidelización para comercios
		</span>
		<h1 class="mx-auto mt-6 max-w-3xl text-4xl font-extrabold leading-tight text-indigo-950 sm:text-5xl">
			Convierte clientes de una visita en clientes de siempre
		</h1>
		<p class="mx-auto mt-5 max-w-2xl text-lg text-slate-600">
			YAPAI te da puntos, premios, un kiosco de registro y una ruleta — todo lo que tu
			local necesita para que la gente vuelva.
		</p>
		<div class="mt-8 flex items-center justify-center gap-4">
			<a href="/registro" class="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 font-semibold text-white shadow-lg shadow-emerald-600/25 hover:bg-emerald-700">
				Crear mi programa gratis <Icon name="arrow-right" clase="h-4 w-4" />
			</a>
			<a href="#planes" class="rounded-xl border border-slate-300 px-6 py-3 font-semibold text-slate-700 hover:border-emerald-500 hover:text-emerald-700">
				Ver planes
			</a>
		</div>
		<p class="mt-4 text-xs text-slate-500">14 días de prueba · Sin tarjeta</p>
	</section>

	<!-- Cómo funciona -->
	<section class="bg-indigo-950 py-16">
		<div class="mx-auto max-w-6xl px-6">
			<h2 class="text-center text-2xl font-bold text-white">Cómo funciona</h2>
			<div class="mt-10 grid gap-6 sm:grid-cols-3">
				<div class="rounded-2xl bg-white/5 p-6 ring-1 ring-white/10">
					<span class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-300"><Icon name="monitor" clase="h-5 w-5" /></span>
					<p class="mt-4 font-semibold text-white">1. Instala tu kiosco</p>
					<p class="mt-1.5 text-sm text-slate-300">Una tablet o pantalla en tu local. El cliente se registra con su cédula y teléfono en 20 segundos.</p>
				</div>
				<div class="rounded-2xl bg-white/5 p-6 ring-1 ring-white/10">
					<span class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-300"><Icon name="ruleta" clase="h-5 w-5" /></span>
					<p class="mt-4 font-semibold text-white">2. Ellos giran y ganan</p>
					<p class="mt-1.5 text-sm text-slate-300">La ruleta reparte puntos. Cada visita es una oportunidad de ganar — y de volver.</p>
				</div>
				<div class="rounded-2xl bg-white/5 p-6 ring-1 ring-white/10">
					<span class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-300"><Icon name="qr-code" clase="h-5 w-5" /></span>
					<p class="mt-4 font-semibold text-white">3. Canjean en caja</p>
					<p class="mt-1.5 text-sm text-slate-300">El cliente muestra su QR, tu cajero lo escanea y entrega el premio. Simple y sin fricción.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Features -->
	<section class="mx-auto max-w-6xl px-6 py-16">
		<h2 class="text-center text-2xl font-bold text-indigo-950">Todo incluido</h2>
		<div class="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
			{#each features as f}
				<div class="rounded-2xl border border-slate-200 p-6">
					<span class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600"><Icon name={f.icon} clase="h-5 w-5" /></span>
					<p class="mt-4 font-semibold text-indigo-950">{f.titulo}</p>
					<p class="mt-1.5 text-sm text-slate-600">{f.texto}</p>
				</div>
			{/each}
		</div>
	</section>

	<!-- Planes -->
	<section id="planes" class="mx-auto max-w-6xl px-6 pb-20">
		<h2 class="text-center text-2xl font-bold text-indigo-950">Planes para cada tamaño</h2>
		<p class="mt-2 text-center text-slate-500">Empieza gratis, crece cuando lo necesites.</p>

		{#if errorPlanes}
			<p class="mt-8 text-center text-sm text-slate-500">{errorPlanes}</p>
		{:else if planes.length === 0}
			<p class="mt-8 text-center text-sm text-slate-500">Cargando planes…</p>
		{:else}
			<div class="mt-10 grid gap-6 sm:grid-cols-3">
				{#each planes as plan, i}
					<div class="relative rounded-2xl border p-6 {i === 1 ? 'border-emerald-500 shadow-xl shadow-emerald-600/10 ring-2 ring-emerald-500/20' : 'border-slate-200'}">
						{#if i === 1}
							<span class="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-emerald-600 px-3 py-0.5 text-xs font-bold text-white">Recomendado</span>
						{/if}
						<p class="font-bold text-indigo-950">{plan.nombre}</p>
						<p class="mt-1 min-h-10 text-sm text-slate-500">{plan.descripcion ?? ''}</p>
						<p class="mt-4">
							<span class="text-3xl font-extrabold text-indigo-950">{plan.precio_mensual === 0 ? 'Gratis' : `${plan.moneda} ${plan.precio_mensual}`}</span>
							{#if plan.precio_mensual > 0}<span class="text-sm text-slate-500">/mes</span>{/if}
						</p>
						<ul class="mt-5 space-y-2 text-sm text-slate-600">
							<li class="flex items-center gap-2"><Icon name="check" clase="h-4 w-4 text-emerald-600" />{fmtLimite(plan.max_sucursales, 'sucursal', 'sucursales')}</li>
							<li class="flex items-center gap-2"><Icon name="check" clase="h-4 w-4 text-emerald-600" />{fmtLimite(plan.max_pantallas, 'pantalla', 'pantallas')} de kiosco</li>
							<li class="flex items-center gap-2"><Icon name="check" clase="h-4 w-4 text-emerald-600" />{fmtLimite(plan.max_clientes, 'cliente', 'clientes')}</li>
							<li class="flex items-center gap-2"><Icon name="check" clase="h-4 w-4 text-emerald-600" />{fmtLimite(plan.max_empleados, 'empleado', 'empleados')}</li>
							<li class="flex items-center gap-2 {plan.ruleta_habilitada ? '' : 'text-slate-500'}">
								<Icon name={plan.ruleta_habilitada ? 'check' : 'x'} clase="h-4 w-4 {plan.ruleta_habilitada ? 'text-emerald-600' : 'text-slate-300'}" />
								Ruleta del kiosco
							</li>
						</ul>
						<a href="/registro" class="mt-6 block rounded-lg py-2.5 text-center text-sm font-semibold {i === 1 ? 'bg-emerald-600 text-white hover:bg-emerald-700' : 'border border-slate-300 text-slate-700 hover:border-emerald-500 hover:text-emerald-700'}">
							Empezar con {plan.nombre}
						</a>
					</div>
				{/each}
			</div>
		{/if}
	</section>

	<footer class="border-t border-slate-200 py-8 text-center text-sm text-slate-500">
		<img src="/logo.png" alt="YAPAI" class="mx-auto h-7 opacity-70" />
		<p class="mt-3">© 2026 YAPAI — Fidelización para comercios</p>
	</footer>
</div>
