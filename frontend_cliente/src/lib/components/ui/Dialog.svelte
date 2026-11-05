<script lang="ts">
	import type { Snippet } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	import Icon from './Icon.svelte';

	let {
		abierto = $bindable(false),
		titulo,
		texCancelar = 'Volver',
		texConfirmar = 'Aceptar',
		peligroso = false,
		onConfirmar,
		oncerrar = null,
		children,
	}: {
		abierto: boolean;
		titulo: string;
		texCancelar?: string;
		texConfirmar?: string;
		peligroso?: boolean;
		onConfirmar?: () => void;
		oncerrar?: (() => void) | null;
		children: Snippet;
	} = $props();

	function cerrar() {
		abierto = false;
		oncerrar?.();
	}
</script>

{#if abierto}
	<div class="fixed inset-0 z-[90] flex items-end sm:items-center justify-center p-4"
		role="dialog" aria-modal="true" aria-label={titulo}>
		<button transition:fade={{ duration: 150 }} onclick={cerrar} aria-label="Cerrar"
			class="absolute inset-0 bg-black/50"></button>
		<div transition:scale={{ start: 0.96, duration: 150 }}
			class="relative w-full max-w-sm rounded-2xl bg-white p-5 shadow-xl">
			<h3 class="text-lg font-semibold text-gray-900">{titulo}</h3>
			<div class="mt-2 text-sm text-gray-600">{@render children()}</div>
			<div class="mt-5 flex justify-end gap-2">
				<button onclick={cerrar}
					class="rounded-lg px-4 py-2 text-sm font-medium text-indigo-600 hover:bg-indigo-50">
					{texCancelar}
				</button>
				<button onclick={() => { onConfirmar?.(); cerrar(); }}
					class="rounded-lg px-4 py-2 text-sm font-semibold text-white {peligroso ? 'bg-red-600 hover:bg-red-700' : 'bg-indigo-600 hover:bg-indigo-700'}">
					{texConfirmar}
				</button>
			</div>
		</div>
	</div>
{/if}
