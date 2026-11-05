<script lang="ts">
	let { titulo, valor, subtitulo = '', color = 'indigo' }: {
		titulo: string;
		valor: string | number;
		subtitulo?: string;
		color?: 'indigo' | 'green' | 'amber' | 'red' | 'sky';
	} = $props();

	const colores: Record<string, string> = {
		indigo: 'bg-indigo-50 text-indigo-600',
		green: 'bg-green-50 text-green-600',
		amber: 'bg-amber-50 text-amber-600',
		red: 'bg-red-50 text-red-600',
		sky: 'bg-sky-50 text-sky-600'
	};
</script>

<div class="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm sm:p-5">
	<p class="text-xs font-medium text-slate-500 sm:text-sm">{titulo}</p>
	<p class="mt-1.5 text-xl font-bold {colores[color].split(' ')[1]} sm:mt-2 sm:text-3xl">{valor}</p>
	{#if subtitulo}
		<p class="mt-1 text-[11px] text-slate-400 sm:text-xs">{subtitulo}</p>
	{/if}
</div>
