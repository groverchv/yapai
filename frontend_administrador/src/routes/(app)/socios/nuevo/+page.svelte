<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { onMount } from 'svelte';
	import { api, ApiError } from '#lib/api/client';
	import type { CategoriaOut, EsquemaOut, SocioDetalle } from '#lib/types';
	import { formatDinero } from '#lib/utils/format';
	import { subirImagenCloudinary } from '#lib/utils/upload';

	let categorias = $state<CategoriaOut[]>([]);
	let esquemas = $state<EsquemaOut[]>([]);
	let enviando = $state(false);
	let subiendoLogo = $state(false);
	let error = $state('');
	let creado = $state<{ socio: SocioDetalle; onboarding_link: string } | null>(null);

	let f = $state({
		nombre_comercial: '', razon_social: '', nit_rut: '',
		email_contacto: '', telefono: '', logo_url: '',
		categoria_id: '', esquema_comision_id: '',
		owner_nombre: '', owner_email: ''
	});

	onMount(async () => {
		[categorias, esquemas] = await Promise.all([
			api.get<CategoriaOut[]>('/admin/categorias'),
			api.get<EsquemaOut[]>('/admin/esquemas')
		]);
	});

	async function manejarSeleccionArchivo(e: Event) {
		const input = e.target as HTMLInputElement;
		const archivo = input.files?.[0];
		if (!archivo) return;

		subiendoLogo = true;
		error = '';
		try {
			const url = await subirImagenCloudinary(archivo, { carpeta: 'logos' });
			f.logo_url = url;
		} catch (err) {
			error = err instanceof ApiError ? err.detail : 'Error al subir el logo a Cloudinary';
		} finally {
			subiendoLogo = false;
		}
	}

	async function crear(e: SubmitEvent) {
		e.preventDefault();
		enviando = true;
		error = '';
		try {
			creado = await api.post('/admin/socios', {
				nombre_comercial: f.nombre_comercial,
				razon_social: f.razon_social || null,
				nit_rut: f.nit_rut,
				email_contacto: f.email_contacto || null,
				telefono: f.telefono || null,
				logo_url: f.logo_url || null,
				categoria_id: f.categoria_id ? Number(f.categoria_id) : null,
				esquema_comision_id: f.esquema_comision_id ? Number(f.esquema_comision_id) : null,
				owner: { nombre: f.owner_nombre, email: f.owner_email }
			});
		} catch (err) {
			error = err instanceof ApiError ? err.detail : 'Error al crear el socio';
		} finally {
			enviando = false;
		}
	}

	const input = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500';
	const label = 'mb-1 block text-sm font-medium text-slate-700';
</script>

{#if creado}
	<div class="mx-auto max-w-2xl rounded-xl border border-green-200 bg-white p-8 shadow-sm">
		<h2 class="text-xl font-semibold text-green-700"><Icon name="check" clase="mr-1 inline h-5 w-5 align-middle" /> Socio creado: {creado.socio.nombre_comercial}</h2>
		<p class="mt-2 text-sm text-slate-600">
			Se envió el correo de bienvenida a <strong>{creado.socio.owner?.email}</strong> con el enlace
			para establecer su contraseña.
		</p>
		<div class="mt-4 rounded-lg bg-slate-50 p-3">
			<p class="text-xs font-medium text-slate-500">Enlace de onboarding (también enviado por email):</p>
			<code class="mt-1 block break-all text-xs text-indigo-600">{creado.onboarding_link}</code>
		</div>
		<div class="mt-6 flex gap-3">
			<a href="/socios/{creado.socio.id}"
				class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
				Ver detalle
			</a>
			<button onclick={() => { creado = null; f = { ...f, nombre_comercial: '', razon_social: '', nit_rut: '', email_contacto: '', telefono: '', owner_nombre: '', owner_email: '' }; }}
				class="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">
				Crear otro socio
			</button>
		</div>
	</div>
{:else}
	<form onsubmit={crear} class="mx-auto max-w-3xl space-y-6">
		{#if error}
			<p class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
		{/if}

		<section class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
			<h2 class="mb-4 font-semibold text-slate-700">1 · Datos comerciales</h2>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				<div>
					<label for="nc" class={label}>Nombre comercial *</label>
					<input id="nc" bind:value={f.nombre_comercial} required class={input} />
				</div>
				<div>
					<label for="rs" class={label}>Razón social</label>
					<input id="rs" bind:value={f.razon_social} class={input} />
				</div>
				<div>
					<label for="nit" class={label}>NIT/RUT *</label>
					<input id="nit" bind:value={f.nit_rut} required class={input} />
				</div>
				<div>
					<label for="cat" class={label}>Categoría</label>
					<select id="cat" bind:value={f.categoria_id} class={input}>
						<option value="">— Sin categoría —</option>
						{#each categorias as c}
							<option value={c.id} disabled={!c.activa}>{c.nombre}</option>
						{/each}
					</select>
				</div>
				<div>
					<label for="em" class={label}>Email contacto</label>
					<input id="em" type="email" bind:value={f.email_contacto} class={input} />
				</div>
				<div>
					<label for="tel" class={label}>Teléfono</label>
					<input id="tel" bind:value={f.telefono} class={input} />
				</div>
				<div class="sm:col-span-2">
					<span class={label}>Logotipo del comercio (Cloudinary)</span>
					<div class="flex items-center gap-4 rounded-lg border border-dashed border-slate-300 p-4 bg-slate-50/50">
						{#if f.logo_url}
							<img src={f.logo_url} alt="Logo" class="h-16 w-16 rounded-lg object-cover border border-slate-200 shadow-xs" />
						{:else}
							<div class="flex h-16 w-16 items-center justify-center rounded-lg bg-slate-200 text-slate-500">
								<Icon name="camera" clase="h-8 w-8 text-slate-500" />
							</div>
						{/if}
						<div class="flex-1">
							<label class="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50">
								<Icon name="upload" clase="h-4 w-4 text-slate-500" />
								<span>{subiendoLogo ? 'Subiendo a Cloudinary…' : f.logo_url ? 'Cambiar logotipo' : 'Seleccionar archivo'}</span>
								<input type="file" accept="image/*" onchange={manejarSeleccionArchivo} disabled={subiendoLogo} class="hidden" />
							</label>
							<p class="mt-1 text-xs text-slate-500">PNG, JPG o WEBP recomendados (cuadrado, min 200x200px).</p>
							{#if f.logo_url}
								<button type="button" onclick={() => (f.logo_url = '')} class="mt-1 text-xs text-red-600 hover:underline">
									Eliminar logo
								</button>
							{/if}
						</div>
					</div>
				</div>
			</div>
		</section>

		<section class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
			<h2 class="mb-4 font-semibold text-slate-700">2 · Usuario administrador (Owner)</h2>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				<div>
					<label for="on" class={label}>Nombre completo *</label>
					<input id="on" bind:value={f.owner_nombre} required class={input} />
				</div>
				<div>
					<label for="oe" class={label}>Email *</label>
					<input id="oe" type="email" bind:value={f.owner_email} required class={input} />
				</div>
			</div>
			<p class="mt-3 text-xs text-slate-500">
				Recibirá un correo con un enlace único de vencimiento para establecer su contraseña.
			</p>
		</section>

		<section class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
			<h2 class="mb-4 font-semibold text-slate-700">3 · Esquema de comisión</h2>
			<select bind:value={f.esquema_comision_id} class={input} aria-label="Esquema de comisión">
				<option value="">— Sin esquema —</option>
				{#each esquemas.filter((e) => e.activo) as es}
					<option value={es.id}>
						{es.nombre} — registro {formatDinero(es.costo_registro, es.moneda)} · canje {formatDinero(es.costo_canje, es.moneda)}
					</option>
				{/each}
			</select>
		</section>

		<div class="flex justify-end gap-3">
			<a href="/socios" class="rounded-lg border border-slate-300 px-5 py-2.5 text-sm text-slate-600 hover:bg-slate-50">
				Cancelar
			</a>
			<button type="submit" disabled={enviando}
				class="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
				{enviando ? 'Creando…' : 'Crear socio y enviar onboarding'}
			</button>
		</div>
	</form>
{/if}
