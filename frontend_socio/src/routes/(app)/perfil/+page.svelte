<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '#lib/api/client';
	import { auth } from '#lib/stores/auth.svelte';
	import ImageUploader from '#lib/components/ui/ImageUploader.svelte';
	import Seguridad2fa from '#lib/components/ui/Seguridad2fa.svelte';
	import { i18n, type Locale } from '#lib/i18n.svelte';
	import type { Perfil } from '#lib/types';

	let perfil = $state<Perfil | null>(null);
	let nombre = $state('');
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
			logo = perfil.logo_url;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cargar';
		}
	}

	async function guardarNombre(e: SubmitEvent) {
		e.preventDefault();
		guardando = true;
		error = '';
		mensaje = '';
		try {
			perfil = await api.patch<Perfil>('/socio/perfil', {
				nombre,
				...(logo ? { logo_url: logo } : {})
			});
			if (auth.usuario) auth.usuario = { ...auth.usuario, nombre: perfil.nombre };
			mensaje = 'Perfil actualizado';
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

<div class="max-w-2xl space-y-6">
	{#if perfil}
		<div class="rounded-xl border border-slate-200 bg-white p-6">
			<h3 class="font-semibold text-slate-800">Datos de contacto</h3>
			<p class="mt-1 text-sm text-slate-500">
				Comercio: <strong>{perfil.tenant_nombre}</strong>
			</p>
			<p class="mt-2 text-sm">
				<span class="text-slate-400">Idioma:</span>
				{#each idiomas as idioma}
					<button onclick={() => i18n.set(idioma.code)}
						class="ml-2 rounded-full px-3 py-0.5 text-xs font-semibold transition
							{i18n.locale === idioma.code ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}">
						{idioma.nombre}
					</button>
				{/each}
			</p>
			<form onsubmit={guardarNombre} class="mt-4 space-y-4">
				<div>
					<label for="nom" class="mb-1 block text-sm font-medium text-slate-700">Nombre</label>
					<input id="nom" type="text" bind:value={nombre} required minlength="2"
						class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
				</div>
				<div>
					<span class="mb-1 block text-sm font-medium text-slate-700">Logo del comercio</span>
					<ImageUploader bind:value={logo} carpeta="logo" aspecto="square" />
					<p class="mt-1 text-xs text-slate-400">Aparece en la app de clientes y en el kiosco.</p>
				</div>
				<div>
					<label for="cor" class="mb-1 block text-sm font-medium text-slate-700">Correo</label>
					<input id="cor" type="email" value={perfil.email} disabled
						class="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-400" />
					<p class="mt-1 text-xs text-slate-400">El correo es tu identificador de acceso y no puede cambiarse.</p>
				</div>
				{#if error}
					<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
				{/if}
				{#if mensaje}
					<p class="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{mensaje}</p>
				{/if}
				<button type="submit" disabled={guardando}
					class="rounded-lg bg-emerald-600 px-6 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
					{guardando ? 'Guardando…' : 'Guardar cambios'}
				</button>
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
