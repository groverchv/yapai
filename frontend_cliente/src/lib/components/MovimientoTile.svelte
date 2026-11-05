<script lang="ts">
	import type { Movimiento } from '../types';
	import Icon from './ui/Icon.svelte';

	const TIPOS: Record<string, string> = {
		registro: 'Registro en local',
		ruleta: 'Ruleta',
		bonus_manual: 'Bono por compra',
		referido: 'Bono por referido',
		canje: 'Canje de premio',
		congelar: 'Puntos congelados',
		liberar: 'Puntos liberados',
		anulacion: 'Anulación',
	};

	let { movimiento, fechaTxt }: { movimiento: Movimiento; fechaTxt: string } = $props();
	const positivo = $derived(movimiento.puntos >= 0);
	const subtitulo = $derived(
		[movimiento.comercio, movimiento.sucursal, fechaTxt].filter(Boolean).join(' · ')
	);
</script>

<div class="mb-2 flex items-center gap-3 rounded-xl bg-white p-3 shadow-sm ring-1 ring-black/5">
	<span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full
		{positivo ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}">
		<Icon name={positivo ? 'plus' : 'minus'} clase="h-5 w-5" />
	</span>
	<div class="min-w-0 flex-1">
		<p class="text-sm font-medium">{TIPOS[movimiento.tipo] ?? movimiento.tipo}</p>
		<p class="truncate text-xs text-gray-500">{subtitulo}</p>
	</div>
	<span class="shrink-0 text-base font-bold {positivo ? 'text-green-700' : 'text-red-700'}">
		{positivo ? '+' : ''}{movimiento.puntos}
	</span>
</div>
