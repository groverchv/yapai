<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '#lib/stores/auth.svelte';
	import { onMount } from 'svelte';

	onMount(() => {
		goto(auth.autenticado ? '/billetera' : '/login', { replaceState: true });
	});
</script>

<div class="flex min-h-dvh items-center justify-center bg-gray-100">
	<div class="h-8 w-8 animate-spin rounded-full border-[3px] border-indigo-200 border-t-indigo-600"></div>
</div>
