<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { fetchRed, API_BASE } from '#lib/api/client';
	import logo from '#lib/assets/logo.png';

	let estado = $state<'cargando' | 'ok' | 'error'>('cargando');
	let mensaje = $state('');

	onMount(async () => {
		const token = page.url.searchParams.get('token') ?? '';
		if (!token) {
			estado = 'error';
			mensaje = 'El enlace no es válido.';
			return;
		}
		try {
			const res = await fetchRed(`${API_BASE}/auth/verificar-email`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ token })
			});
			const data = await res.json().catch(() => null);
			if (!res.ok) throw new Error(data?.detail ?? 'Token inválido o expirado');
			estado = 'ok';
		} catch (e) {
			estado = 'error';
			mensaje = e instanceof Error ? e.message : 'No se pudo verificar el correo';
		}
	});
</script>

<div class="flex min-h-dvh items-center justify-center bg-slate-50 px-4">
	<div class="w-full max-w-sm rounded-2xl bg-white p-8 text-center shadow-sm">
		<img src={logo} alt="YAPAI" class="mx-auto h-10" />
		{#if estado === 'cargando'}
			<p class="mt-6 text-sm text-slate-500">Verificando tu correo…</p>
		{:else if estado === 'ok'}
			<h1 class="mt-6 text-xl font-bold text-slate-900">¡Correo verificado!</h1>
			<p class="mt-2 text-sm text-slate-600">Tu dirección quedó confirmada. Ya puedes usar tu portal con normalidad.</p>
		{:else}
			<h1 class="mt-6 text-xl font-bold text-slate-900">No se pudo verificar</h1>
			<p class="mt-2 text-sm text-slate-600">{mensaje} Puedes pedir un enlace nuevo desde tu perfil.</p>
		{/if}
		<a href="/login" class="mt-6 inline-block rounded-lg bg-emerald-600 px-5 py-2 text-sm font-semibold text-white hover:bg-emerald-700">
			Ir al portal
		</a>
	</div>
</div>
