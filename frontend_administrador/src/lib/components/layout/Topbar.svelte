<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { goto } from '$app/navigation';
	import { api } from '../../api/client';
	import { i18n } from '#lib/i18n.svelte';
	import { auth } from '../../stores/auth.svelte';

	let { titulo }: { titulo: string } = $props();

	async function logout() {
		if (auth.refreshToken) {
			await api.post('/auth/logout', { refresh_token: auth.refreshToken }).catch(() => {});
		}
		auth.limpiar();
		goto('/login');
	}
</script>

<header class="flex items-center justify-between border-b border-slate-200 bg-white px-8 py-4">
	<h1 class="text-xl font-semibold text-slate-800">{titulo}</h1>
	<button onclick={logout}
		class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50">
		<Icon name="log-out" clase="mr-1 inline h-4 w-4 align-middle" />{i18n.t('accion.cerrar_sesion')}
	</button>
</header>
