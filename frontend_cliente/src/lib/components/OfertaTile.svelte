<script lang="ts">
	import type { Comunicado } from '../types';
	import { cloudinaryThumb, esNueva } from '../utils/format';
	import Icon from './ui/Icon.svelte';
	import Spinner from './ui/Spinner.svelte';

	let { comunicado, onTap }: { comunicado: Comunicado; onTap: () => void } = $props();
	let cargada = $state(false);
	let fallo = $state(false);
</script>

<button onclick={onTap} class="relative aspect-square w-full overflow-hidden rounded-xl bg-gray-200 text-left">
	{#if fallo}
		<div class="flex h-full w-full items-center justify-center text-gray-400">
			<Icon name="image-off" clase="h-8 w-8" />
		</div>
	{:else}
		{#if !cargada}
			<div class="absolute inset-0 flex items-center justify-center text-gray-400">
				<Spinner clase="h-5 w-5" />
			</div>
		{/if}
		<img src={cloudinaryThumb(comunicado.imagen_url)} alt="" loading="lazy"
			class="h-full w-full object-cover {cargada ? '' : 'opacity-0'}"
			onload={() => (cargada = true)} onerror={() => (fallo = true)} />
	{/if}
	<div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 to-transparent px-2 pb-1.5 pt-4">
		<p class="line-clamp-2 text-[11px] font-semibold leading-tight text-white">{comunicado.titulo}</p>
	</div>
	{#if esNueva(comunicado.publicado_en)}
		<span class="absolute left-1.5 top-1.5 rounded-md bg-green-400 px-1.5 py-0.5 text-[9px] font-bold tracking-wide text-black/80">NUEVA</span>
	{/if}
</button>
