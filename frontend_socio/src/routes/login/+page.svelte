<script lang="ts">
	import { goto } from '$app/navigation';
	import { API_BASE, fetchRed } from '#lib/api/client';
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
		if (usuario.rol !== 'owner' && usuario.rol !== 'cajero') {
			throw new Error('Este portal es solo para socios y su personal');
		}
		auth.guardar(tokens, usuario);
		goto(usuario.rol === 'cajero' ? '/terminal' : '/dashboard');
	}

	async function entrar(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		cargando = true;
		try {
			const res = await fetchRed(`${API_BASE}/auth/login`, {
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
			const res = await fetchRed(`${API_BASE}/auth/login/2fa`, {
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

<div class="flex min-h-screen items-center justify-center bg-slate-100 p-4 lg:bg-gradient-to-br lg:from-indigo-900 lg:via-indigo-950 lg:to-indigo-800 lg:p-8">
	<div class="w-full max-w-sm lg:grid lg:max-w-4xl lg:grid-cols-2 lg:overflow-hidden lg:rounded-3xl lg:shadow-2xl">

		<!-- Panel de marca (solo desktop) -->
		<div class="hidden flex-col justify-between bg-gradient-to-br from-indigo-800 to-indigo-950 p-10 text-white lg:flex">
			<div>
				<div class="flex items-center gap-2">
					<img src="/logo.png" alt="YAPAI" class="h-14 rounded-xl bg-white p-2" />
					<span class="rounded bg-emerald-600 px-2 py-1 text-xs font-bold text-white">SOCIO</span>
				</div>
				<h1 class="mt-8 text-3xl font-bold leading-tight">Tu programa de lealtad,<br />sin fricción.</h1>
				<p class="mt-3 text-sm leading-relaxed text-white/70">
					Fideliza clientes con QR en el mostrador, premios configurables
					y métricas en tiempo real. Sin apps, sin hardware.
				</p>
			</div>
			<div class="space-y-3">
				{#each [
					'Dashboard con métricas de tus clientes',
					'Terminal de canje con escáner QR',
					'Kiosco de registro en 15 segundos',
				] as f}
					<div class="flex items-center gap-3 text-sm text-white/80">
						<span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-emerald-400">✓</span>
						{f}
					</div>
				{/each}
			</div>
		</div>

		<!-- Formulario -->
		<div class="rounded-2xl bg-white p-8 shadow-lg lg:rounded-none lg:shadow-none">
		<div class="mb-8 text-center lg:hidden">
			<img src="/logo.png" alt="YAPAI" class="inline-block h-10" />
			<span class="ml-2 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold text-white align-middle">SOCIO</span>
			<p class="mt-2 text-sm text-slate-500">Portal del comercio afiliado</p>
		</div>
		<div class="mb-8 hidden lg:block">
			<h2 class="text-xl font-bold text-slate-900">Bienvenido de nuevo</h2>
			<p class="text-sm text-slate-500">Portal del comercio afiliado</p>
		</div>

		{#if etapa === 'credenciales'}
		<form onsubmit={entrar} class="space-y-4">
			<div>
				<label for="email" class="mb-1 block text-sm font-medium text-slate-700">{i18n.t('login.correo')}</label>
				<input id="email" type="email" bind:value={email} required
					class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
					placeholder="dueno@micomercio.com" />
			</div>
			<div>
				<label for="password" class="mb-1 block text-sm font-medium text-slate-700">{i18n.t('login.contrasena')}</label>
				<input id="password" type="password" bind:value={password} required
					class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
			</div>

			{#if error}
				<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
			{/if}

			<button type="submit" disabled={cargando}
				class="w-full rounded-lg bg-emerald-600 py-2.5 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
				{cargando ? i18n.t('login.ingresando') : i18n.t('login.ingresar')}
			</button>

			<p class="text-center text-sm">
				<a href="/recuperar" class="text-emerald-600 hover:underline">{i18n.t('login.olvidaste')}</a>
			</p>
			<p class="text-center text-sm text-slate-500">
				{i18n.t('login.sin_cuenta')} <a href="/registro" class="font-medium text-emerald-600 hover:underline">{i18n.t('login.registrate')}</a>
			</p>
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
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-center text-xl tracking-[0.3em] focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
					placeholder="000000" />
			</div>

			{#if error}
				<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
			{/if}

			<button type="submit" disabled={cargando}
				class="w-full rounded-lg bg-emerald-600 py-2.5 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
				{cargando ? i18n.t('login.verificando') : i18n.t('login.verificar')}
			</button>
			<button type="button" onclick={() => { etapa = 'credenciales'; codigo = ''; error = ''; }}
				class="w-full text-sm text-slate-500 hover:underline">{i18n.t('login.volver')}</button>
		</form>
		{/if}
		</div>
	</div>
</div>
