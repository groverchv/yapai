<script lang="ts">
	import { page } from '$app/state';
	import { API_BASE, fetchRed } from '#lib/api/client';

	let password = $state('');
	let confirmar = $state('');
	let error = $state('');
	let listo = $state(false);
	let cargando = $state(false);

	const token = $derived(page.url.searchParams.get('token') ?? '');

	async function activar(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		if (password !== confirmar) {
			error = 'Las contraseñas no coinciden';
			return;
		}
		cargando = true;
		try {
			const res = await fetchRed(`${API_BASE}/auth/onboarding`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ token, password })
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? 'Enlace inválido o expirado');
			listo = true;
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
			<p class="mt-2 text-sm text-slate-500">Activa tu cuenta</p>
		</div>

		{#if !token}
			<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
				Enlace inválido: falta el token de activación.
			</p>
		{:else if listo}
			<div class="space-y-4 text-center">
				<p class="rounded-lg bg-emerald-50 px-3 py-3 text-sm text-emerald-700">
					¡Cuenta activada! Ya puedes iniciar sesión.
				</p>
				<a href="/login" class="inline-block rounded-lg bg-emerald-600 px-6 py-2.5 font-semibold text-white hover:bg-emerald-700">
					Ir a iniciar sesión
				</a>
			</div>
		{:else}
			<form onsubmit={activar} class="space-y-4">
				<div>
					<label for="p1" class="mb-1 block text-sm font-medium text-slate-700">Nueva contraseña</label>
					<input id="p1" type="password" bind:value={password} required minlength="8"
						class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
					<p class="mt-1 text-xs text-slate-400">Mínimo 8 caracteres</p>
				</div>
				<div>
					<label for="p2" class="mb-1 block text-sm font-medium text-slate-700">Confirmar contraseña</label>
					<input id="p2" type="password" bind:value={confirmar} required
						class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
				</div>

				{#if error}
					<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
				{/if}

				<button type="submit" disabled={cargando}
					class="w-full rounded-lg bg-emerald-600 py-2.5 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
					{cargando ? 'Activando…' : 'Establecer contraseña'}
				</button>
			</form>
		{/if}
	</div>
</div>
