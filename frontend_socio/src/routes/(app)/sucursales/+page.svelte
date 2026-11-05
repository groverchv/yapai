<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import ImageUploader from '#lib/components/ui/ImageUploader.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import { formatFecha } from '#lib/utils/format';
	import type { Pantalla, Sucursal } from '#lib/types';

	let sucursales = $state<Sucursal[]>([]);
	let cargando = $state(true);
	let error = $state('');
	let mensaje = $state('');

	let modal = $state<'crear' | 'editar' | 'pantalla' | null>(null);
	let qrModal = $state<{ svg: string; url: string; nombre: string } | null>(null);
	let previewPantalla = $state<Pantalla | null>(null);
	let seleccionada = $state<Sucursal | null>(null);
	let formNombre = $state('');
	let formDireccion = $state('');
	let formEncargado = $state('');
	let formImagen = $state('');
	let formPantalla = $state('');
	let nuevaPantalla = $state<Pantalla | null>(null);
	let guardando = $state(false);
	let errorModal = $state('');

	async function cargar() {
		cargando = true;
		error = '';
		try {
			sucursales = await api.get<Sucursal[]>('/socio/sucursales');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cargar';
		} finally {
			cargando = false;
		}
	}

	function abrirCrear() {
		formNombre = '';
		formDireccion = '';
		formEncargado = '';
		formImagen = '';
		errorModal = '';
		modal = 'crear';
	}

	function abrirEditar(s: Sucursal) {
		seleccionada = s;
		formNombre = s.nombre;
		formDireccion = s.direccion ?? '';
		formEncargado = s.encargado_nombre ?? '';
		formImagen = s.imagen_url ?? '';
		errorModal = '';
		modal = 'editar';
	}

	function abrirPantalla(s: Sucursal) {
		seleccionada = s;
		formPantalla = '';
		nuevaPantalla = null;
		errorModal = '';
		modal = 'pantalla';
	}

	async function guardar(e: SubmitEvent) {
		e.preventDefault();
		guardando = true;
		errorModal = '';
		try {
			const body = {
				nombre: formNombre,
				direccion: formDireccion || null,
				encargado_nombre: formEncargado || null,
				imagen_url: formImagen || null
			};
			if (modal === 'crear') await api.post('/socio/sucursales', body);
			else if (seleccionada) await api.patch(`/socio/sucursales/${seleccionada.id}`, body);
			modal = null;
			cargar();
		} catch (err) {
			errorModal = err instanceof Error ? err.message : 'Error al guardar';
		} finally {
			guardando = false;
		}
	}

	async function crearPantalla(e: SubmitEvent) {
		e.preventDefault();
		if (!seleccionada) return;
		guardando = true;
		errorModal = '';
		try {
			nuevaPantalla = await api.post<Pantalla>(
				`/socio/sucursales/${seleccionada.id}/pantallas`, { nombre: formPantalla });
			cargar();
		} catch (err) {
			errorModal = err instanceof Error ? err.message : 'Error al crear';
		} finally {
			guardando = false;
		}
	}

	async function accion(s: Sucursal, op: 'suspender' | 'reactivar') {
		error = '';
		try {
			await api.post(`/socio/sucursales/${s.id}/${op}`);
			cargar();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error';
		}
	}

	async function verQr(p: Pantalla) {
		try {
			const qr = await api.get<{ svg: string; url: string }>(
				`/socio/sucursales/pantallas/${p.id}/qr`);
			qrModal = { ...qr, nombre: p.nombre };
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error';
		}
	}

	function descargarQr() {
		if (!qrModal) return;
		const blob = new Blob([qrModal.svg], { type: 'image/svg+xml' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `kiosco-qr-${qrModal.nombre.toLowerCase().replace(/\s+/g, '-')}.svg`;
		a.click();
		URL.revokeObjectURL(url);
	}

	async function rotarToken(p: Pantalla) {
		error = '';
		mensaje = '';
		try {
			await api.post(`/socio/sucursales/pantallas/${p.id}/rotar-token`);
			mensaje = `Token rotado para "${p.nombre}". La pantalla deberá configurarse nuevamente.`;
			cargar();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error';
		}
	}

	onMount(cargar);
</script>

<div class="space-y-4">
	<div class="flex justify-end">
		<button onclick={abrirCrear}
			class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
			+ Nueva sucursal
		</button>
	</div>

	{#if error}
		<p class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
	{/if}
	{#if mensaje}
		<p class="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{mensaje}</p>
	{/if}

	{#if cargando}
		<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
			{#each Array(2) as _}
				<div class="h-64 animate-pulse rounded-xl bg-slate-100"></div>
			{/each}
		</div>
	{:else if sucursales.length === 0}
		<EmptyState icono="store" titulo="Aún no tienes sucursales"
			descripcion="Registra tu local con dirección y coordenadas GPS — tus clientes verán cómo llegar desde la app."
			cta="Agregar mi primera sucursal" oncta={abrirCrear} />
	{:else}
		<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
			{#each sucursales as s}
				<div class="flex flex-col justify-between overflow-hidden rounded-xl border border-slate-200 bg-white">
					<div>
						{#if s.imagen_url}
							<div class="relative h-44 w-full bg-slate-100">
								<img src={s.imagen_url} alt={s.nombre} class="h-full w-full object-cover" />
								<div class="absolute top-3 right-3 flex gap-1">
									<Badge texto={s.estado === 'activa' ? 'Activa' : 'Suspendida'}
										variante={s.estado === 'activa' ? 'ok' : 'bad'} />
									{#if s.pin_set}
										<Badge texto="PIN definido" variante="info" />
									{/if}
								</div>
							</div>
						{/if}
						<div class="p-5">
							<div class="flex items-start justify-between">
								<div>
									<h3 class="text-base font-semibold text-slate-800">{s.nombre}</h3>
									<p class="text-sm text-slate-500">{s.direccion ?? 'Sin dirección'}</p>
									<p class="mt-0.5 text-xs text-slate-500">Encargado: {s.encargado_nombre ?? '—'}</p>
								</div>
								{#if !s.imagen_url}
									<div class="flex gap-1">
										<Badge texto={s.estado === 'activa' ? 'Activa' : 'Suspendida'}
											variante={s.estado === 'activa' ? 'ok' : 'bad'} />
										{#if s.pin_set}
											<Badge texto="PIN definido" variante="info" />
										{/if}
									</div>
								{/if}
							</div>

							<div class="mt-4 space-y-2">
								<p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
									Pantallas / Kioscos ({s.pantallas.length})
								</p>
								{#each s.pantallas as p}
									<div class="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
										<div>
											<span class="font-medium text-slate-700">{p.nombre}</span>
											<Badge texto={p.estado} variante={p.estado === 'activa' ? 'ok' : 'bad'} />
											<p class="font-mono text-xs text-slate-500">
												{kioscoUrl(p.device_token)}
											</p>
											{#if p.habilitada_hasta}
												<p class="text-xs text-emerald-600">Habilitada hasta {formatFecha(p.habilitada_hasta)}</p>
											{/if}
										</div>
										<div class="flex shrink-0 flex-col items-end gap-1">
											<button onclick={() => verQr(p)}
												class="text-xs font-medium text-emerald-600 hover:underline">Ver QR</button>
											<button onclick={() => (previewPantalla = p)}
												class="text-xs font-medium text-indigo-600 hover:underline">Vista previa</button>
											<button onclick={() => rotarToken(p)}
												class="text-xs text-sky-600 hover:underline">Rotar token</button>
										</div>
									</div>
								{:else}
									<p class="text-sm text-slate-500">Sin pantallas registradas.</p>
								{/each}
							</div>
						</div>
					</div>

					<div class="border-t border-slate-100 bg-slate-50/50 px-5 py-3 flex gap-3 text-sm">
						<button onclick={() => abrirEditar(s)} class="text-emerald-600 hover:underline">Editar</button>
						{#if s.estado === 'activa'}
							<button onclick={() => abrirPantalla(s)} class="text-sky-600 hover:underline">+ Pantalla</button>
							<button onclick={() => accion(s, 'suspender')} class="text-red-600 hover:underline">Suspender</button>
						{:else}
							<button onclick={() => accion(s, 'reactivar')} class="text-green-600 hover:underline">Reactivar</button>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<Modal abierto={modal === 'crear' || modal === 'editar'}
	titulo={modal === 'crear' ? 'Nueva sucursal' : 'Editar sucursal'} onclose={() => (modal = null)}>
	<form onsubmit={guardar} class="space-y-4">
		<div>
			<span class="mb-1 block text-sm font-medium text-slate-700">Foto de la sucursal</span>
			<ImageUploader bind:value={formImagen} carpeta="sucursales" aspecto="video" />
		</div>
		<div>
			<label for="sn" class="mb-1 block text-sm font-medium text-slate-700">Nombre</label>
			<input id="sn" type="text" bind:value={formNombre} required minlength="2"
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
		</div>
		<div>
			<label for="sd" class="mb-1 block text-sm font-medium text-slate-700">Dirección</label>
			<input id="sd" type="text" bind:value={formDireccion}
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
		</div>
		<div>
			<label for="se" class="mb-1 block text-sm font-medium text-slate-700">Encargado</label>
			<input id="se" type="text" bind:value={formEncargado}
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
		</div>
		{#if errorModal}
			<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{errorModal}</p>
		{/if}
		<button type="submit" disabled={guardando}
			class="w-full rounded-lg bg-emerald-600 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
			{guardando ? 'Guardando…' : 'Guardar'}
		</button>
	</form>
</Modal>

<Modal abierto={modal === 'pantalla'} titulo="Registrar pantalla / kiosco" onclose={() => (modal = null)}>
	{#if nuevaPantalla}
		<div class="space-y-3">
			<p class="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
				Pantalla "{nuevaPantalla.nombre}" creada.
			</p>
			<p class="text-sm text-slate-600">Abre esta URL en el dispositivo del local:</p>
			<code class="block rounded-lg bg-slate-100 px-3 py-2 font-mono text-xs break-all">
				{kioscoUrl(nuevaPantalla.device_token)}
			</code>
			<button onclick={() => { nuevaPantalla = null; modal = null; }}
				class="w-full rounded-lg bg-emerald-600 py-2 font-semibold text-white hover:bg-emerald-700">
				Listo
			</button>
		</div>
	{:else}
		<form onsubmit={crearPantalla} class="space-y-4">
			<div>
				<label for="pn" class="mb-1 block text-sm font-medium text-slate-700">Nombre de la pantalla</label>
				<input id="pn" type="text" bind:value={formPantalla} required placeholder="Ej: Pantalla entrada"
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
			</div>
			{#if errorModal}
				<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{errorModal}</p>
			{/if}
			<button type="submit" disabled={guardando}
				class="w-full rounded-lg bg-emerald-600 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
				{guardando ? 'Creando…' : 'Crear pantalla'}
			</button>
		</form>
	{/if}
</Modal>

<Modal abierto={qrModal !== null} titulo={`QR del kiosco — ${qrModal?.nombre ?? ''}`} onclose={() => (qrModal = null)}>
	{#if qrModal}
		<div class="space-y-4 text-center">
			<p class="text-sm text-slate-600">
				Imprime este código y pégalo junto a la pantalla. Al escanearlo, el dispositivo
				abre el kiosco directamente.
			</p>
			<div class="mx-auto w-56 rounded-xl border border-slate-200 p-3 [&_svg]:h-auto [&_svg]:w-full">
				{@html qrModal.svg}
			</div>
			<code class="block rounded-lg bg-slate-100 px-3 py-2 font-mono text-xs break-all">{qrModal.url}</code>
			<div class="flex gap-2">
				<button onclick={descargarQr}
					class="flex-1 rounded-lg bg-emerald-600 py-2 text-sm font-semibold text-white hover:bg-emerald-700">
					Descargar SVG
				</button>
				<button onclick={() => window.print()}
					class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:border-emerald-500">
					Imprimir
				</button>
			</div>
		</div>
	{/if}
</Modal>

<Modal abierto={previewPantalla !== null} titulo={`Vista previa — ${previewPantalla?.nombre ?? ''}`}
	onclose={() => (previewPantalla = null)}>
	{#if previewPantalla}
		<p class="mb-3 text-xs text-slate-500">
			Así se ve el kiosco en la pantalla del local. Si pide PIN, habilítala primero desde la terminal de caja.
		</p>
		<div class="overflow-hidden rounded-xl border border-slate-200 bg-slate-950">
			<iframe src={kioscoUrl(previewPantalla.device_token)}
				title="Vista previa del kiosco" class="h-[540px] w-full"></iframe>
		</div>
		<a href={kioscoUrl(previewPantalla.device_token)} target="_blank" rel="noreferrer"
			class="mt-3 block text-center text-xs font-semibold text-emerald-700 hover:underline">
			Abrir en pestaña nueva ↗
		</a>
	{/if}
</Modal>

<script lang="ts" module>
	function kioscoUrl(token: string): string {
		return `${location.origin}/kiosco/${token}`;
	}
</script>
