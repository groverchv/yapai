<script lang="ts">
	import { toast } from '#lib/stores/toast.svelte';
	import { fly } from 'svelte/transition';
	import Icon from './Icon.svelte';

	const estilos: Record<string, string> = {
		exito: 'bg-emerald-700 text-white',
		error: 'bg-red-700 text-white',
		info: 'bg-indigo-700 text-white',
	};
	const iconos: Record<string, string> = { exito: 'check', error: 'x', info: 'info' };
</script>

<div class="pointer-events-none fixed bottom-24 sm:bottom-4 left-1/2 -translate-x-1/2 sm:left-auto sm:translate-x-0 sm:right-4 z-[100] flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2" role="status" aria-live="polite">
	{#each toast.lista as t (t.id)}
		<button transition:fly={{ y: 20, duration: 200 }} onclick={() => toast.quitar(t.id)}
			class="pointer-events-auto flex items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-medium shadow-lg {estilos[t.tipo]}">
			<span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/20 text-xs font-bold">
				<Icon name={iconos[t.tipo]} clase="h-3.5 w-3.5" />
			</span>
			<span class="flex-1">{t.texto}</span>
		</button>
	{/each}
</div>
