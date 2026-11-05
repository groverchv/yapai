<script lang="ts">
	import type { Cliente, Wallet } from '../types';
	import { cloudinaryThumb, iniciales } from '../utils/format';
	import Icon from './ui/Icon.svelte';
	import Spinner from './ui/Spinner.svelte';

	let {
		cliente,
		wallet,
		subiendoFoto = false,
		onQr = null,
		onAvatar = null,
		onHistorial = null,
	}: {
		cliente: Cliente | null;
		wallet: Wallet | null;
		subiendoFoto?: boolean;
		onQr?: (() => void) | null;
		onAvatar?: (() => void) | null;
		onHistorial?: (() => void) | null;
	} = $props();
</script>

<div class="rounded-[20px] bg-gradient-to-br from-navy to-navy-claro p-5 text-white shadow-lg shadow-navy/40">
	<div class="flex items-center">
		<button onclick={onAvatar} class="relative shrink-0" aria-label="Cambiar foto">
			<div class="flex h-[52px] w-[52px] items-center justify-center overflow-hidden rounded-full bg-white/20">
				{#if subiendoFoto}
					<Spinner clase="h-6 w-6" />
				{:else if cliente?.foto_url}
					<img src={cloudinaryThumb(cliente.foto_url, 120)} alt="" class="h-full w-full object-cover" />
				{:else}
					<span class="text-xl font-bold">{iniciales(cliente?.nombre)}</span>
				{/if}
			</div>
			<span class="absolute -bottom-0.5 -right-0.5 rounded-full bg-white p-[3px] text-navy shadow">
				<Icon name="camera" clase="h-3 w-3" />
			</span>
		</button>
		<div class="ml-3.5 min-w-0 flex-1">
			<p class="truncate text-[17px] font-bold">{cliente?.nombre ?? '—'}</p>
			<p class="mt-0.5 text-[13px] text-white/70">CI {cliente?.ci ?? '—'}</p>
		</div>
		<Icon name="shield" clase="h-7 w-7 text-white/30" />
	</div>

	<div class="my-4 h-px bg-white/20"></div>

	<div class="flex items-end">
		<div class="flex-1">
			<p class="text-[11px] tracking-[1.2px] text-white/60">PUNTOS DISPONIBLES</p>
			<p class="mt-1 text-4xl font-bold leading-none">{wallet?.disponible ?? '—'}</p>
			{#if wallet && wallet.congelado > 0}
				<p class="mt-1.5 text-[11px] text-white/70">{wallet.congelado} pts congelados en pases</p>
			{/if}
		</div>
		<div class="flex flex-col gap-2">
			<button onclick={onQr} aria-label="Mi código" title="Mi código"
				class="rounded-xl bg-white p-2.5 text-navy transition-transform hover:scale-105">
				<Icon name="qr-code" clase="h-[26px] w-[26px]" />
			</button>
			<button onclick={onHistorial} aria-label="Historial" title="Historial"
				class="rounded-xl bg-white p-2.5 text-navy transition-transform hover:scale-105">
				<Icon name="receipt" clase="h-[26px] w-[26px]" />
			</button>
		</div>
	</div>
</div>
