<script lang="ts">
	import '../app.css';
	import ToastHost from '#lib/components/ui/ToastHost.svelte';
	import { pwa } from '#lib/stores/pwa.svelte';
	import type { LayoutProps } from './$types';
	import { onMount } from 'svelte';

	let { children }: LayoutProps = $props();
	onMount(() => pwa.registrar());
</script>

<svelte:head>
	<link rel="icon" href="/favicon.png" />
	<title>YAPAI Socio</title>
</svelte:head>

{@render children()}
<ToastHost />
