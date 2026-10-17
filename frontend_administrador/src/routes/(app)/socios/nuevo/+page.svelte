<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { onMount } from 'svelte';
	import { api, ApiError } from '#lib/api/client';
	import type { CategoriaOut, EsquemaOut, SocioDetalle } from '#lib/types';
	import { formatDinero } from '#lib/utils/format';

	let categorias = $state<CategoriaOut[]>([]);
	let esquemas = $state<EsquemaOut[]>([]);
	let enviando = $state(false);
	let error = $state('');
	let creado = $state<{ socio: SocioDetalle; onboarding_link: string } | null>(null);

	let f = $state({
		nombre_comercial: '', razon_social: '', nit_rut: '',
		email_contacto: '', telefono: '', categoria_id: '', esquema_comision_id: '',
		owner_nombre: '', owner_email: ''
	});

	onMount(async () => {
		[categorias, esquemas] = await Promise.all([
			api.get<CategoriaOut[]>('/admin/categorias'),
			api.get<EsquemaOut[]>('/admin/esquemas')
		]);
	});

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
