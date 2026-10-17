<script lang="ts">
	let { texto, variante = 'neutral' }: {
		texto: string;
		variante?: 'ok' | 'warn' | 'bad' | 'neutral' | 'info';
	} = $props();

	const estilos: Record<string, string> = {
		ok: 'bg-green-100 text-green-700',
		warn: 'bg-amber-100 text-amber-700',
		bad: 'bg-red-100 text-red-700',
		neutral: 'bg-slate-100 text-slate-600',
		info: 'bg-sky-100 text-sky-700'
	};
</script>

<span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold {estilos[variante]}">
	{texto}
</span>
