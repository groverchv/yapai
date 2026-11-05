<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { goto } from '$app/navigation';
	import { api } from '../../api/client';
	import { i18n } from '#lib/i18n.svelte';
	import { auth } from '../../stores/auth.svelte';

	let { titulo, onmenu }: { titulo: string; onmenu?: () => void } = $props();

	async function logout() {
		if (auth.refreshToken) {
			await api.post('/auth/logout', { refresh_token: auth.refreshToken }).catch(() => {});
		}
		auth.limpiar();
		goto('/login');
	}
</script>

<header class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-4 sm:px-8">
	<div class="flex min-w-0 items-center gap-3">
		{#if onmenu}
			<button onclick={onmenu} aria-label="Abrir menú"
				class="rounded-lg border border-slate-300 p-1.5 text-slate-600 hover:bg-slate-50 lg:hidden">
				<Icon name="menu" clase="h-5 w-5" />
			</button>
		{/if}
		<h1 class="truncate text-xl font-semibold text-slate-800">{titulo}</h1>
	</div>
	<button onclick={logout}
		class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50">
		<Icon name="log-out" clase="mr-1 inline h-4 w-4 align-middle" />{i18n.t('accion.cerrar_sesion')}
	</button>
</header>
