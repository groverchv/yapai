<script lang="ts">
	import type { Pase } from '../types';
	import { fecha } from '../utils/format';
	import Icon from './ui/Icon.svelte';

	const COLORES: Record<string, string> = {
		activo: 'text-green-600',
		canjeado: 'text-blue-600',
		cancelado: 'text-gray-500',
		expirado: 'text-orange-500',
	};
	const FONDOS: Record<string, string> = {
		activo: 'bg-green-50',
		canjeado: 'bg-blue-50',
		cancelado: 'bg-gray-100',
		expirado: 'bg-orange-50',
	};

	let { pase, onTap }: { pase: Pase; onTap: () => void } = $props();
	const color = $derived(COLORES[pase.estado] ?? 'text-orange-500');
	const fondo = $derived(FONDOS[pase.estado] ?? 'bg-orange-50');
</script>

<button onclick={onTap}
	class="mb-2.5 flex w-full items-center gap-3 rounded-xl bg-white p-3.5 text-left shadow-sm ring-1 ring-black/5 transition-shadow hover:shadow">
	<Icon name="qr-code" clase="h-9 w-9 shrink-0 {color}" />
	<div class="min-w-0 flex-1">
		<p class="text-sm font-bold">{pase.premio_nombre}</p>
		<p class="text-xs text-gray-500">{pase.comercio} · {pase.puntos} pts · PIN {pase.pin_corto}</p>
		{#if pase.estado === 'activo' && pase.expira_en}
			<p class="text-xs text-gray-500">Vence {fecha(pase.expira_en)}</p>
		{/if}
	</div>
	<span class="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium capitalize {fondo} {color}">
		{pase.estado}
	</span>
</button>
