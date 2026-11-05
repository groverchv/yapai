<script lang="ts" generics="T extends Record<string, unknown>">
	import type { Snippet } from 'svelte';

	let { columnas, filas, cargando = false, celda, acciones }: {
		columnas: { key: string; label: string }[];
		filas: T[];
		cargando?: boolean;
		celda?: Snippet<[{ key: string; fila: T }]>;
		acciones?: Snippet<[T]>;
	} = $props();

	let colspan = $derived(columnas.length + (acciones ? 1 : 0));
</script>

<div class="overflow-x-auto">
	<table class="w-full text-left text-sm">
		<thead>
			<tr class="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
				{#each columnas as col}
					<th class="px-4 py-3 font-semibold">{col.label}</th>
				{/each}
				{#if acciones}<th class="px-4 py-3 font-semibold text-right">Acciones</th>{/if}
			</tr>
		</thead>
		<tbody>
			{#if cargando}
				{#each [1, 2, 3, 4, 5] as _}
					<tr class="border-b border-slate-100">
						{#each columnas as col}
							<td class="px-4 py-3"><div class="h-4 animate-pulse rounded bg-slate-200"></div></td>
						{/each}
						{#if acciones}<td class="px-4 py-3"><div class="ml-auto h-4 w-16 animate-pulse rounded bg-slate-200"></div></td>{/if}
					</tr>
				{/each}
			{:else if filas.length === 0}
				<tr><td colspan={colspan} class="px-4 py-10 text-center text-slate-500">Sin resultados</td></tr>
			{:else}
				{#each filas as fila}
					<tr class="border-b border-slate-100 hover:bg-slate-50">
						{#each columnas as col}
							<td class="px-4 py-3 text-slate-700">
								{#if celda}
									{@render celda({ key: col.key, fila })}
								{:else}
									{fila[col.key] ?? '—'}
								{/if}
							</td>
						{/each}
						{#if acciones}<td class="px-4 py-3 text-right whitespace-nowrap">{@render acciones(fila)}</td>{/if}
					</tr>
				{/each}
			{/if}
		</tbody>
	</table>
</div>
