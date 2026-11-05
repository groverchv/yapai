<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { auth } from '#lib/stores/auth.svelte';

	onMount(() => {
		goto(auth.autenticado ? '/dashboard' : '/login');
	});
</script>

<div class="flex h-screen items-center justify-center text-slate-500">Redirigiendo…</div>
