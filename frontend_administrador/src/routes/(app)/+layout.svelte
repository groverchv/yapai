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
	let menuAbierto = $state(false);

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
		<!-- Sidebar fija en desktop -->
		<div class="hidden lg:block">
			<Sidebar />
		</div>

		<!-- Drawer del menú en móvil/tablet -->
		{#if menuAbierto}
			<div class="fixed inset-0 z-40 lg:hidden">
				<button class="absolute inset-0 bg-slate-950/60" aria-label="Cerrar menú"
					onclick={() => (menuAbierto = false)}></button>
				<div class="absolute left-0 top-0 h-full shadow-2xl">
					<Sidebar onnavegar={() => (menuAbierto = false)} />
				</div>
			</div>
		{/if}

		<div class="flex min-w-0 flex-1 flex-col overflow-hidden">
			<Topbar {titulo} onmenu={() => (menuAbierto = true)} />
			<main class="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
				{@render children()}
			</main>
		</div>
	</div>
{:else}
	<div class="flex h-screen items-center justify-center bg-slate-100 text-slate-400">
		Verificando sesión…
	</div>
{/if}
