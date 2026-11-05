<script lang="ts">
	import type { Snippet } from 'svelte';
	import Icon from './Icon.svelte';

	let { abierto = false, titulo, onclose, children }: {
		abierto: boolean;
		titulo: string;
		onclose?: () => void;
		children: Snippet;
	} = $props();
</script>

<svelte:window onkeydown={(e) => abierto && e.key === 'Escape' && onclose?.()} />
{#if abierto}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
		role="presentation" onclick={(e) => e.target === e.currentTarget && onclose?.()}>
		<div class="flex max-h-[92dvh] w-full max-w-lg flex-col rounded-xl bg-white shadow-xl" role="dialog" aria-modal="true" aria-label={titulo}>
			<div class="flex shrink-0 items-center justify-between border-b border-slate-200 px-6 py-4">
				<h3 class="text-lg font-semibold text-slate-800">{titulo}</h3>
				<button onclick={() => onclose?.()}
					class="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-600" aria-label="Cerrar">
					<Icon name="x" clase="h-5 w-5" />
				</button>
			</div>
			<div class="overflow-y-auto px-6 py-4">
				{@render children()}
			</div>
		</div>
	</div>
{/if}
