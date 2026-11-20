<script lang="ts">
	import { onMount } from 'svelte';
	import { API_BASE, fetchRed } from '#lib/api/client';
	import { auth } from '#lib/stores/auth.svelte';
	import logo from '#lib/assets/logo.png';

	let status = $state<'operational' | 'degraded' | null>(null);

	onMount(async () => {
		try {
			const res = await fetchRed(`${API_BASE.replace('/api/v1', '')}/status`);
			status = (await res.json()).status ?? null;
		} catch { /* silencioso */ }
	});

	const faqs = [
		{
			p: '¿Qué es YAPAI?',
			r: 'Un programa de fidelización para tu negocio: tus clientes acumulan puntos en cada visita y los canjean por premios que tú defines. Incluye kiosco de registro, ruleta y portal de métricas.'
		},
		{
			p: '¿Cómo empiezan mis clientes?',
			r: 'Instala una tablet o pantalla en tu local (el kiosco). El cliente se registra con su cédula y teléfono en 20 segundos, gana puntos de bienvenida y puede girar la ruleta.'
		},
		{
			p: '¿Cómo funcionan los puntos?',
			r: 'El cliente gana puntos al registrarse, al girar la ruleta diaria y por bonus que tu cajero otorga en caja. Los puntos se canjean por premios mostrando un pase con QR que tu cajero valida.'
		},
		{
			p: '¿Qué necesito en mi local?',
			r: 'Cualquier tablet, smart TV o pantalla con navegador. Tu cajero la habilita con el PIN de caja desde la terminal y queda lista para que los clientes la usen.'
		},
		{
			p: '¿Cómo controlan el fraude?',
			r: 'Las pantallas piden PIN de caja y expiran a las 8 horas. Los cajeros tienen límites diarios de puntos. La ruleta permite un giro por cliente al día. Todo queda en un registro de auditoría inmutable.'
		},
		{
			p: '¿Puedo tener varias sucursales?',
			r: 'Sí. Cada sucursal tiene sus propias pantallas y cajeros, y las métricas se separan por sucursal. Los planes limitan el número de sucursales y pantallas.'
		},
		{
			p: '¿Qué pasa si se acaba mi prueba gratis?',
			r: 'Te avisamos por correo antes de que termine. Después se emite tu primera factura; si no se paga tras el período de gracia, la cuenta se suspende hasta regularizar.'
		},
		{
			p: '¿Cómo pago mi suscripción?',
			r: 'Con pago en línea (tarjeta) desde tu portal de facturación, o por transferencia/QR subiendo el comprobante — lo confirmamos en un máximo de 24 horas hábiles.'
		},
		{
			p: '¿Puedo exportar mis datos o darme de baja?',
			r: 'Sí. En Configuración → Cuenta puedes exportar todos tus datos en JSON y solicitar la baja. Conservamos tus datos 30 días por si cambias de opinión y luego se anonimizan.'
		},
		{
			p: '¿Qué datos guardan de mis clientes?',
			r: 'Solo lo necesario para el programa: nombre, cédula y teléfono (verificado por código SMS). El cliente puede exportar o eliminar su cuenta desde la app en cualquier momento.'
		}
	];
</script>

<svelte:head><title>Ayuda — YAPAI</title></svelte:head>

<div class="min-h-dvh bg-slate-50">
	<header class="mx-auto flex max-w-3xl items-center justify-between px-6 py-5">
		<a href="/"><img src={logo} alt="YAPAI" class="h-9" /></a>
		{#if auth.autenticado}
			<a href="/dashboard" class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:border-emerald-500 hover:text-emerald-700">
				Volver al panel
			</a>
		{:else}
			<a href="/registro" class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">
				Empezar gratis
			</a>
		{/if}
	</header>

	<main class="mx-auto max-w-3xl px-6 pb-16">
		<h1 class="text-3xl font-bold text-indigo-950">Preguntas frecuentes</h1>
		<p class="mt-2 text-slate-600">Todo lo que necesitas saber para sacarle el máximo a tu programa de fidelización.</p>

		<div class="mt-8 space-y-3">
			{#each faqs as f}
				<details class="group rounded-xl border border-slate-200 bg-white px-5 py-4 open:border-emerald-300">
					<summary class="flex cursor-pointer items-center justify-between font-semibold text-slate-800 [&::-webkit-details-marker]:hidden">
						{f.p}
						<span class="ml-3 text-slate-400 transition group-open:rotate-180">▾</span>
					</summary>
					<p class="mt-3 text-sm leading-relaxed text-slate-600">{f.r}</p>
				</details>
			{/each}
		</div>

		{#if status}
			<div class="mt-10 flex items-center justify-center gap-2 rounded-xl border {status === 'operational' ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50'} px-4 py-3">
				<span class="h-2 w-2 rounded-full {status === 'operational' ? 'bg-emerald-500' : 'bg-amber-500'}"></span>
				<span class="text-sm font-medium {status === 'operational' ? 'text-emerald-800' : 'text-amber-800'}">
					{status === 'operational' ? 'Todos los sistemas operativos' : 'Servicio degradado — estamos trabajando en ello'}
				</span>
			</div>
		{/if}

		<div class="mt-10 rounded-2xl border border-emerald-200 bg-emerald-50 p-6 text-center">
			<p class="font-semibold text-emerald-900">¿No encuentras tu respuesta?</p>
			<p class="mt-1 text-sm text-emerald-800">Escríbenos a
				<a href="mailto:soporte@yapai.com" class="font-semibold underline">soporte@yapai.com</a>
				y te respondemos en menos de 24 h hábiles.</p>
		</div>
	</main>
</div>
