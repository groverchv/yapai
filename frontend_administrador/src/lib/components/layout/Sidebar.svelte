<script lang="ts">
	import { page } from '$app/state';
	import { i18n } from '#lib/i18n.svelte';
	import { auth } from '../../stores/auth.svelte';
	import { pwa } from '../../stores/pwa.svelte';
	import { toast } from '../../stores/toast.svelte';
	import Icon from '../ui/Icon.svelte';

	// onnavegar: el layout cierra el drawer móvil al tocar un enlace
	let { onnavegar }: { onnavegar?: () => void } = $props();

	const secciones = [
		{
			titulo: 'nav.general',
			items: [{ label: 'nav.dashboard', href: '/dashboard', icono: 'layout-dashboard' }]
		},
		{
			titulo: 'nav.socios',
			items: [
				{ label: 'nav.listado_socios', href: '/socios', icono: 'building' },
				{ label: 'nav.nuevo_socio', href: '/socios/nuevo', icono: 'plus' }
			]
		},
		{
			titulo: 'nav.operacion',
			items: [
				{ label: 'nav.transacciones', href: '/monitoreo/transacciones', icono: 'trending-up' },
				{ label: 'nav.rendimiento', href: '/monitoreo/rendimiento', icono: 'target' },
				{ label: 'nav.liquidaciones', href: '/liquidaciones', icono: 'banknote' },
				{ label: 'nav.facturacion_saas', href: '/facturacion', icono: 'receipt' }
			]
		},
		{
			titulo: 'nav.configuracion',
			items: [
				{ label: 'nav.categorias', href: '/configuracion/categorias', icono: 'tag' },
				{ label: 'nav.esquemas', href: '/configuracion/esquemas', icono: 'percent' },
				{ label: 'nav.planes', href: '/configuracion/planes', icono: 'sparkles' }
			]
		},
		{
			titulo: 'nav.cuenta',
			items: [{ label: 'nav.perfil', href: '/perfil', icono: 'user-round' }]
		}
	];

	function activo(href: string): boolean {
		const p = page.url.pathname;
		if (href === '/socios') return p === '/socios' || (p.startsWith('/socios/') && p !== '/socios/nuevo');
		return p === href || p.startsWith(href + '/');
	}

	async function instalar() {
		const acepto = await pwa.instalar();
		if (!acepto && !pwa.instalada) {
			toast.info('Abre el menú del navegador y elige "Instalar app" o "Añadir a pantalla de inicio"');
		}
	}
</script>

<aside class="flex h-screen w-64 flex-col bg-indigo-950 text-slate-300">
	<div class="flex items-center gap-2 px-6 py-5">
		<div class="rounded-lg bg-white px-3 py-1.5">
			<img src="/logo.png" alt="YAPAI" class="h-6" />
		</div>
		<span class="rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold text-white">ADMIN</span>
	</div>

	<nav class="flex-1 space-y-5 overflow-y-auto px-3 py-2">
		{#each secciones as seccion}
			<div>
				<p class="px-3 pb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
					{i18n.t(seccion.titulo as never)}
				</p>
				{#each seccion.items as item}
					<a href={item.href} onclick={onnavegar}
						class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition
							{activo(item.href) ? 'bg-indigo-600 text-white' : 'hover:bg-indigo-900 hover:text-white'}">
						<Icon name={item.icono} clase="h-4 w-4 shrink-0" /> {i18n.t(item.label as never)}
					</a>
				{/each}
			</div>
		{/each}
	</nav>

	{#if !pwa.instalada}
		<div class="px-3 pb-2">
			<button onclick={instalar}
				class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-indigo-300 transition hover:bg-indigo-900 hover:text-white">
				<Icon name="download" clase="h-4 w-4 shrink-0" /> {i18n.t('nav.instalar')}
			</button>
		</div>
	{/if}

	<div class="border-t border-slate-800 px-4 py-4">
		<p class="truncate text-sm font-medium text-white">{auth.usuario?.nombre ?? '—'}</p>
		<p class="truncate text-xs text-slate-500">{auth.usuario?.email ?? ''}</p>
	</div>
</aside>
