<script lang="ts">
	import { page } from '$app/state';
	import { i18n } from '#lib/i18n.svelte';
	import { auth } from '../../stores/auth.svelte';
	import Icon from '../ui/Icon.svelte';

	const secciones = [
		{
			titulo: 'nav.general',
			items: [{ label: 'nav.dashboard', href: '/dashboard', icono: 'layout-dashboard' }]
		},
		{
			titulo: 'nav.operacion',
			items: [
				{ label: 'nav.transacciones', href: '/transacciones', icono: 'trending-up' },
				{ label: 'nav.premios', href: '/premios', icono: 'gift' },
				{ label: 'nav.ruleta', href: '/ruleta', icono: 'ruleta' },
				{ label: 'nav.campanas', href: '/campanas', icono: 'sparkles' },
				{ label: 'nav.comunicados', href: '/comunicados', icono: 'image-plus' }
			]
		},
		{
			titulo: 'nav.negocio',
			items: [
				{ label: 'nav.sucursales', href: '/sucursales', icono: 'store' },
				{ label: 'nav.empleados', href: '/empleados', icono: 'users' },
				{ label: 'nav.accesos', href: '/accesos', icono: 'key-round' }
			]
		},
		{
			titulo: 'nav.cuenta',
			items: [
				{ label: 'nav.perfil', href: '/perfil', icono: 'user-round' },
				{ label: 'nav.facturacion', href: '/facturacion', icono: 'receipt' }
			]
		}
	];

	function activo(href: string): boolean {
		const p = page.url.pathname;
		return p === href || p.startsWith(href + '/');
	}
</script>

<aside class="flex h-screen w-64 flex-col bg-indigo-950 text-slate-300">
	<!-- Identidad de la Empresa del Socio -->
	<div class="border-b border-indigo-900/60 bg-indigo-950/40 px-5 py-4">
		<div class="flex items-center gap-3">
			{#if auth.usuario?.tenant_logo}
				<div class="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-white p-1 shadow-md ring-2 ring-emerald-500/30">
					<img src={auth.usuario.tenant_logo} alt={auth.usuario?.tenant_nombre ?? 'Logo'}
						class="h-full w-full object-cover rounded-lg" />
				</div>
			{:else}
				<div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 text-white font-extrabold text-lg shadow-md ring-2 ring-white/10">
					{(auth.usuario?.tenant_nombre || 'S')[0].toUpperCase()}
				</div>
			{/if}
			<div class="min-w-0 flex-1">
				<p class="truncate text-sm font-bold text-white tracking-tight" title={auth.usuario?.tenant_nombre ?? 'Mi Comercio'}>
					{auth.usuario?.tenant_nombre || 'Mi Comercio'}
				</p>
				<div class="flex items-center gap-1.5 mt-0.5">
					<span class="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
					<span class="text-[10px] font-bold tracking-wider text-emerald-400 uppercase">
						SOCIO
					</span>
				</div>
			</div>
		</div>
	</div>

	<nav class="flex-1 space-y-5 overflow-y-auto px-3 py-2">
		{#each secciones as seccion}
			<div>
				<p class="px-3 pb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
					{i18n.t(seccion.titulo as never)}
				</p>
				{#each seccion.items as item}
					<a href={item.href}
						class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition
							{activo(item.href) ? 'bg-emerald-600 text-white' : 'hover:bg-indigo-900 hover:text-white'}">
						<Icon name={item.icono} clase="h-4 w-4 shrink-0" /> {i18n.t(item.label as never)}
					</a>
				{/each}
			</div>
		{/each}
	</nav>

	<div class="border-t border-slate-800 px-4 py-4">
		<p class="truncate text-sm font-medium text-white">{auth.usuario?.nombre ?? '—'}</p>
		<p class="truncate text-xs text-slate-500">{auth.usuario?.email ?? ''}</p>
	</div>
</aside>
