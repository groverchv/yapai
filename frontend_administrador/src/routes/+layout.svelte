<script lang="ts">
	import '../app.css';
	import ToastHost from '#lib/components/ui/ToastHost.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href="/favicon.png" />
	<title>YAPAI Admin</title>
</svelte:head>

{@render children()}
<ToastHost />
