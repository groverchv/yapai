<script lang="ts">
	import '../app.css';
	import ToastHost from '#lib/components/ui/ToastHost.svelte';
	import { pwa } from '#lib/stores/pwa.svelte';
	import { onMount } from 'svelte';

	let { children } = $props();
	onMount(() => pwa.registrar());
</script>

{@render children()}
<ToastHost />
