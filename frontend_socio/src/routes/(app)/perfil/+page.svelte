<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '#lib/api/client';
	import { auth } from '#lib/stores/auth.svelte';
	import ImageUploader from '#lib/components/ui/ImageUploader.svelte';
	import Seguridad2fa from '#lib/components/ui/Seguridad2fa.svelte';
	import { i18n, type Locale } from '#lib/i18n.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import type { Perfil } from '#lib/types';

	let perfil = $state<Perfil | null>(null);
	let nombre = $state('');
	let tenantNombre = $state('');
	let logo = $state<string | null>(null);
	let error = $state('');
	let mensaje = $state('');
	let guardando = $state(false);

	const idiomas: { code: Locale; nombre: string }[] = [
		{ code: 'es', nombre: 'Español' },
		{ code: 'en', nombre: 'English' }
	];

	let passActual = $state('');
	let passNuevo = $state('');
	let passConfirmar = $state('');
	let errorPass = $state('');
	let cambiando = $state(false);

	async function cargar() {
		try {
			perfil = await api.get<Perfil>('/socio/perfil');
			nombre = perfil.nombre;
			tenantNombre = perfil.tenant_nombre;
			logo = perfil.logo_url;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cargar';
		}
	}

	async function guardarPerfil(e: SubmitEvent) {
		e.preventDefault();
		guardando = true;
		error = '';
		mensaje = '';
		try {
			perfil = await api.patch<Perfil>('/socio/perfil', {
				nombre,
				tenant_nombre: tenantNombre,
				logo_url: logo
			});
			if (auth.usuario) {
				auth.actualizarUsuario({
					...auth.usuario,
					nombre: perfil.nombre,
					tenant_nombre: perfil.tenant_nombre,
					tenant_logo: perfil.logo_url
				});
			}
			mensaje = '¡Datos de empresa y perfil actualizados exitosamente!';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error al guardar';
		} finally {
			guardando = false;
		}
	}

	async function cambiarPassword(e: SubmitEvent) {
		e.preventDefault();
		errorPass = '';
		if (passNuevo !== passConfirmar) {
			errorPass = 'Las contraseñas no coinciden';
			return;
		}
		cambiando = true;
		try {
			await api.post('/socio/perfil/cambiar-password', {
				password_actual: passActual,
				password_nuevo: passNuevo
			});
			auth.limpiar();
			goto('/login');
		} catch (err) {
			errorPass = err instanceof Error ? err.message : 'Error';
		} finally {
			cambiando = false;
		}
	}

	onMount(cargar);
</script>

<div class="max-w-3xl space-y-6">
	{#if perfil}
		<!-- Tarjeta de Branding y Logo con Cloudinary -->
		<div class="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm transition hover:shadow-md">
			<div class="border-b border-slate-100 bg-gradient-to-r from-emerald-50 via-teal-50/50 to-white px-6 py-4">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-3">
						<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm">
							<Icon name="store" clase="h-5 w-5" />
						</div>
						<div>
							<h3 class="text-base font-bold text-slate-800">Marca y Logo de la Empresa</h3>
							<p class="text-xs text-slate-500">Almacenado y optimizado en la nube con Cloudinary</p>
						</div>
					</div>
					<span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-100/80 px-3 py-1 text-xs font-semibold text-emerald-800">
						<span class="h-1.5 w-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
						Cloudinary Activo
					</span>
				</div>
			</div>

			<div class="p-6">
				<div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
					<!-- Columna de subida de imagen con Cloudinary -->
					<div class="flex flex-col items-center sm:items-start text-center sm:text-left">
						<span class="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">Logo Oficial</span>
						<ImageUploader bind:value={logo} carpeta="logo" aspecto="square" />
						<p class="mt-2 text-[11px] leading-relaxed text-slate-400">
							Se muestra en la <strong class="text-slate-600">App Móvil de Clientes</strong>, en el <strong class="text-slate-600">Kiosco de Registro</strong> y en la terminal de caja.
						</p>
					</div>

					<!-- Formulario de datos comerciales -->
					<div class="md:col-span-2 space-y-4">
						<div>
							<label for="tnom" class="mb-1 block text-sm font-semibold text-slate-700">Nombre Comercial del Negocio</label>
							<input id="tnom" type="text" bind:value={tenantNombre} required minlength="2"
								placeholder="Ej: Pizzería Don Yapai"
								class="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-800 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition" />
							<p class="mt-1 text-xs text-slate-400">Nombre visible para tus clientes y en reportes oficiales.</p>
						</div>

						<div class="rounded-xl border border-dashed border-emerald-200 bg-emerald-50/40 p-3.5">
							<div class="flex items-start gap-2.5">
								<Icon name="check-circle" clase="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" />
								<div class="text-xs text-emerald-900 leading-relaxed">
									<strong class="font-semibold">Subida automática a Cloudinary:</strong> al seleccionar o arrastrar tu archivo, se optimiza en CDN con entrega ultra rápida en todos los dispositivos.
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Tarjeta de Datos de Contacto y Dueño -->
		<div class="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
			<div class="flex items-center gap-3 mb-5 pb-3 border-b border-slate-100">
				<div class="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
					<Icon name="user" clase="h-4 w-4" />
				</div>
				<div>
					<h3 class="font-bold text-slate-800">Datos del Administrador</h3>
					<p class="text-xs text-slate-500">Información del titular de la cuenta</p>
				</div>
			</div>

			<form onsubmit={guardarPerfil} class="space-y-4">
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label for="nom" class="mb-1 block text-sm font-medium text-slate-700">Nombre completo</label>
						<input id="nom" type="text" bind:value={nombre} required minlength="2"
							class="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm text-slate-800 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition" />
					</div>
					<div>
						<label for="cor" class="mb-1 block text-sm font-medium text-slate-700">Correo electrónico</label>
						<input id="cor" type="email" value={perfil.email} disabled
							class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-400 cursor-not-allowed" />
						<p class="mt-1 text-xs text-slate-400">Identificador único de acceso (no modificable).</p>
					</div>
				</div>

				<div>
					<span class="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-500">Idioma de la plataforma</span>
					<div class="flex items-center gap-2">
						{#each idiomas as idioma}
							<button type="button" onclick={() => i18n.set(idioma.code)}
								class="rounded-lg px-4 py-1.5 text-xs font-semibold transition
									{i18n.locale === idioma.code ? 'bg-emerald-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}">
								{idioma.nombre}
							</button>
						{/each}
					</div>
				</div>

				{#if error}
					<p class="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm font-medium text-red-600">{error}</p>
				{/if}
				{#if mensaje}
					<p class="rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm font-medium text-emerald-700">{mensaje}</p>
				{/if}

				<div class="pt-2">
					<button type="submit" disabled={guardando}
						class="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-emerald-700 active:scale-[0.98] disabled:opacity-50">
						{#if guardando}
							<Icon name="loader" clase="h-4 w-4 animate-spin" />
							<span>Guardando cambios…</span>
						{:else}
							<Icon name="check" clase="h-4 w-4" />
							<span>Guardar cambios</span>
						{/if}
					</button>
				</div>
			</form>
		</div>

		<div class="rounded-xl border border-slate-200 bg-white p-6">
			<h3 class="font-semibold text-slate-800">Cambiar contraseña</h3>
			<p class="mt-1 text-xs text-slate-400">Al cambiarla se cerrarán todas tus sesiones activas.</p>
			<form onsubmit={cambiarPassword} class="mt-4 space-y-4">
				<div>
					<label for="pa" class="mb-1 block text-sm font-medium text-slate-700">Contraseña actual</label>
					<input id="pa" type="password" bind:value={passActual} required
						class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label for="pn" class="mb-1 block text-sm font-medium text-slate-700">Nueva contraseña</label>
						<input id="pn" type="password" bind:value={passNuevo} required minlength="8"
							class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
					</div>
					<div>
						<label for="pc" class="mb-1 block text-sm font-medium text-slate-700">Confirmar</label>
						<input id="pc" type="password" bind:value={passConfirmar} required
							class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
					</div>
				</div>
				{#if errorPass}
					<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{errorPass}</p>
				{/if}
				<button type="submit" disabled={cambiando}
					class="rounded-lg bg-slate-900 px-6 py-2 font-semibold text-white hover:bg-slate-800 disabled:opacity-50">
					{cambiando ? 'Cambiando…' : 'Cambiar contraseña'}
				</button>
			</form>
		</div>

		<Seguridad2fa />
	{:else}
		<p class="text-slate-400">Cargando perfil…</p>
	{/if}
</div>
