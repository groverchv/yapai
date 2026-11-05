<script lang="ts">
	import { onMount } from 'svelte';
	import { api, ApiError } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import type { PlanOut } from '#lib/types';
	import { formatDinero } from '#lib/utils/format';

	let items = $state<PlanOut[]>([]);
	let cargando = $state(false);
	let mensaje = $state('');
	let modal = $state<PlanOut | 'nuevo' | null>(null);
	let f = $state({
		slug: '', nombre: '', descripcion: '', precio_mensual: 0, moneda: 'BOB',
		max_sucursales: 0, max_pantallas: 0, max_clientes: 0, max_empleados: 0,
		ruleta_habilitada: true, orden: 0
	});

	const columnas = [
		{ key: 'nombre', label: 'Plan' },
		{ key: 'precio_mensual', label: 'Precio' },
		{ key: 'max_sucursales', label: 'Sucursales' },
		{ key: 'max_pantallas', label: 'Pantallas' },
		{ key: 'max_clientes', label: 'Clientes' },
		{ key: 'max_empleados', label: 'Empleados' },
		{ key: 'ruleta_habilitada', label: 'Ruleta' },
		{ key: 'tenants_asignados', label: 'Socios' },
		{ key: 'activo', label: 'Estado' }
	];

	const lim = (v: number) => (v === 0 ? '∞' : v);

	async function cargar() {
		cargando = true;
		try { items = await api.get('/admin/planes'); }
		finally { cargando = false; }
	}

	function abrirNuevo() {
		f = { slug: '', nombre: '', descripcion: '', precio_mensual: 0, moneda: 'BOB',
			max_sucursales: 0, max_pantallas: 0, max_clientes: 0, max_empleados: 0,
			ruleta_habilitada: true, orden: (items.length + 1) * 10 };
		modal = 'nuevo';
	}
	function abrirEditar(p: PlanOut) {
		f = { slug: p.slug, nombre: p.nombre, descripcion: p.descripcion ?? '',
			precio_mensual: p.precio_mensual, moneda: p.moneda,
			max_sucursales: p.max_sucursales, max_pantallas: p.max_pantallas,
			max_clientes: p.max_clientes, max_empleados: p.max_empleados,
			ruleta_habilitada: p.ruleta_habilitada, orden: p.orden };
		modal = p;
	}

	async function guardar() {
		try {
			if (modal === 'nuevo') {
				await api.post('/admin/planes', { ...f, descripcion: f.descripcion || null });
			} else if (modal) {
				const { slug: _s, ...body } = f;
				await api.patch(`/admin/planes/${modal.id}`, { ...body, descripcion: f.descripcion || null });
			}
			modal = null;
			mensaje = 'Plan guardado';
			cargar();
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error';
		}
	}

	async function toggle(p: PlanOut) {
		await api.patch(`/admin/planes/${p.id}`, { activo: !p.activo });
		cargar();
	}

	onMount(cargar);
	const input = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100 focus:border-indigo-500 focus:outline-none';
	const label = 'mb-1 block text-xs font-medium text-slate-500';
</script>

<div class="mb-4 flex flex-wrap items-center justify-between gap-3">
	{#if mensaje}<p class="rounded-lg bg-sky-50 px-4 py-2 text-sm text-sky-700">{mensaje}</p>{:else}<span></span>{/if}
	<button onclick={abrirNuevo}
		class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
		+ Nuevo plan
	</button>
</div>

<p class="mb-4 text-sm text-slate-500">
	Límite <strong>0 = ilimitado</strong>. Los planes inactivos no aparecen en la landing ni en el signup.
</p>

<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
	<DataTable {columnas} filas={items as unknown as Record<string, unknown>[]} {cargando}>
		{#snippet celda({ key, fila })}
			{@const p = fila as unknown as PlanOut}
			{#if key === 'nombre'}<span class="font-medium">{p.nombre}</span> <span class="text-xs text-slate-400">({p.slug})</span>
			{:else if key === 'precio_mensual'}{p.precio_mensual === 0 ? 'Gratis' : formatDinero(p.precio_mensual, p.moneda) + '/mes'}
			{:else if key.startsWith('max_')}{lim(p[key as keyof PlanOut] as number)}
			{:else if key === 'ruleta_habilitada'}<Badge texto={p.ruleta_habilitada ? 'sí' : 'no'} variante={p.ruleta_habilitada ? 'ok' : 'neutral'} />
			{:else if key === 'activo'}<Badge texto={p.activo ? 'activo' : 'inactivo'} variante={p.activo ? 'ok' : 'neutral'} />
			{:else}{p[key as keyof PlanOut]}{/if}
		{/snippet}
		{#snippet acciones(fila)}
			{@const p = fila as unknown as PlanOut}
			<button onclick={() => abrirEditar(p)} class="mr-2 text-xs font-medium text-indigo-600 hover:underline">Editar</button>
			<button onclick={() => toggle(p)} class="text-xs font-medium text-amber-600 hover:underline">
				{p.activo ? 'Desactivar' : 'Activar'}
			</button>
		{/snippet}
	</DataTable>
</div>

<Modal abierto={modal !== null} titulo={modal === 'nuevo' ? 'Nuevo plan' : `Editar ${modal?.nombre}`} onclose={() => (modal = null)}>
	<form onsubmit={(e) => { e.preventDefault(); guardar(); }} class="space-y-4">
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
			<div><span class={label}>Slug *</span>
				<input bind:value={f.slug} required disabled={modal !== 'nuevo'} pattern="[a-z0-9-]+" class={input} placeholder="starter" /></div>
			<div><span class={label}>Nombre *</span>
				<input bind:value={f.nombre} required class={input} /></div>
		</div>
		<div><span class={label}>Descripción</span>
			<input bind:value={f.descripcion} class={input} /></div>
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
			<div><span class={label}>Precio/mes</span>
				<input type="number" step="0.01" min="0" bind:value={f.precio_mensual} class={input} /></div>
			<div><span class={label}>Moneda</span>
				<input bind:value={f.moneda} maxlength="3" class={input} /></div>
			<div><span class={label}>Orden</span>
				<input type="number" bind:value={f.orden} class={input} /></div>
		</div>
		<fieldset class="rounded-lg border border-slate-200 p-3">
			<legend class="px-1 text-xs font-medium text-slate-500">Límites (0 = ilimitado)</legend>
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
				<div><span class={label}>Sucursales</span>
					<input type="number" min="0" bind:value={f.max_sucursales} class={input} /></div>
				<div><span class={label}>Pantallas</span>
					<input type="number" min="0" bind:value={f.max_pantallas} class={input} /></div>
				<div><span class={label}>Clientes</span>
					<input type="number" min="0" bind:value={f.max_clientes} class={input} /></div>
				<div><span class={label}>Empleados</span>
					<input type="number" min="0" bind:value={f.max_empleados} class={input} /></div>
			</div>
		</fieldset>
		<label class="flex items-center gap-2 text-sm text-slate-700">
			<input type="checkbox" bind:checked={f.ruleta_habilitada} class="h-4 w-4 rounded border-slate-300 text-emerald-600" />
			Incluye ruleta del kiosco
		</label>
		<div class="flex justify-end gap-2">
			<button type="button" onclick={() => (modal = null)} class="rounded-lg border border-slate-300 px-4 py-2 text-sm">Cancelar</button>
			<button type="submit" class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">Guardar</button>
		</div>
	</form>
</Modal>
