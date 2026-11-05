<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { api, ApiError } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import KpiCard from '#lib/components/ui/KpiCard.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import Pagination from '#lib/components/ui/Pagination.svelte';
	import type {
		CategoriaOut, ClienteListItem, EsquemaOut, KpisSocio, Pagina,
		PlanOut, SocioDetalle, SucursalListItem, UsuarioListItem
	} from '#lib/types';
	import { formatFecha, formatFechaCorta } from '#lib/utils/format';

	import Icon from '#lib/components/ui/Icon.svelte';
	import { subirImagenCloudinary } from '#lib/utils/upload';

	const id = Number(page.params.id);

	let socio = $state<SocioDetalle | null>(null);
	let kpis = $state<KpisSocio | null>(null);
	let categorias = $state<CategoriaOut[]>([]);
	let esquemas = $state<EsquemaOut[]>([]);
	let planes = $state<PlanOut[]>([]);
	let planSel = $state<string>('');
	let guardandoPlan = $state(false);
	let subiendoLogo = $state(false);
	let tab = $state<'perfil' | 'usuarios' | 'sucursales' | 'clientes'>('perfil');
	let usuarios = $state<UsuarioListItem[]>([]);
	let sucursales = $state<SucursalListItem[]>([]);
	let clientes = $state<Pagina<ClienteListItem> | null>(null);
	let pageClientes = $state(1);
	let mensaje = $state('');
	let editando = $state(false);
	let confirmar = $state<'suspender' | 'reactivar' | null>(null);

	let f = $state({
		nombre_comercial: '', razon_social: '', nit_rut: '',
		email_contacto: '', telefono: '', logo_url: '',
		categoria_id: '', esquema_comision_id: ''
	});

	function llenarForm() {
		if (!socio) return;
		f = {
			nombre_comercial: socio.nombre_comercial,
			razon_social: socio.razon_social ?? '',
			nit_rut: socio.nit_rut,
			email_contacto: socio.email_contacto ?? '',
			telefono: socio.telefono ?? '',
			logo_url: socio.logo_url ?? '',
			categoria_id: socio.categoria_id ? String(socio.categoria_id) : '',
			esquema_comision_id: socio.esquema_comision_id ? String(socio.esquema_comision_id) : ''
		};
	}

	async function manejarSeleccionLogo(e: Event) {
		const input = e.target as HTMLInputElement;
		const archivo = input.files?.[0];
		if (!archivo) return;

		subiendoLogo = true;
		mensaje = '';
		try {
			const url = await subirImagenCloudinary(archivo, { carpeta: 'logos', tenantId: id });
			f.logo_url = url;
		} catch (err) {
			mensaje = err instanceof ApiError ? err.detail : 'Error al subir imagen a Cloudinary';
		} finally {
			subiendoLogo = false;
		}
	}

	async function cargar() {
		socio = await api.get<SocioDetalle>(`/admin/socios/${id}`);
		kpis = await api.get<KpisSocio>(`/admin/socios/${id}/kpis`);
		planSel = socio.plan_id ? String(socio.plan_id) : '';
		llenarForm();
	}

	async function guardarPlan() {
		guardandoPlan = true;
		try {
			await api.patch(`/admin/socios/${id}/plan`, { plan_id: planSel ? Number(planSel) : null });
			mensaje = 'Plan actualizado';
			cargar();
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error al cambiar plan';
		} finally {
			guardandoPlan = false;
		}
	}

	async function cargarTab() {
		if (tab === 'usuarios') usuarios = await api.get(`/admin/socios/${id}/usuarios`);
		if (tab === 'sucursales') sucursales = await api.get(`/admin/socios/${id}/sucursales`);
		if (tab === 'clientes') {
			clientes = await api.get(`/admin/socios/${id}/clientes?page=${pageClientes}&size=10`);
		}
	}

	async function guardar() {
		try {
			await api.patch(`/admin/socios/${id}`, {
				nombre_comercial: f.nombre_comercial,
				razon_social: f.razon_social || null,
				nit_rut: f.nit_rut,
				email_contacto: f.email_contacto || null,
				telefono: f.telefono || null,
				logo_url: f.logo_url || null,
				categoria_id: f.categoria_id ? Number(f.categoria_id) : null,
				esquema_comision_id: f.esquema_comision_id ? Number(f.esquema_comision_id) : null
			});
			mensaje = 'Perfil actualizado';
			editando = false;
			cargar();
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error al guardar';
		}
	}

	async function cambiarEstado() {
		if (!confirmar || !socio) return;
		try {
			await api.post(`/admin/socios/${id}/${confirmar}`);
			mensaje = confirmar === 'suspender' ? 'Socio suspendido (portal y pantallas bloqueadas)' : 'Socio reactivado';
			confirmar = null;
			cargar();
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error';
		}
	}

	async function accion(acc: 'forzar-reset' | 'reenviar-onboarding') {
		try {
			const r = await api.post<{ detail: string }>(`/admin/socios/${id}/${acc}`);
			mensaje = r.detail;
		} catch (e) {
			mensaje = e instanceof ApiError ? e.detail : 'Error';
		}
	}

	onMount(async () => {
		await cargar();
		[categorias, esquemas, planes] = await Promise.all([
			api.get<CategoriaOut[]>('/admin/categorias'), api.get<EsquemaOut[]>('/admin/esquemas'),
			api.get<PlanOut[]>('/admin/planes')
		]);
	});

	$effect(() => { cargarTab(); });

	const input = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50 focus:border-indigo-500 focus:outline-none';
	const label = 'mb-1 block text-xs font-medium text-slate-500';
</script>

{#if !socio}
	<p class="text-slate-500">Cargando…</p>
{:else}
	<div class="mb-5 flex flex-wrap items-center gap-4">
		{#if socio.logo_url}
			<img src={socio.logo_url} alt={socio.nombre_comercial} class="h-14 w-14 rounded-xl object-cover border border-slate-200 shadow-xs" />
		{:else}
			<div class="flex h-14 w-14 items-center justify-center rounded-xl bg-indigo-50 text-base font-bold text-indigo-600 border border-indigo-100">
				{socio.nombre_comercial.slice(0, 2).toUpperCase()}
			</div>
		{/if}
		<div>
			<h2 class="text-2xl font-bold text-slate-800">{socio.nombre_comercial}</h2>
			<p class="text-sm text-slate-500">NIT {socio.nit_rut} · alta {formatFechaCorta(socio.created_at)}</p>
		</div>
		<Badge texto={socio.estado} variante={socio.estado === 'activo' ? 'ok' : 'bad'} />
		<div class="ml-auto flex gap-2">
			{#if socio.estado === 'activo'}
				<button onclick={() => (confirmar = 'suspender')}
					class="rounded-lg border border-red-300 px-3 py-2 text-sm text-red-600 hover:bg-red-50">Suspender</button>
			{:else}
				<button onclick={() => (confirmar = 'reactivar')}
					class="rounded-lg border border-green-300 px-3 py-2 text-sm text-green-600 hover:bg-green-50">Reactivar</button>
			{/if}
			<button onclick={() => accion('forzar-reset')}
				class="rounded-lg border border-amber-300 px-3 py-2 text-sm text-amber-600 hover:bg-amber-50">
				Forzar reset clave
			</button>
			{#if socio.owner?.onboarding_pendiente}
				<button onclick={() => accion('reenviar-onboarding')}
					class="rounded-lg border border-sky-300 px-3 py-2 text-sm text-sky-600 hover:bg-sky-50">
					Reenviar onboarding
				</button>
			{/if}
		</div>
	</div>

	{#if mensaje}
		<p class="mb-4 rounded-lg bg-sky-50 px-4 py-2 text-sm text-sky-700">{mensaje}</p>
	{/if}

	{#if kpis}
		<div class="mb-6 grid grid-cols-2 gap-4 xl:grid-cols-5">
			<KpiCard titulo="Clientes nuevos" valor={kpis.clientes_nuevos} color="indigo" />
			<KpiCard titulo="Puntos emitidos" valor={kpis.puntos_emitidos} color="green" />
			<KpiCard titulo="Puntos consumidos" valor={kpis.puntos_consumidos} color="amber" />
			<KpiCard titulo="Canjes exitosos" valor={kpis.canjes_exitosos} color="sky" />
			<KpiCard titulo="Tiempo al 1er giro"
				valor={kpis.horas_a_primer_giro !== null ? `${kpis.horas_a_primer_giro}h` : 'sin giros'}
				color="red" />
		</div>
	{/if}

	<div class="mb-4 flex gap-1 rounded-lg bg-slate-200 p-1 text-sm w-fit">
		{#each [['perfil', 'Perfil'], ['usuarios', `Usuarios (${socio.total_empleados})`], ['sucursales', `Sucursales (${socio.total_sucursales})`], ['clientes', `Clientes (${socio.total_clientes})`]] as [key, texto]}
			<button onclick={() => { tab = key as typeof tab; }}
				class="rounded-md px-4 py-1.5 {tab === key ? 'bg-white font-semibold shadow-sm' : 'text-slate-600'}">
				{texto}
			</button>
		{/each}
	</div>

	{#if tab === 'perfil'}
		<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
			<form onsubmit={(e) => { e.preventDefault(); guardar(); }}
				class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
				<div class="mb-4 flex items-center justify-between">
					<h3 class="font-semibold text-slate-700">Perfil comercial</h3>
					<button type="button" onclick={() => { editando = !editando; llenarForm(); }}
						class="text-sm text-indigo-600 hover:underline">
						{editando ? 'Cancelar edición' : 'Editar'}
					</button>
				</div>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<div><span class={label}>Nombre comercial</span>
						<input bind:value={f.nombre_comercial} disabled={!editando} class={input} /></div>
					<div><span class={label}>Razón social</span>
						<input bind:value={f.razon_social} disabled={!editando} class={input} /></div>
					<div><span class={label}>NIT/RUT</span>
						<input bind:value={f.nit_rut} disabled={!editando} class={input} /></div>
					<div><span class={label}>Categoría</span>
						<select bind:value={f.categoria_id} disabled={!editando} class={input}>
							<option value="">—</option>
							{#each categorias as c}<option value={c.id}>{c.nombre}</option>{/each}
						</select></div>
					<div><span class={label}>Email contacto</span>
						<input bind:value={f.email_contacto} disabled={!editando} class={input} /></div>
					<div><span class={label}>Teléfono</span>
						<input bind:value={f.telefono} disabled={!editando} class={input} /></div>
					<div class="sm:col-span-2"><span class={label}>Esquema de comisión</span>
						<select bind:value={f.esquema_comision_id} disabled={!editando} class={input}>
							<option value="">—</option>
							{#each esquemas as es}<option value={es.id}>{es.nombre} ({es.costo_registro}/{es.costo_canje} {es.moneda})</option>{/each}
						</select></div>
					<div class="sm:col-span-2">
						<span class={label}>Logotipo comercial (Cloudinary)</span>
						<div class="flex items-center gap-4 rounded-lg border border-slate-200 bg-slate-50/50 p-4">
							{#if f.logo_url}
								<img src={f.logo_url} alt="Logo" class="h-16 w-16 rounded-lg object-cover border border-slate-200 shadow-xs" />
							{:else}
								<div class="flex h-16 w-16 items-center justify-center rounded-lg bg-slate-200 text-slate-500">
									<Icon name="camera" clase="h-8 w-8 text-slate-500" />
								</div>
							{/if}
							<div class="flex-1">
								{#if editando}
									<label class="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50">
										<Icon name="upload" clase="h-4 w-4 text-slate-500" />
										<span>{subiendoLogo ? 'Subiendo a Cloudinary…' : f.logo_url ? 'Cambiar logotipo' : 'Subir imagen'}</span>
										<input type="file" accept="image/*" onchange={manejarSeleccionLogo} disabled={subiendoLogo} class="hidden" />
									</label>
									<p class="mt-1 text-xs text-slate-500">Formato cuadrado PNG, JPG o WEBP.</p>
									{#if f.logo_url}
										<button type="button" onclick={() => (f.logo_url = '')} class="mt-1 text-xs text-rose-600 hover:underline">
											Remover logo
										</button>
									{/if}
								{:else}
									<p class="text-xs text-slate-500 font-medium">
										{f.logo_url ? 'Logotipo activo en Cloudinary' : 'Sin logotipo cargado'}
									</p>
								{/if}
							</div>
						</div>
					</div>
				</div>
				{#if editando}
					<button type="submit" class="mt-5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
						Guardar cambios
					</button>
				{/if}
			</form>

			<div class="space-y-6">
				<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
					<h3 class="mb-4 font-semibold text-slate-700">Owner</h3>
					{#if socio.owner}
						<p class="text-sm font-medium text-slate-800">{socio.owner.nombre}</p>
						<p class="text-sm text-slate-500">{socio.owner.email}</p>
						<div class="mt-2 flex items-center gap-2">
							<Badge texto={socio.owner.estado} variante={socio.owner.estado === 'activo' ? 'ok' : 'bad'} />
							{#if socio.owner.onboarding_pendiente}
								<Badge texto="onboarding pendiente" variante="warn" />
							{/if}
						</div>
					{:else}
						<p class="text-sm text-slate-500">Sin owner asignado</p>
					{/if}
				</div>

				<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
					<h3 class="mb-4 font-semibold text-slate-700">Plan comercial</h3>
					<div class="space-y-3">
						<div>
							<span class={label}>Plan</span>
							<select bind:value={planSel} class={input}>
								<option value="">Sin plan (ilimitado)</option>
								{#each planes as p}
									<option value={p.id}>{p.nombre} — {p.precio_mensual === 0 ? 'gratis' : `${p.precio_mensual} ${p.moneda}/mes`}</option>
								{/each}
							</select>
						</div>
						{#if socio.trial_fin}
							<p class="text-xs text-slate-500">
								Trial hasta: <strong>{formatFecha(socio.trial_fin)}</strong>
								{#if socio.trial_fin > new Date().toISOString()}
									<Badge texto="en trial" variante="info" />
								{/if}
							</p>
						{/if}
						<div class="flex items-center justify-between text-xs text-slate-500">
							<span>Estado de cuenta</span>
							<Badge
								texto={socio.facturacion_estado === 'al_dia' ? 'al día' : socio.facturacion_estado}
								variante={socio.facturacion_estado === 'al_dia' ? 'ok' : socio.facturacion_estado === 'pendiente' ? 'warn' : 'bad'} />
						</div>
						{#if String(socio.plan_id ?? '') !== planSel}
							<button onclick={guardarPlan} disabled={guardandoPlan}
								class="w-full rounded-lg bg-emerald-600 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
								{guardandoPlan ? 'Guardando…' : 'Aplicar plan'}
							</button>
						{/if}
					</div>
				</div>
			</div>
		</div>

	{:else if tab === 'usuarios'}
		<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
			<DataTable
				columnas={[{ key: 'nombre', label: 'Nombre' }, { key: 'email', label: 'Email' }, { key: 'rol', label: 'Rol' }, { key: 'estado', label: 'Estado' }, { key: 'ultimo_login', label: 'Último login' }]}
				filas={usuarios as unknown as Record<string, unknown>[]}>
				{#snippet celda({ key, fila })}
					{@const u = fila as unknown as UsuarioListItem}
					{#if key === 'estado'}<Badge texto={u.estado} variante={u.estado === 'activo' ? 'ok' : 'bad'} />
					{:else if key === 'ultimo_login'}{formatFecha(u.ultimo_login)}
					{:else}{u[key as keyof UsuarioListItem] ?? '—'}{/if}
				{/snippet}
			</DataTable>
		</div>

	{:else if tab === 'sucursales'}
		<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
			<DataTable
				columnas={[{ key: 'nombre', label: 'Nombre' }, { key: 'direccion', label: 'Dirección' }, { key: 'encargado_nombre', label: 'Encargado' }, { key: 'estado', label: 'Estado' }]}
				filas={sucursales as unknown as Record<string, unknown>[]}>
				{#snippet celda({ key, fila })}
					{@const s = fila as unknown as SucursalListItem}
					{#if key === 'estado'}<Badge texto={s.estado} variante={s.estado === 'activa' ? 'ok' : 'bad'} />
					{:else}{s[key as keyof SucursalListItem] ?? '—'}{/if}
				{/snippet}
			</DataTable>
		</div>

	{:else}
		<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
			<DataTable
				columnas={[{ key: 'nombre', label: 'Nombre' }, { key: 'ci', label: 'CI' }, { key: 'telefono', label: 'Teléfono' }, { key: 'estado', label: 'Estado' }, { key: 'created_at', label: 'Registro' }]}
				filas={(clientes?.items ?? []) as unknown as Record<string, unknown>[]}>
				{#snippet celda({ key, fila })}
					{@const c = fila as unknown as ClienteListItem}
					{#if key === 'estado'}<Badge texto={c.estado} variante={c.estado === 'activo' ? 'ok' : 'neutral'} />
					{:else if key === 'created_at'}{formatFechaCorta(c.created_at)}
					{:else}{c[key as keyof ClienteListItem] ?? '—'}{/if}
				{/snippet}
			</DataTable>
			{#if clientes}
				<Pagination total={clientes.total} page={clientes.page} size={clientes.size}
					onchange={(p) => { pageClientes = p; cargarTab(); }} />
			{/if}
		</div>
	{/if}
{/if}

<Modal abierto={confirmar !== null} titulo="Confirmar" onclose={() => (confirmar = null)}>
	{#if confirmar && socio}
		<p class="text-sm text-slate-600">
			¿{confirmar === 'suspender' ? 'Suspender' : 'Reactivar'} a <strong>{socio.nombre_comercial}</strong>?
		</p>
		{#if confirmar === 'suspender'}
			<p class="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
				Bloquea el acceso al portal de sus usuarios y las pantallas físicas del local.
			</p>
		{/if}
		<div class="mt-5 flex justify-end gap-2">
			<button onclick={() => (confirmar = null)} class="rounded-lg border border-slate-300 px-4 py-2 text-sm">Cancelar</button>
			<button onclick={cambiarEstado}
				class="rounded-lg px-4 py-2 text-sm font-semibold text-white {confirmar === 'suspender' ? 'bg-red-600' : 'bg-green-600'}">
				Confirmar
			</button>
		</div>
	{/if}
</Modal>
