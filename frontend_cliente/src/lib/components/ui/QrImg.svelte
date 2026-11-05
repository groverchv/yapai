<script lang="ts">
	import QRCode from 'qrcode';
	import { onMount } from 'svelte';

	let { data, size = 240, color = '#000000' }: { data: string; size?: number; color?: string } = $props();
	let src = $state('');

	async function generar() {
		try {
			src = await QRCode.toDataURL(data, {
				width: size * 2,
				margin: 1,
				color: { dark: color, light: '#ffffff' },
			});
		} catch {
			src = '';
		}
	}

	onMount(generar);
	$effect(() => { if (data) generar(); });
</script>

{#if src}
	<img {src} alt="Código QR" width={size} height={size} class="block" />
{:else}
	<div class="flex items-center justify-center bg-gray-100" style:width="{size}px" style:height="{size}px">
		<span class="text-xs text-gray-400">QR</span>
	</div>
{/if}
