<script lang="ts">
	import Icon from "./Icon.svelte";
	let { total, page, size, onchange }: {
		total: number;
		page: number;
		size: number;
		onchange: (page: number) => void;
	} = $props();

	let paginas = $derived(Math.max(1, Math.ceil(total / size)));
</script>

<div class="flex items-center justify-between border-t border-slate-200 px-4 py-3 text-sm">
	<p class="text-slate-500">{total} resultado(s) · página {page} de {paginas}</p>
	<div class="flex gap-2">
		<button disabled={page <= 1} onclick={() => onchange(page - 1)}
			class="rounded-lg border border-slate-300 px-3 py-1 disabled:opacity-40 hover:bg-slate-50">
			<Icon name="chevron-left" clase="inline h-4 w-4 align-middle" /> Anterior
		</button>
		<button disabled={page >= paginas} onclick={() => onchange(page + 1)}
			class="rounded-lg border border-slate-300 px-3 py-1 disabled:opacity-40 hover:bg-slate-50">
			Siguiente <Icon name="chevron-right" clase="inline h-4 w-4 align-middle" />
		</button>
	</div>
</div>
