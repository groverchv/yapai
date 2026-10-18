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
