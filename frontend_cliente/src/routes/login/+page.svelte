<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { auth } from '#lib/stores/auth.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import Spinner from '#lib/components/ui/Spinner.svelte';
	import logo from '#lib/assets/logo.png';
	import { env } from '$env/dynamic/public';

	const DEMO = env.PUBLIC_DEMO === '1';

	let esRegistro = $state(page.url.searchParams.get('registro') === '1');
	let nombre = $state('');
	let telefono = $state('');
	let ci = $state('');
	let codigoReferido = $state(
		page.url.searchParams.get('ref') ?? sessionStorage.getItem('yapai_ref') ?? ''
	);
	let error = $state('');
	let cargando = $state(false);

	async function enviar() {
		error = '';
		cargando = true;
		try {
			const tel = telefono.trim().replace(/[\s-]/g, '');
			const ciLimpio = ci.trim().replace(/[\s-]/g, '');
			if (esRegistro) {
				const nom = nombre.trim();
				if (nom.length < 2) throw new Error('Ingresa tu nombre completo');
				if (tel.length < 4) throw new Error('Ingresa un teléfono válido');
				if (ciLimpio.length < 3) throw new Error('Ingresa una cédula válida');
				await auth.registro(nom, tel, ciLimpio, codigoReferido || undefined);
				sessionStorage.removeItem('yapai_ref');
			} else {
				await auth.login(tel, ciLimpio);
			}
			goto('/billetera');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error inesperado';
		} finally {
			cargando = false;
		}
	}

	function cargarDemo() {
		telefono = '70000001';
		ci = '12345678';
	}
</script>

<div class="flex min-h-dvh items-center justify-center bg-gray-100 lg:bg-gradient-to-br lg:from-navy lg:via-[#0e1a38] lg:to-navy-claro lg:p-8">
	<div class="w-full max-w-sm lg:grid lg:max-w-4xl lg:grid-cols-2 lg:overflow-hidden lg:rounded-3xl lg:shadow-2xl">

		<!-- Panel de marca (solo desktop) -->
		<div class="hidden flex-col justify-between bg-gradient-to-br from-navy to-navy-claro p-10 text-white lg:flex">
			<div>
				<img src={logo} alt="YAPAI" class="h-16 rounded-xl bg-white p-2" />
				<h1 class="mt-6 text-3xl font-bold leading-tight">Tu billetera de puntos,<br />sin tarjetas ni apps.</h1>
				<p class="mt-3 text-sm leading-relaxed text-white/70">
					Acumula puntos en tus comercios favoritos, canjea premios con tu QR
					y descubre ofertas cerca de ti.
				</p>
			</div>
			<div class="space-y-3">
				{#each [
					{ icono: 'qr-code', texto: 'Tu pase digital siempre contigo' },
					{ icono: 'gift', texto: 'Premios y ofertas exclusivas' },
					{ icono: 'store', texto: 'Todos tus comercios en un solo lugar' },
				] as f}
					<div class="flex items-center gap-3 text-sm text-white/80">
						<span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10">
							<Icon name={f.icono} clase="h-4 w-4" />
						</span>
						{f.texto}
					</div>
				{/each}
			</div>
		</div>

		<!-- Formulario -->
		<div class="px-6 py-10 lg:bg-white lg:p-10">
			<div class="text-center lg:hidden">
				<img src={logo} alt="YAPAI" class="mx-auto h-16" />
				<p class="mt-1 text-base text-gray-500">Tu billetera de puntos</p>
			</div>

			<h2 class="hidden text-xl font-bold text-gray-900 lg:block">
				{esRegistro ? 'Crea tu cuenta' : 'Bienvenido de nuevo'}
			</h2>
			<p class="hidden text-sm text-gray-500 lg:block">
				{esRegistro ? 'Regístrate y empieza a acumular puntos' : 'Ingresa con tu teléfono y CI'}
			</p>

			<div class="mt-8 grid grid-cols-2 rounded-full border border-gray-300 p-1 lg:mt-6">
				<button onclick={() => { esRegistro = false; error = ''; }}
					class="flex items-center justify-center gap-2 rounded-full py-2 text-sm font-medium transition-colors
						{!esRegistro ? 'bg-indigo-600 text-white' : 'text-gray-600'}">
					<Icon name="log-in" clase="h-4 w-4" /> Ingresar
				</button>
				<button onclick={() => { esRegistro = true; error = ''; }}
					class="flex items-center justify-center gap-2 rounded-full py-2 text-sm font-medium transition-colors
						{esRegistro ? 'bg-indigo-600 text-white' : 'text-gray-600'}">
					<Icon name="user-plus" clase="h-4 w-4" /> Registrarme
				</button>
			</div>

			<form class="mt-6 space-y-4" onsubmit={(e) => { e.preventDefault(); enviar(); }}>
				{#if esRegistro}
					<label class="relative block">
						<Icon name="user-round" clase="pointer-events-none absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
						<input bind:value={nombre} type="text" placeholder="Nombre completo" autocomplete="name"
							class="w-full rounded-xl border border-gray-300 bg-white py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
					</label>
				{/if}
				<label class="relative block">
					<Icon name="phone" clase="pointer-events-none absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
					<input bind:value={telefono} type="tel" placeholder="Teléfono celular" autocomplete="tel"
						class="w-full rounded-xl border border-gray-300 bg-white py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
				</label>
				<label class="relative block">
					<Icon name="id-card" clase="pointer-events-none absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
					<input bind:value={ci} type="text" inputmode="numeric" placeholder="Cédula de identidad (CI)"
						class="w-full rounded-xl border border-gray-300 bg-white py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
				</label>
				{#if esRegistro}
					<label class="relative block">
						<Icon name="gift" clase="pointer-events-none absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
						<input bind:value={codigoReferido} type="text" placeholder="Código de referido (opcional)"
							class="w-full rounded-xl border border-gray-300 bg-white py-3 pl-10 pr-4 text-sm uppercase outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
					</label>
				{/if}

				{#if error}
					<div class="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
				{/if}

				<button type="submit" disabled={cargando}
					class="flex h-12 w-full items-center justify-center rounded-xl bg-indigo-600 text-base font-semibold text-white transition-colors hover:bg-indigo-700 disabled:opacity-60">
					{#if cargando}<Spinner clase="h-5 w-5" />{:else}{esRegistro ? 'Crear cuenta' : 'Ingresar'}{/if}
				</button>
			</form>

			{#if !esRegistro && DEMO}
				<button onclick={cargarDemo} disabled={cargando}
					class="mx-auto mt-4 flex items-center gap-1.5 text-sm text-indigo-600 hover:underline">
					<Icon name="play" clase="h-4 w-4" /> Cargar usuario demo (70000001 / 12345678)
				</button>
			{/if}

			<p class="mt-4 text-center text-xs text-gray-400">
				{esRegistro
					? 'Tus datos se guardarán en la base de datos para acumular y canjear puntos.'
					: 'Usa el teléfono y la CI con los que te registraste en el local o en la app.'}
			</p>
		</div>
	</div>
</div>
