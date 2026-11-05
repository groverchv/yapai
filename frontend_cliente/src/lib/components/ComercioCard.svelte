<script lang="ts">
	import type { Comercio } from '../types';
	import { cloudinaryThumb } from '../utils/format';
	import Icon from './ui/Icon.svelte';

	let { comercio, onTap }: { comercio: Comercio; onTap: () => void } = $props();
	let fallo = $state(false);
</script>

<button onclick={onTap}
	class="flex w-full flex-col rounded-xl bg-white p-3 text-left shadow-sm ring-1 ring-black/5 transition-shadow hover:shadow">
	<div class="mx-auto h-16 w-16 overflow-hidden rounded-full bg-green-50">
		{#if comercio.logo_url && !fallo}
			<img src={cloudinaryThumb(comercio.logo_url, 160)} alt="" class="h-full w-full object-cover"
				onerror={() => (fallo = true)} />
		{:else}
			<div class="flex h-full w-full items-center justify-center text-green-600">
				<Icon name="store" clase="h-7 w-7" />
			</div>
		{/if}
	</div>
	<p class="mt-2.5 line-clamp-2 text-[13px] font-bold leading-snug">{comercio.nombre_comercial}</p>
	{#if comercio.puntos_ganados > 0}
		<span class="mt-1 w-fit rounded-md bg-green-50 px-1.5 py-0.5 text-[10px] font-semibold text-green-800">
			Ganaste {comercio.puntos_ganados} pts aquí
		</span>
	{/if}
	<div class="mt-auto flex items-center pt-2">
		<span class="flex-1 truncate text-[11px] text-gray-500">{comercio.categoria ?? 'Comercio'}</span>
		<Icon name="gift" clase="h-3 w-3 text-green-700" />
		<span class="ml-0.5 text-[11px] font-bold text-green-700">{comercio.total_premios}</span>
	</div>
</button>
