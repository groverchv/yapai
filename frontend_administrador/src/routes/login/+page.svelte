<script lang="ts">
	import { goto } from '$app/navigation';
	import { API_BASE } from '#lib/api/client';
	import { i18n } from '#lib/i18n.svelte';
	import { auth } from '#lib/stores/auth.svelte';
	import type { TokenPair, UsuarioMe } from '#lib/types';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let cargando = $state(false);
	let etapa = $state<'credenciales' | 'codigo'>('credenciales');
	let preToken = $state('');
	let codigo = $state('');

	function entrarConTokens(data: { tokens: TokenPair; usuario: UsuarioMe }) {
		const { tokens, usuario } = data;
		if (usuario.rol !== 'superadmin') {
			throw new Error('Este portal es solo para administradores YAPAI');
		}
		auth.guardar(tokens, usuario);
		goto('/dashboard');
	}

	async function entrar(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		cargando = true;
		try {
			const res = await fetch(`${API_BASE}/auth/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email, password })
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? i18n.t('login.error_auth'));
			if (data.requires_2fa) {
				preToken = data.pre_token;
				etapa = 'codigo';
				return;
			}
			entrarConTokens(data);
		} catch (err) {
			error = err instanceof Error ? err.message : i18n.t('login.error_conexion');
		} finally {
			cargando = false;
		}
	}

	async function verificar(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		cargando = true;
		try {
			const res = await fetch(`${API_BASE}/auth/login/2fa`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ pre_token: preToken, codigo: codigo.replace(/\s/g, '') })
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? i18n.t('login.error_auth'));
			entrarConTokens(data);
		} catch (err) {
			error = err instanceof Error ? err.message : i18n.t('login.error_conexion');
		} finally {
			cargando = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-slate-100 p-4">
	<div class="w-full max-w-sm rounded-2xl bg-white p-8 shadow-lg">
		<div class="mb-8 text-center">
			<img src="/logo.png" alt="YAPAI" class="inline-block h-10" />
			<span class="ml-2 rounded bg-indigo-600 px-1.5 py-0.5 text-[10px] font-bold text-white align-middle">ADMIN</span>
			<p class="mt-2 text-sm text-slate-500">Portal de administración interna</p>
		</div>

		{#if etapa === 'credenciales'}
		<form onsubmit={entrar} class="space-y-4">
			<div>
				<label for="email" class="mb-1 block text-sm font-medium text-slate-700">{i18n.t('login.correo')}</label>
				<input id="email" type="email" bind:value={email} required
					class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
					placeholder="admin@yapai.com" />
			</div>
			<div>
				<label for="password" class="mb-1 block text-sm font-medium text-slate-700">{i18n.t('login.contrasena')}</label>
				<input id="password" type="password" bind:value={password} required
					class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500" />
			</div>

			{#if error}
				<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
			{/if}

			<button type="submit" disabled={cargando}
				class="w-full rounded-lg bg-indigo-600 py-2.5 font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
				{cargando ? i18n.t('login.ingresando') : i18n.t('login.ingresar')}
			</button>
		</form>
		{:else}
		<form onsubmit={verificar} class="space-y-4">
			<p class="text-sm text-slate-600">
				{i18n.t('login.ayuda_2fa')}
			</p>
			<div>
				<label for="codigo" class="mb-1 block text-sm font-medium text-slate-700">{i18n.t('login.codigo')}</label>
				<input id="codigo" type="text" inputmode="numeric" autocomplete="one-time-code"
					bind:value={codigo} required minlength="6" maxlength="8"
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-center text-xl tracking-[0.3em] focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
					placeholder="000000" />
			</div>

			{#if error}
				<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
			{/if}

			<button type="submit" disabled={cargando}
				class="w-full rounded-lg bg-indigo-600 py-2.5 font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
				{cargando ? i18n.t('login.verificando') : i18n.t('login.verificar')}
			</button>
			<button type="button" onclick={() => { etapa = 'credenciales'; codigo = ''; error = ''; }}
				class="w-full text-sm text-slate-500 hover:underline">{i18n.t('login.volver')}</button>
		</form>
		{/if}
	</div>
</div>
