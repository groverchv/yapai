<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import Sidebar from '#lib/components/layout/Sidebar.svelte';
	import Topbar from '#lib/components/layout/Topbar.svelte';
	import { auth } from '#lib/stores/auth.svelte';
	import type { LayoutProps } from './$types';
	import type { Perfil, UsuarioMe } from '#lib/types';

	let { children }: LayoutProps = $props();
	let verificado = $state(false);
	let menuAbierto = $state(false);

	const titulos: [RegExp, string][] = [
		[/^\/dashboard/, 'Dashboard'],
		[/^\/transacciones/, 'Historial de Transacciones'],
		[/^\/premios/, 'Catálogo de Premios'],
		[/^\/ruleta/, 'Ruleta de Premios'],
		[/^\/sucursales/, 'Sucursales y Pantallas'],
		[/^\/empleados/, 'Gestión de Empleados'],
		[/^\/accesos/, 'PIN de Caja'],
		[/^\/perfil/, 'Mi Perfil']
	];

	let titulo = $derived(
		titulos.find(([re]) => re.test(page.url.pathname))?.[1] ?? 'YAPAI Socio'
	);

	onMount(async () => {
		if (!auth.autenticado) {
			goto('/login');
			return;
		}
		try {
			const me = await api.get<{ tipo: string; usuario: UsuarioMe }>('/auth/me');
			if (me.tipo !== 'usuario' || me.usuario.rol !== 'owner') {
				throw new Error('sin permisos');
			}
			try {
				const p = await api.get<Perfil>('/socio/perfil');
				me.usuario.tenant_nombre = p.tenant_nombre;
				me.usuario.tenant_logo = p.logo_url;
			} catch (e) {
				console.warn('No se pudo cargar perfil del socio:', e);
			}
			auth.actualizarUsuario(me.usuario);
			verificado = true;
		} catch {
			if (auth.usuario?.rol === 'cajero') {
				goto('/terminal');
				return;
			}
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
