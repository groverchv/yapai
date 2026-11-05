<script lang="ts">
	import type { Snippet } from 'svelte';
	import { goto } from '$app/navigation';
	import Icon from './ui/Icon.svelte';

	let {
		titulo,
		atras = null,
		accion = null,
	}: {
		titulo: string;
		atras?: string | null;
		accion?: Snippet | null;
	} = $props();
</script>

<header class="sticky top-0 z-30 flex h-14 items-center border-b border-gray-200/70 bg-white/95 px-2 backdrop-blur">
	<div class="w-10">
		{#if atras}
			<button onclick={() => (atras ? goto(atras) : history.back())} aria-label="Volver"
				class="flex h-9 w-9 items-center justify-center rounded-full text-gray-600 hover:bg-gray-100">
				<Icon name="arrow-left" clase="h-5 w-5" />
			</button>
		{/if}
	</div>
	<h1 class="flex-1 text-center text-base font-semibold text-gray-900">{titulo}</h1>
	<div class="flex w-10 justify-center">
		{#if accion}{@render accion()}{/if}
	</div>
</header>
