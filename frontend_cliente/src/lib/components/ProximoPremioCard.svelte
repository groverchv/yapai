<script lang="ts">
	import type { ProximoPremio } from '../types';
	import { cloudinaryThumb } from '../utils/format';
	import Icon from './ui/Icon.svelte';

	let { proximo, onTap }: { proximo: ProximoPremio; onTap: () => void } = $props();
	let fallo = $state(false);

	const progreso = $derived(
		proximo.costo_puntos > 0 ? Math.min(proximo.saldo / proximo.costo_puntos, 1) : 0
	);
</script>

<button onclick={onTap}
	class="flex w-full items-center gap-3 rounded-xl bg-white p-3 text-left shadow-sm ring-1 ring-black/5 transition-shadow hover:shadow">
	<div class="h-14 w-14 shrink-0 overflow-hidden rounded-[10px] bg-gray-200">
		{#if proximo.imagen_url && !fallo}
			<img src={cloudinaryThumb(proximo.imagen_url, 160)} alt="" class="h-full w-full object-cover"
				onerror={() => (fallo = true)} />
		{:else}
			<div class="flex h-full w-full items-center justify-center text-gray-400">
				<Icon name="gift" clase="h-6 w-6" />
			</div>
		{/if}
	</div>
	<div class="min-w-0 flex-1">
		<p class="text-[13px] font-bold leading-snug">
			{proximo.alcanzable
				? `¡Ya te alcanza para ${proximo.nombre}!`
				: `Te faltan ${proximo.faltante} pts para ${proximo.nombre}`}
		</p>
		<p class="mt-0.5 truncate text-xs text-gray-500">{proximo.comercio}</p>
		<div class="mt-2 h-[7px] overflow-hidden rounded bg-gray-200">
			<div class="h-full rounded transition-all {proximo.alcanzable ? 'bg-green-500' : 'bg-navy'}"
				style:width="{progreso * 100}%"></div>
		</div>
		<p class="mt-1 text-[11px] text-gray-400">{proximo.saldo} / {proximo.costo_puntos} pts</p>
	</div>
	<Icon name="chevron-right" clase="h-5 w-5 shrink-0 text-gray-400" />
</button>
