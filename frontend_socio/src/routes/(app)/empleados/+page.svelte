<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import Pagination from '#lib/components/ui/Pagination.svelte';
	import { formatFecha } from '#lib/utils/format';
	import type { Empleado, Pagina, Sucursal } from '#lib/types';

	let datos = $state<Pagina<Empleado> | null>(null);
	let sucursales = $state<Sucursal[]>([]);
	let cargando = $state(false);
	let error = $state('');
	let mensaje = $state('');

	let q = $state('');
	let estado = $state('');
	let page = $state(1);

	let modalCrear = $state(false);
	let modalEditar = $state<Empleado | null>(null);
	let formNombre = $state('');
	let formEmail = $state('');
	let formSucursales = $state<number[]>([]);
	let guardando = $state(false);
	let errorModal = $state('');

	const columnas = [
		{ key: 'nombre', label: 'Nombre' },
		{ key: 'email', label: 'Correo' },
		{ key: 'sucursales', label: 'Sucursales' },
		{ key: 'estado', label: 'Estado' },
		{ key: 'ultimo_login', label: 'Último acceso' }
	];

	async function cargar(p = 1) {
		cargando = true;
		error = '';
		page = p;
		try {
			const params = new URLSearchParams({ page: String(p), size: '20' });
			if (q) params.set('q', q);
			if (estado) params.set('estado', estado);
			datos = await api.get<Pagina<Empleado>>(`/socio/empleados?${params}`);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cargar';
		} finally {
			cargando = false;
		}
	}

	function abrirCrear() {
		formNombre = '';
		formEmail = '';
		formSucursales = [];
		errorModal = '';
		modalCrear = true;
	}

	function abrirEditar(emp: Empleado) {
		formNombre = emp.nombre;
		formSucursales = sucursales
			.filter((s) => emp.sucursales.includes(s.nombre))
			.map((s) => s.id);
		errorModal = '';
		modalEditar = emp;
	}

	function toggleSucursal(id: number) {
		formSucursales = formSucursales.includes(id)
			? formSucursales.filter((x) => x !== id)
			: [...formSucursales, id];
	}

	async function crear(e: SubmitEvent) {
		e.preventDefault();
		guardando = true;
		errorModal = '';
		try {
			await api.post('/socio/empleados', {
				nombre: formNombre, email: formEmail, sucursal_ids: formSucursales
			});
			modalCrear = false;
			mensaje = 'Empleado creado. Se enviaron las credenciales por correo.';
			cargar();
		} catch (err) {
			errorModal = err instanceof Error ? err.message : 'Error al crear';
		} finally {
			guardando = false;
		}
	}

	async function editar(e: SubmitEvent) {
		e.preventDefault();
		if (!modalEditar) return;
		guardando = true;
		errorModal = '';
		try {
			await api.patch(`/socio/empleados/${modalEditar.id}`, {
				nombre: formNombre, sucursal_ids: formSucursales
			});
			modalEditar = null;
			cargar(page);
		} catch (err) {
			errorModal = err instanceof Error ? err.message : 'Error al guardar';
		} finally {
			guardando = false;
		}
	}

	async function accion(emp: Empleado, op: 'suspender' | 'reactivar' | 'reenviar') {
		error = '';
		mensaje = '';
		try {
			const res = await api.post<{ detail?: string }>(`/socio/empleados/${emp.id}/${op}`);
			if (op === 'reenviar') mensaje = res.detail ?? 'Credenciales reenviadas';
			cargar(page);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error';
		}
	}

	onMount(async () => {
		cargar();
		sucursales = await api.get<Sucursal[]>('/socio/sucursales').catch(() => []);
	});
</script>

<div class="space-y-4">
	<div class="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4">
		<div>
			<label for="q" class="mb-1 block text-xs font-medium text-slate-500">Buscar</label>
			<input id="q" type="text" bind:value={q} placeholder="Nombre o correo…"
				class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm" />
		</div>
		<div>
			<label for="est" class="mb-1 block text-xs font-medium text-slate-500">Estado</label>
			<select id="est" bind:value={estado} class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm">
				<option value="">Todos</option>
				<option value="activo">Activos</option>
				<option value="suspendido">Suspendidos</option>
			</select>
		</div>
		<button onclick={() => cargar(1)}
			class="rounded-lg bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-emerald-700">
			Filtrar
		</button>
		<div class="flex-1"></div>
		<button onclick={abrirCrear}
			class="rounded-lg bg-slate-900 px-4 py-1.5 text-sm font-semibold text-white hover:bg-slate-800">
			+ Nuevo empleado
		</button>
	</div>

	{#if error}
		<p class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
	{/if}
	{#if mensaje}
		<p class="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{mensaje}</p>
	{/if}

	<div class="rounded-xl border border-slate-200 bg-white">
		<DataTable {columnas} filas={(datos?.items ?? []) as unknown as Record<string, unknown>[]} {cargando}>
			{#snippet celda({ key, fila })}
				{@const emp = fila as unknown as Empleado}
				{#if key === 'sucursales'}
					{emp.sucursales.length > 0 ? emp.sucursales.join(', ') : '—'}
				{:else if key === 'estado'}
					<Badge texto={emp.estado === 'activo' ? 'Activo' : 'Suspendido'}
						variante={emp.estado === 'activo' ? 'ok' : 'bad'} />
					{#if emp.onboarding_pendiente}
						<Badge texto="Pendiente activación" variante="warn" />
					{/if}
				{:else if key === 'ultimo_login'}
					{formatFecha(emp.ultimo_login)}
				{:else}
					{emp[key as keyof Empleado] ?? '—'}
				{/if}
			{/snippet}
			{#snippet acciones(fila)}
				{@const emp = fila as unknown as Empleado}
				<div class="flex justify-end gap-2 text-xs">
					<button onclick={() => abrirEditar(emp)} class="text-emerald-600 hover:underline">Editar</button>
					<button onclick={() => accion(emp, 'reenviar')} class="text-sky-600 hover:underline">
						Reenviar credenciales
					</button>
					{#if emp.estado === 'activo'}
						<button onclick={() => accion(emp, 'suspender')} class="text-red-600 hover:underline">Suspender</button>
					{:else}
						<button onclick={() => accion(emp, 'reactivar')} class="text-green-600 hover:underline">Reactivar</button>
					{/if}
				</div>
			{/snippet}
		</DataTable>
		{#if datos}
			<Pagination total={datos.total} {page} size={datos.size} onchange={cargar} />
		{/if}
	</div>
</div>

<Modal abierto={modalCrear} titulo="Nuevo empleado (cajero)" onclose={() => (modalCrear = false)}>
	<form onsubmit={crear} class="space-y-4">
		<div>
			<label for="en" class="mb-1 block text-sm font-medium text-slate-700">Nombre completo</label>
			<input id="en" type="text" bind:value={formNombre} required minlength="2"
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
		</div>
		<div>
			<label for="ee" class="mb-1 block text-sm font-medium text-slate-700">Correo</label>
			<input id="ee" type="email" bind:value={formEmail} required
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
			<p class="mt-1 text-xs text-slate-400">Recibirá un correo para activar su cuenta.</p>
		</div>
		<fieldset>
			<legend class="mb-1 text-sm font-medium text-slate-700">Sucursales asignadas</legend>
			<div class="space-y-1">
				{#each sucursales.filter((s) => s.estado === 'activa') as s}
					<label class="flex items-center gap-2 text-sm text-slate-600">
						<input type="checkbox" checked={formSucursales.includes(s.id)}
							onchange={() => toggleSucursal(s.id)} class="rounded" />
						{s.nombre}
					</label>
				{:else}
					<p class="text-sm text-slate-400">No hay sucursales activas.</p>
				{/each}
			</div>
		</fieldset>
		{#if errorModal}
			<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{errorModal}</p>
		{/if}
		<button type="submit" disabled={guardando}
			class="w-full rounded-lg bg-emerald-600 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
			{guardando ? 'Creando…' : 'Crear empleado'}
		</button>
	</form>
</Modal>

<Modal abierto={modalEditar !== null} titulo="Editar empleado" onclose={() => (modalEditar = null)}>
	<form onsubmit={editar} class="space-y-4">
		<div>
			<label for="en2" class="mb-1 block text-sm font-medium text-slate-700">Nombre completo</label>
			<input id="en2" type="text" bind:value={formNombre} required minlength="2"
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
		</div>
		<fieldset>
			<legend class="mb-1 text-sm font-medium text-slate-700">Sucursales asignadas</legend>
			<div class="space-y-1">
				{#each sucursales.filter((s) => s.estado === 'activa') as s}
					<label class="flex items-center gap-2 text-sm text-slate-600">
						<input type="checkbox" checked={formSucursales.includes(s.id)}
							onchange={() => toggleSucursal(s.id)} class="rounded" />
						{s.nombre}
					</label>
				{/each}
			</div>
		</fieldset>
		{#if errorModal}
			<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{errorModal}</p>
		{/if}
		<button type="submit" disabled={guardando}
			class="w-full rounded-lg bg-emerald-600 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
			{guardando ? 'Guardando…' : 'Guardar cambios'}
		</button>
	</form>
</Modal>
