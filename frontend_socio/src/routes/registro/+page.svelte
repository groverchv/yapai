<script lang="ts">
	import { goto } from '$app/navigation';
	import { API_BASE, fetchRed } from '#lib/api/client';
	import { auth } from '#lib/stores/auth.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import type { SignupResponse } from '#lib/types';

	let negocio = $state('');
	let nombre = $state('');
	let email = $state('');
	let telefono = $state('');
	let password = $state('');
	let error = $state('');
	let cargando = $state(false);
	let pendiente = $state(false);

	async function registrar(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		cargando = true;
		try {
			const res = await fetchRed(`${API_BASE}/auth/signup`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					negocio_nombre: negocio,
					owner_nombre: nombre,
					email,
					password,
					telefono: telefono || null
				})
			});
			const data = await res.json().catch(() => null);
			if (!res.ok) {
				const d = data?.detail;
				throw new Error(typeof d === 'string' ? d : (d?.mensaje ?? 'No se pudo crear la cuenta'));
			}
			const r: SignupResponse = data;
			if (r.aprobado && r.tokens && r.usuario) {
				auth.guardar(r.tokens, r.usuario);
				goto('/dashboard');
			} else {
				pendiente = true;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error de conexión';
		} finally {
			cargando = false;
		}
	}
</script>

<svelte:head><title>Crea tu cuenta — YAPAI</title></svelte:head>

<div class="flex min-h-screen items-center justify-center bg-slate-100 p-4">
	<div class="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
		{#if pendiente}
			<div class="text-center">
				<span class="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-50 text-amber-500"><Icon name="info" clase="h-7 w-7" /></span>
				<h1 class="mt-4 text-xl font-bold text-indigo-950">Cuenta en revisión</h1>
				<p class="mt-2 text-sm text-slate-600">
					Recibimos tu registro. El equipo YAPAI revisará <strong>{negocio}</strong> y te
					avisaremos a <strong>{email}</strong> cuando esté activo.
				</p>
				<a href="/" class="mt-6 inline-block rounded-lg border border-slate-300 px-5 py-2 text-sm font-semibold text-slate-700 hover:border-emerald-500">
					Volver al inicio
				</a>
			</div>
		{:else}
			<div class="mb-6 text-center">
				<img src="/logo.png" alt="YAPAI" class="inline-block h-10" />
				<h1 class="mt-3 text-xl font-bold text-indigo-950">Crea tu programa de puntos</h1>
				<p class="mt-1 text-sm text-slate-500">14 días gratis · Sin tarjeta</p>
			</div>

			<form onsubmit={registrar} class="space-y-4">
				<div>
					<label for="neg" class="mb-1 block text-sm font-medium text-slate-700">Nombre del comercio</label>
					<input id="neg" bind:value={negocio} required minlength="2"
						class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
						placeholder="Pizzería Don Mario" />
				</div>
				<div>
					<label for="nom" class="mb-1 block text-sm font-medium text-slate-700">Tu nombre</label>
					<input id="nom" bind:value={nombre} required minlength="2"
						class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
						placeholder="Mario Pérez" />
				</div>
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
					<div>
						<label for="em" class="mb-1 block text-sm font-medium text-slate-700">Correo</label>
						<input id="em" type="email" bind:value={email} required
							class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
							placeholder="mario@correo.com" />
					</div>
					<div>
						<label for="tel" class="mb-1 block text-sm font-medium text-slate-700">Teléfono</label>
						<input id="tel" bind:value={telefono}
							class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
							placeholder="70000000" />
					</div>
				</div>
				<div>
					<label for="pw" class="mb-1 block text-sm font-medium text-slate-700">Contraseña</label>
					<input id="pw" type="password" bind:value={password} required minlength="8"
						class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
						placeholder="Mínimo 8 caracteres" />
				</div>

				{#if error}
					<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
				{/if}

				<button type="submit" disabled={cargando}
					class="w-full rounded-lg bg-emerald-600 py-2.5 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
					{cargando ? 'Creando cuenta…' : 'Crear mi cuenta gratis'}
				</button>

				<p class="text-center text-sm text-slate-500">
					¿Ya tienes cuenta? <a href="/login" class="font-medium text-emerald-600 hover:underline">Ingresa</a>
				</p>
			</form>
		{/if}
	</div>
</div>
