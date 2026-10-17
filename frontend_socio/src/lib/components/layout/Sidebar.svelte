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
				{ label: 'nav.campanas', href: '/campanas', icono: 'sparkles' }
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
	<div class="flex items-center gap-2 px-6 py-5">
		<div class="rounded-lg bg-white px-3 py-1.5">
			<img src="/logo.png" alt="YAPAI" class="h-6" />
		</div>
		<span class="rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold text-white">SOCIO</span>
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
