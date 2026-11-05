<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, mensajeError } from '#lib/api/client';
	import type { Pase } from '#lib/types';
	import PaseCard from '#lib/components/PaseCard.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import Skeleton from '#lib/components/ui/Skeleton.svelte';
	import PullRefresh from '#lib/components/ui/PullRefresh.svelte';
	import { onMount } from 'svelte';

	let pases = $state<Pase[]>([]);
	let cargando = $state(true);
	let error = $state('');

	const ORDEN: Record<string, number> = { activo: 0, canjeado: 1, cancelado: 2, expirado: 3 };

	async function cargar() {
		cargando = true;
		error = '';
		try {
			const data = await api.get<Pase[]>('/cliente/pases');
			pases = [...data].sort(
				(a, b) => (ORDEN[a.estado] ?? 9) - (ORDEN[b.estado] ?? 9)
			);
		} catch (e) {
			error = mensajeError(e);
		} finally {
			cargando = false;
		}
	}

	onMount(cargar);
</script>


<PullRefresh onRefresh={cargar}>
	<div class="p-4 lg:w-full lg:p-8">
		{#if cargando}
			<div class="space-y-3 lg:grid lg:grid-cols-2 lg:gap-3 lg:space-y-0 xl:grid-cols-3" aria-busy="true">
				{#each { length: 4 } as _}
					<div class="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
						<Skeleton clase="h-4 w-2/3" />
						<Skeleton clase="mt-2 h-3 w-1/3" />
						<Skeleton clase="mt-4 h-3 w-1/2" />
					</div>
				{/each}
			</div>
		{:else if error}
			<div class="flex flex-col items-center gap-2 py-16">
				<p class="text-sm text-red-600">{error}</p>
				<button onclick={cargar} class="text-sm font-medium text-indigo-600 hover:underline">Reintentar</button>
			</div>
		{:else if pases.length === 0}
			<div class="flex flex-col items-center py-24 text-center">
				<Icon name="qr-code" clase="h-16 w-16 text-gray-300" />
				<p class="mt-4 text-sm text-gray-700">No tienes pases generados</p>
				<p class="text-sm text-gray-500">Canjea un premio desde Explorar</p>
			</div>
		{:else}
			<div class="lg:grid lg:grid-cols-2 lg:gap-3 xl:grid-cols-3">
				{#each pases as p (p.id)}
					<PaseCard pase={p} onTap={() => goto(`/pases/${p.id}`)} />
				{/each}
			</div>
		{/if}
	</div>
</PullRefresh>
