<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';

	/** Deep link de referido: /r/CODIGO → registro con código pre-llenado. */
	onMount(() => {
		const codigo = page.params.codigo?.toUpperCase() ?? '';
		if (codigo) sessionStorage.setItem('yapai_ref', codigo);
		goto('/login?registro=1', { replaceState: true });
	});
</script>

<div class="flex min-h-dvh items-center justify-center bg-gray-100">
	<div class="h-8 w-8 animate-spin rounded-full border-[3px] border-indigo-200 border-t-indigo-600"></div>
</div>
