<script lang="ts">
	import type { Snippet } from 'svelte';
	import Spinner from './Spinner.svelte';

	/** Pull-to-refresh en dispositivos táctiles: arrastra desde el tope para recargar. */
	let {
		onRefresh,
		children,
	}: {
		onRefresh: () => Promise<void> | void;
		children: Snippet;
	} = $props();

	let contenedor: HTMLElement;
	let tirando = $state(false);
	let distancia = $state(0);
	let startY = 0;
	const UMBRAL = 70;

	function onTouchStart(e: TouchEvent) {
		if (contenedor.scrollTop === 0) {
			startY = e.touches[0].clientY;
			tirando = true;
		} else {
			tirando = false;
		}
	}

	function onTouchMove(e: TouchEvent) {
		if (!tirando) return;
		const dy = e.touches[0].clientY - startY;
		distancia = dy > 0 ? Math.min(dy * 0.5, 110) : 0;
	}

	async function onTouchEnd() {
		if (tirando && distancia >= UMBRAL) {
			distancia = 48;
			await onRefresh();
		}
		tirando = false;
		distancia = 0;
	}
</script>

<div bind:this={contenedor} class="relative min-h-0 flex-1 overflow-y-auto" role="main"
	ontouchstart={onTouchStart} ontouchmove={onTouchMove} ontouchend={onTouchEnd}>
	<div class="pointer-events-none sticky top-0 z-10 flex justify-center transition-[height] duration-150"
		style:height="{distancia}px" style:margin-bottom="{-distancia}px" aria-hidden="true">
		{#if distancia > 8}
			<div class="flex items-center pt-2 text-indigo-600">
				<Spinner clase="h-6 w-6" />
			</div>
		{/if}
	</div>
	{@render children()}
</div>
