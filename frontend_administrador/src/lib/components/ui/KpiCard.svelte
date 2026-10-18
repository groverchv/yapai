<script lang="ts">
	import Icon from './Icon.svelte';

	let { titulo, valor, subtitulo = '', color = 'indigo', icono = '', href = '' }: {
		titulo: string;
		valor: string | number;
		subtitulo?: string;
		color?: 'indigo' | 'green' | 'amber' | 'red' | 'sky' | 'purple' | 'emerald';
		icono?: string;
		href?: string;
	} = $props();

	const estilos: Record<string, { bg: string; text: string; iconBg: string }> = {
		indigo: { bg: 'bg-indigo-50/50', text: 'text-indigo-600', iconBg: 'bg-indigo-100 text-indigo-700' },
		green: { bg: 'bg-emerald-50/50', text: 'text-emerald-600', iconBg: 'bg-emerald-100 text-emerald-700' },
		emerald: { bg: 'bg-emerald-50/50', text: 'text-emerald-600', iconBg: 'bg-emerald-100 text-emerald-700' },
		amber: { bg: 'bg-amber-50/50', text: 'text-amber-600', iconBg: 'bg-amber-100 text-amber-700' },
		red: { bg: 'bg-rose-50/50', text: 'text-rose-600', iconBg: 'bg-rose-100 text-rose-700' },
		sky: { bg: 'bg-sky-50/50', text: 'text-sky-600', iconBg: 'bg-sky-100 text-sky-700' },
		purple: { bg: 'bg-purple-50/50', text: 'text-purple-600', iconBg: 'bg-purple-100 text-purple-700' }
	};

	const config = $derived(estilos[color] ?? estilos.indigo);
</script>

{#snippet contenido()}
	<div class="flex items-start justify-between">
		<span class="text-xs font-semibold uppercase tracking-wider text-slate-500">{titulo}</span>
		{#if icono}
			<div class="flex h-9 w-9 items-center justify-center rounded-lg {config.iconBg}">
				<Icon name={icono} clase="h-5 w-5" />
			</div>
		{/if}
	</div>
	<p class="mt-2 text-2xl font-bold {config.text} tracking-tight sm:text-3xl">{valor}</p>
	{#if subtitulo}
		<p class="mt-1 text-xs text-slate-500 flex items-center gap-1 font-medium">{subtitulo}</p>
	{/if}
{/snippet}

{#if href}
	<a {href} class="group block rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow-md">
		{@render contenido()}
	</a>
{:else}
	<div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
		{@render contenido()}
	</div>
{/if}

