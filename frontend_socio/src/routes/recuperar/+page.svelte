<script lang="ts">
	import { page } from '$app/state';
	import { API_BASE } from '#lib/api/client';

	const token = $derived(page.url.searchParams.get('token') ?? '');

	let email = $state('');
	let password = $state('');
	let confirmar = $state('');
	let error = $state('');
	let mensaje = $state('');
	let cargando = $state(false);

	async function solicitar(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		cargando = true;
		try {
			const res = await fetch(`${API_BASE}/auth/forgot-password`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email })
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? 'Error');
			mensaje = data.detail ?? 'Si el correo existe, recibirás un enlace de recuperación.';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error de conexión';
		} finally {
			cargando = false;
		}
	}

	async function restablecer(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		if (password !== confirmar) {
			error = 'Las contraseñas no coinciden';
			return;
		}
		cargando = true;
		try {
			const res = await fetch(`${API_BASE}/auth/reset-password`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ token, password })
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? 'Enlace inválido o expirado');
			mensaje = 'Contraseña actualizada. Ya puedes iniciar sesión.';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error de conexión';
		} finally {
			cargando = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-slate-100 p-4">
	<div class="w-full max-w-sm rounded-2xl bg-white p-8 shadow-lg">
		<div class="mb-6 text-center">
			<span class="text-3xl font-bold text-slate-900">YAPAI</span>
			<span class="ml-2 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold text-white">SOCIO</span>
			<p class="mt-2 text-sm text-slate-500">
				{token ? 'Restablecer contraseña' : 'Recuperar acceso'}
			</p>
		</div>

		{#if mensaje}
			<div class="space-y-4 text-center">
				<p class="rounded-lg bg-emerald-50 px-3 py-3 text-sm text-emerald-700">{mensaje}</p>
				<a href="/login" class="text-sm text-emerald-600 hover:underline">Volver a iniciar sesión</a>
			</div>
		{:else if token}
			<form onsubmit={restablecer} class="space-y-4">
				<div>
					<label for="np" class="mb-1 block text-sm font-medium text-slate-700">Nueva contraseña</label>
					<input id="np" type="password" bind:value={password} required minlength="8"
						class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
				</div>
				<div>
					<label for="nc" class="mb-1 block text-sm font-medium text-slate-700">Confirmar contraseña</label>
					<input id="nc" type="password" bind:value={confirmar} required
						class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
				</div>
				{#if error}
					<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
				{/if}
				<button type="submit" disabled={cargando}
					class="w-full rounded-lg bg-emerald-600 py-2.5 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
					{cargando ? 'Guardando…' : 'Restablecer contraseña'}
				</button>
			</form>
		{:else}
			<form onsubmit={solicitar} class="space-y-4">
				<div>
					<label for="em" class="mb-1 block text-sm font-medium text-slate-700">Correo de tu cuenta</label>
					<input id="em" type="email" bind:value={email} required
						class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
				</div>
				{#if error}
					<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
				{/if}
				<button type="submit" disabled={cargando}
					class="w-full rounded-lg bg-emerald-600 py-2.5 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
					{cargando ? 'Enviando…' : 'Enviar enlace de recuperación'}
				</button>
				<p class="text-center text-sm">
					<a href="/login" class="text-slate-500 hover:underline">Volver a iniciar sesión</a>
				</p>
			</form>
		{/if}
	</div>
</div>
