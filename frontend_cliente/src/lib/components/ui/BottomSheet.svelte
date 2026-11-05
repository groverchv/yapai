<script lang="ts">
	import type { Snippet } from 'svelte';
	import { fade, fly } from 'svelte/transition';

	let {
		abierto = $bindable(false),
		altura = 'max-h-[85dvh]',
		oncerrar = null,
		children,
	}: {
		abierto: boolean;
		altura?: string;
		oncerrar?: (() => void) | null;
		children: Snippet;
	} = $props();

	function cerrar() {
		abierto = false;
		oncerrar?.();
	}
</script>

{#if abierto}
	<div class="fixed inset-0 z-[80]" role="dialog" aria-modal="true">
		<button transition:fade={{ duration: 150 }} onclick={cerrar} aria-label="Cerrar"
			class="absolute inset-0 bg-black/50"></button>
		<div transition:fly={{ y: 120, duration: 200 }}
			class="absolute bottom-0 left-1/2 w-full max-w-md -translate-x-1/2 rounded-t-3xl bg-gray-50 shadow-2xl {altura} flex flex-col
				sm:bottom-auto sm:top-1/2 sm:-translate-y-1/2 sm:rounded-3xl sm:max-h-[85vh]">
			<div class="mx-auto mt-3 h-1 w-10 shrink-0 rounded-full bg-gray-300"></div>
			<div class="min-h-0 flex-1 overflow-y-auto px-5 pb-8 pt-3">
				{@render children()}
			</div>
		</div>
	</div>
{/if}
