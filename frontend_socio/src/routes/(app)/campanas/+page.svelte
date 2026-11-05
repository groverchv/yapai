<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { onMount } from 'svelte';
	import { api, ApiError } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import { toast } from '#lib/stores/toast.svelte';
	import { API_BASE } from '#lib/api/client';
	import { auth } from '#lib/stores/auth.svelte';
	import type { Campana, Inactivo, Sucursal } from '#lib/types';
	import { formatFecha } from '#lib/utils/format';

	let campanas = $state<Campana[]>([]);
	let sucursales = $state<Sucursal[]>([]);
	let cargando = $state(true);

	// --- form campaña ---
	let modal = $state(false);
	let editando = $state<Campana | null>(null);
	let formNombre = $state('');
	let formMultiplicador = $state(2);
	let formInicio = $state('');
	let formFin = $state('');
	let formSucursal = $state('');
	let guardando = $state(false);
	let errorModal = $state('');

	// --- inactivos ---
	let dias = $state(30);
	let inactivos = $state<Inactivo[] | null>(null);
	let cargandoInactivos = $state(false);

	const columnasCampanas = [
		{ key: 'nombre', label: 'Campaña' },
		{ key: 'multiplicador', label: 'Mult.' },
		{ key: 'ventana', label: 'Ventana' },
		{ key: 'sucursal_nombre', label: 'Sucursal' },
		{ key: 'estado', label: 'Estado' }
	];
	const columnasInactivos = [
		{ key: 'nombre', label: 'Cliente' },
		{ key: 'telefono', label: 'Teléfono' },
		{ key: 'ult_actividad', label: 'Última actividad' },
		{ key: 'dias_inactivo', label: 'Días inactivo' },
		{ key: 'saldo', label: 'Saldo pts' }
	];

	const aIso = (fechaHora: string) => new Date(fechaHora).toISOString();
	const aInput = (iso: string) => iso.slice(0, 16);

	async function cargar() {
		cargando = true;
		try {
			[campanas, sucursales] = await Promise.all([
				api.get<Campana[]>('/socio/campanas'),
				api.get<Sucursal[]>('/socio/sucursales').catch(() => [] as Sucursal[]),
			]);
		} finally {
			cargando = false;
		}
	}

	function abrirCrear() {
		editando = null;
		formNombre = '';
		formMultiplicador = 2;
		const ahora = new Date();
		formInicio = ahora.toISOString().slice(0, 16);
		formFin = new Date(ahora.getTime() + 7 * 86400000).toISOString().slice(0, 16);
		formSucursal = '';
		errorModal = '';
		modal = true;
	}

	function abrirEditar(c: Campana) {
		editando = c;
		formNombre = c.nombre;
		formMultiplicador = c.multiplicador;
		formInicio = aInput(c.inicio);
		formFin = aInput(c.fin);
		formSucursal = c.sucursal_id ? String(c.sucursal_id) : '';
		errorModal = '';
		modal = true;
	}

	async function guardar(e: SubmitEvent) {
		e.preventDefault();
		guardando = true;
		errorModal = '';
		try {
			const body = {
				nombre: formNombre,
				multiplicador: formMultiplicador,
				inicio: aIso(formInicio),
				fin: aIso(formFin),
				sucursal_id: formSucursal ? Number(formSucursal) : null,
			};
			if (editando) await api.patch(`/socio/campanas/${editando.id}`, body);
			else await api.post('/socio/campanas', { ...body, activa: true });
			toast.exito(editando ? 'Campaña actualizada' : 'Campaña creada');
			modal = false;
			cargar();
		} catch (err) {
			errorModal = err instanceof ApiError ? err.detail : 'Error al guardar';
		} finally {
			guardando = false;
		}
	}

	async function toggle(c: Campana) {
		try {
			await api.patch(`/socio/campanas/${c.id}`, { activa: !c.activa });
			cargar();
		} catch (err) {
			toast.error(err instanceof ApiError ? err.detail : 'Error');
		}
	}

	async function eliminar(c: Campana) {
		try {
			await api.delete(`/socio/campanas/${c.id}`);
			toast.exito('Campaña eliminada');
			cargar();
		} catch (err) {
			toast.error(err instanceof ApiError ? err.detail : 'Error');
		}
	}

	async function cargarInactivos() {
		cargandoInactivos = true;
		try {
			inactivos = await api.get(`/socio/campanas/inactivos?dias=${dias}`);
		} finally {
			cargandoInactivos = false;
		}
	}

	function exportarCsv() {
		// descarga con el token de sesión
		fetch(`${API_BASE}/socio/campanas/inactivos.csv?dias=${dias}`, {
			headers: { Authorization: `Bearer ${auth.accessToken}` }
		})
			.then((r) => r.blob())
			.then((blob) => {
				const a = document.createElement('a');
				a.href = URL.createObjectURL(blob);
				a.download = `inactivos_${dias}d.csv`;
				a.click();
			});
	}

	onMount(() => { cargar(); cargarInactivos(); });
	const input = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none';
</script>

<div class="space-y-8">
	<div>
		<div class="mb-4 flex flex-wrap items-center justify-between gap-3">
			<div>
				<h2 class="text-lg font-semibold text-slate-800">Campañas multiplicadoras</h2>
				<p class="text-sm text-slate-500">Duplica o triplica los puntos que tus clientes ganan en el kiosco (registro y ruleta).</p>
			</div>
			<button onclick={abrirCrear}
				class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">
				+ Nueva campaña
			</button>
		</div>

		<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
			<DataTable columnas={columnasCampanas} filas={campanas as unknown as Record<string, unknown>[]} {cargando}>
				{#snippet celda({ key, fila })}
					{@const c = fila as unknown as Campana}
					{#if key === 'multiplicador'}
						<span class="font-bold text-emerald-600">x{c.multiplicador}</span>
					{:else if key === 'ventana'}
						<span class="text-xs text-slate-500">{formatFecha(c.inicio)} → {formatFecha(c.fin)}</span>
					{:else if key === 'sucursal_nombre'}
						{c.sucursal_nombre ?? 'Todas'}
					{:else if key === 'estado'}
						{#if !c.activa}
							<Badge texto="pausada" variante="neutral" />
						{:else if c.vigente}
							<Badge texto="vigente" variante="ok" />
						{:else}
							<Badge texto="programada" variante="info" />
						{/if}
					{:else}{c[key as keyof Campana]}{/if}
				{/snippet}
				{#snippet acciones(fila)}
					{@const c = fila as unknown as Campana}
					<button onclick={() => abrirEditar(c)} class="text-xs font-medium text-emerald-600 hover:underline">Editar</button>
					<button onclick={() => toggle(c)} class="text-xs font-medium text-amber-600 hover:underline">
						{c.activa ? 'Pausar' : 'Activar'}
					</button>
					<button onclick={() => eliminar(c)} class="text-xs font-medium text-red-600 hover:underline">Eliminar</button>
				{/snippet}
			</DataTable>
		</div>
	</div>

	<div>
		<div class="mb-4 flex flex-wrap items-end justify-between gap-3">
			<div>
				<h2 class="text-lg font-semibold text-slate-800">Clientes inactivos</h2>
				<p class="text-sm text-slate-500">Reactiva a quienes no vuelven — contáctalos por WhatsApp con su teléfono.</p>
			</div>
			<div class="flex items-end gap-2">
				<div>
					<label for="di" class="mb-1 block text-xs font-medium text-slate-500">Sin actividad hace</label>
					<select id="di" bind:value={dias} onchange={cargarInactivos}
						class="rounded-lg border border-slate-300 px-3 py-2 text-sm">
						<option value={15}>15+ días</option>
						<option value={30}>30+ días</option>
						<option value={60}>60+ días</option>
						<option value={90}>90+ días</option>
					</select>
				</div>
				<button onclick={exportarCsv}
					class="flex items-center gap-1.5 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
					<Icon name="download" clase="h-4 w-4" /> Exportar CSV
				</button>
			</div>
		</div>

		{#if inactivos && inactivos.length > 0}
			<div class="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
				{inactivos.length} cliente(s) sin actividad hace más de {dias} días.
				Mensaje sugerido: <em>«¡Te extrañamos! Vuelve y gira la ruleta — tienes puntos esperándote.»</em>
			</div>
		{/if}

		<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
			<DataTable columnas={columnasInactivos} filas={(inactivos ?? []) as unknown as Record<string, unknown>[]} cargando={cargandoInactivos}>
				{#snippet celda({ key, fila })}
					{@const i = fila as unknown as Inactivo}
					{#if key === 'ult_actividad'}
						{formatFecha(i.ult_actividad)}
					{:else if key === 'dias_inactivo'}
						<Badge texto="{i.dias_inactivo} días" variante={i.dias_inactivo > 60 ? 'bad' : 'warn'} />
					{:else}{i[key as keyof Inactivo]}{/if}
				{/snippet}
			</DataTable>
		</div>
	</div>
</div>

<Modal abierto={modal} titulo={editando ? 'Editar campaña' : 'Nueva campaña'} onclose={() => (modal = false)}>
	<form onsubmit={guardar} class="space-y-4">
		<div>
			<label for="cn" class="mb-1 block text-sm font-medium text-slate-700">Nombre</label>
			<input id="cn" type="text" bind:value={formNombre} required minlength="2"
				placeholder="Ej: x2 Fin de semana" class={input} />
		</div>
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
			<div>
				<label for="cm" class="mb-1 block text-sm font-medium text-slate-700">Multiplicador</label>
				<select id="cm" bind:value={formMultiplicador} class={input}>
					{#each [2, 3, 4, 5] as m}<option value={m}>x{m}</option>{/each}
				</select>
			</div>
			<div>
				<label for="cs" class="mb-1 block text-sm font-medium text-slate-700">Sucursal</label>
				<select id="cs" bind:value={formSucursal} class={input}>
					<option value="">Todas</option>
					{#each sucursales as s}<option value={s.id}>{s.nombre}</option>{/each}
				</select>
			</div>
		</div>
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
			<div>
				<label for="ci" class="mb-1 block text-sm font-medium text-slate-700">Inicio</label>
				<input id="ci" type="datetime-local" bind:value={formInicio} required class={input} />
			</div>
			<div>
				<label for="cf" class="mb-1 block text-sm font-medium text-slate-700">Fin</label>
				<input id="cf" type="datetime-local" bind:value={formFin} required class={input} />
			</div>
		</div>
		{#if errorModal}
			<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{errorModal}</p>
		{/if}
		<button type="submit" disabled={guardando}
			class="w-full rounded-lg bg-emerald-600 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
			{guardando ? 'Guardando…' : editando ? 'Guardar cambios' : 'Crear campaña'}
		</button>
	</form>
</Modal>
