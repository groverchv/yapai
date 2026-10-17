<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import Sidebar from '#lib/components/layout/Sidebar.svelte';
	import Topbar from '#lib/components/layout/Topbar.svelte';
	import { auth } from '#lib/stores/auth.svelte';
	import type { LayoutProps } from './$types';
	import type { UsuarioMe } from '#lib/types';

	let { children }: LayoutProps = $props();
	let verificado = $state(false);

	const titulos: [RegExp, string][] = [
		[/^\/dashboard/, 'Dashboard'],
		[/^\/socios\/nuevo/, 'Nuevo Socio'],
		[/^\/socios\/\d+/, 'Detalle de Socio'],
		[/^\/socios/, 'Gestión de Socios'],
		[/^\/monitoreo\/transacciones/, 'Monitor de Transacciones'],
		[/^\/monitoreo\/rendimiento/, 'Rendimiento por Socio'],
		[/^\/liquidaciones/, 'Liquidaciones Mensuales'],
		[/^\/configuracion\/categorias/, 'Categorías de Negocio'],
		[/^\/configuracion\/esquemas/, 'Esquemas de Comisión']
	];

	let titulo = $derived(
		titulos.find(([re]) => re.test(page.url.pathname))?.[1] ?? 'YAPAI Admin'
	);

	onMount(async () => {
		if (!auth.autenticado) {
			goto('/login');
			return;
		}
		try {
			const me = await api.get<{ tipo: string; usuario: UsuarioMe }>('/auth/me');
			if (me.tipo !== 'usuario' || me.usuario.rol !== 'superadmin') {
				throw new Error('sin permisos');
			}
			auth.usuario = me.usuario;
			verificado = true;
		} catch {
			auth.limpiar();
			goto('/login');
		}
	});
</script>

{#if verificado}
	<div class="flex h-screen bg-slate-100">
		<Sidebar />
		<div class="flex flex-1 flex-col overflow-hidden">
			<Topbar {titulo} />
			<main class="flex-1 overflow-y-auto p-8">
				{@render children()}
			</main>
		</div>
	</div>
{:else}
	<div class="flex h-screen items-center justify-center bg-slate-100 text-slate-400">
		Verificando sesión…
	</div>
{/if}
