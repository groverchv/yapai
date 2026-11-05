<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, mensajeError } from '#lib/api/client';
	import type { Categoria, Comercio } from '#lib/types';
	import ComercioCard from '#lib/components/ComercioCard.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import Skeleton from '#lib/components/ui/Skeleton.svelte';
	import PullRefresh from '#lib/components/ui/PullRefresh.svelte';
	import { onMount } from 'svelte';

	let comercios = $state<Comercio[]>([]);
	let categorias = $state<Categoria[]>([]);
	let busqueda = $state('');
	let categoriaId = $state<number | null>(null);
	let soloMios = $state(false);
	let cargando = $state(true);
	let error = $state('');

	const visibles = $derived(
		soloMios ? comercios.filter((c) => c.puntos_ganados > 0) : comercios
	);

	let timer: ReturnType<typeof setTimeout> | undefined;
	function buscar(v: string) {
		busqueda = v;
		clearTimeout(timer);
		timer = setTimeout(cargar, 350);
	}

	async function cargar() {
		cargando = true;
		error = '';
		try {
			const params = new URLSearchParams();
			if (busqueda) params.set('q', busqueda);
			if (categoriaId !== null) params.set('categoria_id', `${categoriaId}`);
			const qs = params.toString();
			const data = await api.get<Comercio[]>(`/cliente/comercios${qs ? `?${qs}` : ''}`);
			comercios = data;
			if (categorias.length === 0) {
				categorias = await api.get<Categoria[]>('/cliente/comercios/categorias');
			}
		} catch (e) {
			error = mensajeError(e);
		} finally {
			cargando = false;
		}
	}

	function elegirCategoria(id: number | null) {
		categoriaId = id;
		cargar();
	}

	onMount(cargar);
</script>


<PullRefresh onRefresh={cargar}>
	<div class="space-y-3 p-4 lg:w-full lg:space-y-4 lg:p-8">
		<label class="relative block">
			<Icon name="search" clase="pointer-events-none absolute left-3.5 top-3.5 h-5 w-5 text-gray-400" />
			<input type="search" placeholder="Buscar comercio…" value={busqueda}
				oninput={(e) => buscar((e.target as HTMLInputElement).value)}
				class="w-full rounded-xl border border-gray-200 bg-white py-3 pl-11 pr-4 text-sm shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
		</label>

		<div class="-mx-4 flex gap-2 overflow-x-auto px-4">
			<button onclick={() => (soloMios = !soloMios)}
				class="flex shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-2 text-[13px] font-medium transition-colors
					{soloMios ? 'border-indigo-600 bg-indigo-600 text-white' : 'border-gray-300 bg-white text-gray-700'}">
				<Icon name="star" clase="h-4 w-4" /> Mis comercios
			</button>
			<button onclick={() => elegirCategoria(null)}
				class="shrink-0 rounded-full border px-3.5 py-2 text-[13px] font-medium transition-colors
					{categoriaId === null ? 'border-indigo-600 bg-indigo-600 text-white' : 'border-gray-300 bg-white text-gray-700'}">
				Todas
			</button>
			{#each categorias as c (c.id)}
				<button onclick={() => elegirCategoria(c.id)}
					class="shrink-0 rounded-full border px-3.5 py-2 text-[13px] font-medium transition-colors
						{categoriaId === c.id ? 'border-indigo-600 bg-indigo-600 text-white' : 'border-gray-300 bg-white text-gray-700'}">
					{c.nombre}
				</button>
			{/each}
		</div>

		{#if cargando}
			<div class="grid grid-cols-[repeat(auto-fill,minmax(130px,1fr))] gap-2.5 lg:grid-cols-5 xl:grid-cols-6" aria-busy="true">
				{#each { length: 6 } as _}
					<div class="rounded-xl bg-white p-3 shadow-sm ring-1 ring-black/5">
						<Skeleton clase="mx-auto h-16 w-16 !rounded-full" />
						<Skeleton clase="mx-auto mt-2.5 h-3.5 w-3/4" />
						<Skeleton clase="mx-auto mt-1.5 h-2.5 w-1/2" />
					</div>
				{/each}
			</div>
		{:else if error}
			<div class="flex flex-col items-center gap-2 py-12">
				<p class="text-sm text-red-600">{error}</p>
				<button onclick={cargar} class="text-sm font-medium text-indigo-600 hover:underline">Reintentar</button>
			</div>
		{:else if visibles.length === 0}
			<p class="py-12 text-center text-sm text-gray-500">
				{soloMios ? 'Aún no tienes puntos en ningún comercio' : 'No hay comercios disponibles'}
			</p>
		{:else}
			<div class="grid grid-cols-[repeat(auto-fill,minmax(130px,1fr))] gap-2.5 lg:grid-cols-5 xl:grid-cols-6">
				{#each visibles as c (c.id)}
					<ComercioCard comercio={c} onTap={() => goto(`/comercio/${c.id}`)} />
				{/each}
			</div>
		{/if}
	</div>
</PullRefresh>
