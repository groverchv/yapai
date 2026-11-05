<script lang="ts">
	import type { Premio } from '../types';
	import { cloudinaryThumb, vence } from '../utils/format';
	import Icon from './ui/Icon.svelte';

	let { premio, onCanjear = null }: { premio: Premio; onCanjear?: (() => void) | null } = $props();
	const bloqueado = $derived(!premio.alcanzable);
	let fallo = $state(false);
</script>

<div class="flex flex-col overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-black/5 {bloqueado ? 'opacity-55' : ''}">
	<div class="h-32 w-full shrink-0 bg-gray-200 sm:h-36 lg:h-40">
		{#if premio.imagen_url && !fallo}
			<img src={cloudinaryThumb(premio.imagen_url)} alt="" loading="lazy" class="block h-full w-full object-cover"
				onerror={() => (fallo = true)} />
		{:else}
			<div class="flex h-full w-full items-center justify-center text-gray-400">
				<Icon name="gift" clase="h-10 w-10" />
			</div>
		{/if}
	</div>
	<div class="flex flex-1 flex-col p-2">
		<p class="truncate text-sm font-bold">{premio.nombre}</p>
		<p class="text-sm font-bold text-green-700">{premio.costo_puntos} pts</p>
		{#if premio.vigencia_hasta}
			<p class="mt-0.5 text-[11px] text-orange-700">Vence {vence(premio.vigencia_hasta)}</p>
		{/if}
		<div class="mt-1.5 pt-1">
			{#if bloqueado}
				<span class="block w-full rounded-full bg-gray-100 py-1 text-center text-[11px] font-medium text-gray-500">
					Puntos insuficientes
				</span>
			{:else}
				<button onclick={onCanjear}
					class="w-full rounded-lg bg-indigo-50 py-1.5 text-sm font-semibold text-indigo-700 hover:bg-indigo-100">
					Canjear
				</button>
			{/if}
		</div>
	</div>
</div>
