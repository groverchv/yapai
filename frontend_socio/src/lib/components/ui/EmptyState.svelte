<script lang="ts">
	import Icon from './Icon.svelte';

	let {
		icono = 'info',
		titulo,
		descripcion = '',
		cta = '',
		oncta
	}: {
		icono?: string;
		titulo: string;
		descripcion?: string;
		cta?: string;
		oncta?: () => void;
	} = $props();
</script>

<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
	<div class="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
		<Icon name={icono} clase="h-6 w-6" />
	</div>
	<p class="mt-3 text-sm font-semibold text-slate-800">{titulo}</p>
	{#if descripcion}
		<p class="mt-1 max-w-sm text-sm text-slate-500">{descripcion}</p>
	{/if}
	{#if cta && oncta}
		<button onclick={oncta}
			class="mt-4 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700">
			{cta}
		</button>
	{/if}
</div>
