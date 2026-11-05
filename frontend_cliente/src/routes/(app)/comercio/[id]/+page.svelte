<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { api, mensajeError } from '#lib/api/client';
	import type { ComercioDetalle, Pase, Premio, SucursalInfo, Wallet } from '#lib/types';
	import AppTopBar from '#lib/components/AppTopBar.svelte';
	import PremioCard from '#lib/components/PremioCard.svelte';
	import Dialog from '#lib/components/ui/Dialog.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import Spinner from '#lib/components/ui/Spinner.svelte';
	import PullRefresh from '#lib/components/ui/PullRefresh.svelte';
	import { toast } from '#lib/stores/toast.svelte';
	import { cloudinaryThumb } from '#lib/utils/format';
	import { onMount } from 'svelte';

	const id = $derived(Number(page.params.id));

	let detalle = $state<ComercioDetalle | null>(null);
	let premios = $state<Premio[]>([]);
	let disponible = $state(0);
	let cargando = $state(true);
	let error = $state('');
	let confirmar = $state<Premio | null>(null);
	let canjeando = $state(false);
	let logoFallo = $state(false);

	const sucursales = $derived<SucursalInfo[]>(detalle?.sucursales ?? []);

	function urlMapa(s: SucursalInfo): string {
		const q = s.latitud != null && s.longitud != null
			? `${s.latitud},${s.longitud}`
			: `${s.nombre} ${s.direccion ?? ''}`.trim();
		return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`;
	}

	async function cargar() {
		cargando = true;
		error = '';
		try {
			const [d, p, w] = await Promise.all([
				api.get<ComercioDetalle>(`/cliente/comercios/${id}`),
				api.get<Premio[]>(`/cliente/comercios/${id}/premios`),
				api.get<Wallet>('/cliente/wallet'),
			]);
			detalle = d;
			premios = p;
			disponible = w.disponible;
		} catch (e) {
			error = mensajeError(e);
		} finally {
			cargando = false;
		}
	}

	async function canjear() {
		if (!confirmar) return;
		const p = confirmar;
		canjeando = true;
		try {
			const pase = await api.post<Pase>('/cliente/pases', { premio_id: p.id });
			toast.exito('Pase generado');
			goto(`/pases/${pase.id}`);
		} catch (e) {
			toast.error(mensajeError(e));
		} finally {
			canjeando = false;
		}
	}

	onMount(cargar);
</script>

<AppTopBar titulo={detalle?.nombre_comercial ?? 'Comercio'} atras="/explorar" />

{#if cargando}
	<div class="flex h-[60dvh] items-center justify-center text-indigo-600"><Spinner clase="h-8 w-8" /></div>
{:else if error}
	<div class="flex h-[60dvh] flex-col items-center justify-center gap-2">
		<p class="text-sm text-red-600">{error}</p>
		<button onclick={cargar} class="text-sm font-medium text-indigo-600 hover:underline">Reintentar</button>
	</div>
{:else}
	<PullRefresh onRefresh={cargar}>
		<div class="space-y-5 p-4 lg:w-full lg:space-y-6 lg:p-8">
			{#if detalle}
				<div class="flex items-center gap-4 rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
					<div class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-full bg-green-50">
						{#if detalle.logo_url && !logoFallo}
							<img src={cloudinaryThumb(detalle.logo_url, 160)} alt="" class="h-full w-full object-cover"
								onerror={() => (logoFallo = true)} />
						{:else}
							<Icon name="store" clase="h-7 w-7 text-green-600" />
						{/if}
					</div>
					<div class="min-w-0">
						<h1 class="truncate text-lg font-bold">{detalle.nombre_comercial}</h1>
						{#if detalle.categoria}
							<span class="mt-1 inline-block rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
								{detalle.categoria}
							</span>
						{/if}
					</div>
				</div>
			{/if}

			{#if sucursales.length > 0}
				<section>
					<h2 class="mb-2 text-base font-semibold">Dónde reclamar</h2>
					<div class="divide-y divide-gray-100 rounded-xl bg-white shadow-sm ring-1 ring-black/5">
						{#each sucursales as s (s.id)}
							<a href={urlMapa(s)} target="_blank" rel="noopener noreferrer"
								class="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-indigo-50/60">
								<Icon name="map-pin" clase="h-5 w-5 shrink-0 text-indigo-500" />
								<div class="min-w-0 flex-1">
									<p class="truncate text-sm font-medium">{s.nombre}</p>
									{#if s.direccion}<p class="truncate text-xs text-gray-500">{s.direccion}</p>{/if}
								</div>
								<span class="shrink-0 rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-semibold text-indigo-600">
									Cómo llegar
								</span>
							</a>
						{/each}
					</div>
				</section>
			{/if}

			<section>
				<h2 class="text-base font-semibold">Premios</h2>
				<div class="mx-auto mt-2 w-fit rounded-full bg-white px-4 py-1.5 text-sm font-medium shadow-sm ring-1 ring-black/5">
					<Icon name="star" clase="mr-1 inline h-4 w-4 text-amber-500" />
					Tu saldo: {disponible} pts
				</div>
				{#if premios.length === 0}
					<div class="mt-3 flex flex-col items-center gap-2 rounded-xl bg-white py-10 shadow-sm ring-1 ring-black/5">
						<Icon name="gift" clase="h-10 w-10 text-gray-300" />
						<p class="text-sm text-gray-500">Sin premios disponibles</p>
					</div>
				{:else}
					<div class="mt-3 grid grid-cols-[repeat(auto-fill,minmax(130px,1fr))] gap-2.5 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
						{#each premios as p (p.id)}
							<PremioCard premio={p} onCanjear={p.alcanzable ? () => (confirmar = p) : null} />
						{/each}
					</div>
				{/if}
			</section>
		</div>
	</PullRefresh>
{/if}

<Dialog abierto={confirmar !== null} titulo="Confirmar canje"
	texConfirmar={canjeando ? 'Generando…' : 'Generar pase'}
	oncerrar={() => (confirmar = null)}
	onConfirmar={canjear}>
	{#if confirmar}
		Vas a generar un pase para <strong>"{confirmar.nombre}"</strong> por
		<strong>{confirmar.costo_puntos} puntos</strong>.<br /><br />
		Los puntos quedarán congelados hasta que el cajero valide la entrega o canceles el pase.
	{/if}
</Dialog>
