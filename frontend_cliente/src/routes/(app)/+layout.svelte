<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { auth } from '#lib/stores/auth.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import logo from '#lib/assets/logo.png';
	import { cloudinaryThumb, iniciales } from '#lib/utils/format';
	import { onMount } from 'svelte';

	let { children } = $props();

	// Banner offline: el contenido ya cargado sigue visible; solo avisamos.
	let sinConexion = $state(false);
	function revisarRed() {
		sinConexion = !navigator.onLine;
	}

	onMount(() => {
		if (!auth.autenticado) goto('/login', { replaceState: true });
		revisarRed();
		window.addEventListener('online', revisarRed);
		window.addEventListener('offline', revisarRed);
		return () => {
			window.removeEventListener('online', revisarRed);
			window.removeEventListener('offline', revisarRed);
		};
	});

	const tabs = [
		{ ruta: '/billetera', nombre: 'Billetera', icono: 'wallet' },
		{ ruta: '/explorar', nombre: 'Explorar', icono: 'store' },
		{ ruta: '/pases', nombre: 'Pases', icono: 'qr-code' },
		{ ruta: '/perfil', nombre: 'Perfil', icono: 'user-round' },
	];

	const cliente = $derived(auth.cliente);
</script>

{#if auth.autenticado}
	<div class="flex min-h-dvh flex-col bg-gray-100">
		{#if sinConexion}
			<div class="flex items-center justify-center gap-2 bg-amber-500 px-4 py-2 text-center text-[13px] font-semibold text-white" role="alert">
				<Icon name="alert-triangle" clase="h-4 w-4 shrink-0" />
				Sin conexión — tus datos cargados siguen visibles
			</div>
		{/if}
		<!-- Nav superior (desktop): ocupa todo el ancho como una web real -->
		<header class="sticky top-0 z-40 hidden h-14 shrink-0 bg-navy text-white shadow-md lg:block">
			<div class="mx-auto flex h-full w-full items-center gap-6 px-6">
				<a href="/billetera" class="flex shrink-0 items-center gap-2">
					<img src={logo} alt="YAPAI" class="h-8 rounded-md bg-white px-1.5 py-0.5" />
				</a>
				<nav class="flex items-center gap-1">
					{#each tabs as t}
						{@const activo = page.url.pathname.startsWith(t.ruta)}
						<a href={t.ruta}
							class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors
								{activo ? 'bg-white/15 text-white' : 'text-white/60 hover:bg-white/10 hover:text-white'}">
							<Icon name={t.icono} clase="h-4 w-4" />
							{t.nombre}
						</a>
					{/each}
				</nav>
				<a href="/perfil" class="ml-auto flex items-center gap-2.5 rounded-lg py-1 pl-1 pr-2 hover:bg-white/10">
					<span class="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full bg-white/15 text-xs font-bold">
						{#if cliente?.foto_url}
							<img src={cloudinaryThumb(cliente.foto_url, 80)} alt="" class="h-full w-full object-cover" />
						{:else}
							{iniciales(cliente?.nombre)}
						{/if}
					</span>
					<span class="max-w-40 truncate text-sm font-medium">{cliente?.nombre ?? ''}</span>
				</a>
			</div>
		</header>

		<!-- Nav superior (móvil): tabs arriba, debajo del header de marca -->
		<nav class="sticky top-0 z-40 shrink-0 border-b border-gray-200 bg-white lg:hidden">
			<div class="mx-auto grid w-full max-w-md grid-cols-4">
				{#each tabs as t}
					{@const activo = page.url.pathname.startsWith(t.ruta)}
					<a href={t.ruta}
						class="flex flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium transition-colors
							{activo ? 'border-b-2 border-indigo-600 text-indigo-600' : 'border-b-2 border-transparent text-gray-500 hover:text-gray-700'}">
						<Icon name={t.icono} clase="h-6 w-6" />
						{t.nombre}
					</a>
				{/each}
			</div>
		</nav>

		<main class="flex min-h-0 flex-1 flex-col">
			{@render children()}
		</main>
	</div>
{:else}
	<div class="flex min-h-dvh items-center justify-center bg-gray-100">
		<div class="h-8 w-8 animate-spin rounded-full border-[3px] border-indigo-200 border-t-indigo-600"></div>
	</div>
{/if}
