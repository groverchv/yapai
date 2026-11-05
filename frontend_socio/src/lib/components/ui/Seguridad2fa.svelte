<script lang="ts">
	import { api } from '#lib/api/client';
	import { auth } from '#lib/stores/auth.svelte';
	import { toast } from '#lib/stores/toast.svelte';
	import Icon from './Icon.svelte';
	import Modal from './Modal.svelte';

	interface TotpSetup {
		secret: string;
		provisioning_uri: string;
		qr_svg: string;
	}

	let setup = $state<TotpSetup | null>(null);
	let codigo = $state('');
	let error = $state('');
	let cargando = $state(false);
	let modalOff = $state(false);
	let passOff = $state('');

	async function iniciar() {
		error = '';
		cargando = true;
		try {
			setup = await api.post<TotpSetup>('/auth/2fa/setup', {});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al iniciar';
		} finally {
			cargando = false;
		}
	}

	async function activar(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		cargando = true;
		try {
			await api.post('/auth/2fa/habilitar', { codigo: codigo.replace(/\s/g, '') });
			if (auth.usuario) auth.usuario = { ...auth.usuario, totp_habilitado: true };
			setup = null;
			codigo = '';
			toast.exito('Verificación en dos pasos activada');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al activar';
		} finally {
			cargando = false;
		}
	}

	async function desactivar(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		cargando = true;
		try {
			await api.post('/auth/2fa/deshabilitar', { password: passOff });
			if (auth.usuario) auth.usuario = { ...auth.usuario, totp_habilitado: false };
			modalOff = false;
			passOff = '';
			toast.exito('Verificación en dos pasos desactivada');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al desactivar';
		} finally {
			cargando = false;
		}
	}
</script>

<div class="rounded-xl border border-slate-200 bg-white p-6">
	<div class="flex items-start justify-between">
		<div>
			<h3 class="flex items-center gap-2 font-semibold text-slate-800">
				<Icon name="shield" clase="h-4 w-4 text-emerald-600" />
				Verificación en dos pasos (2FA)
			</h3>
			<p class="mt-1 text-xs text-slate-500">
				Protege tu cuenta pidiendo un código de tu app de autenticación al entrar.
			</p>
		</div>
		{#if auth.usuario?.totp_habilitado}
			<span class="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">Activo</span>
		{:else}
			<span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-500">Inactivo</span>
		{/if}
	</div>

	{#if !setup}
		<div class="mt-4">
			{#if auth.usuario?.totp_habilitado}
				<button onclick={() => { modalOff = true; error = ''; }}
					class="rounded-lg border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-50">
					Desactivar 2FA
				</button>
			{:else}
				<button onclick={iniciar} disabled={cargando}
					class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
					{cargando ? 'Generando…' : 'Activar 2FA'}
				</button>
			{/if}
		</div>
	{:else}
		<div class="mt-4 space-y-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
			<p class="text-sm text-slate-600">
				Escanea este QR con <strong>Google Authenticator</strong>, <strong>Microsoft Authenticator</strong> o cualquier app TOTP:
			</p>
			<div class="flex justify-center rounded-lg bg-white p-4">
				<!-- eslint-disable-next-line svelte/no-at-html-tags -->
				{@html setup.qr_svg}
			</div>
			<div>
				<p class="text-xs text-slate-500">O ingresa el código manualmente:</p>
				<code class="mt-1 block rounded bg-slate-100 px-3 py-2 text-center font-mono text-sm tracking-widest text-slate-800 select-all">
					{setup.secret}
				</code>
			</div>
			<form onsubmit={activar} class="space-y-3">
				<label for="totp-code" class="block text-sm font-medium text-slate-700">
					Ingresa el código de 6 dígitos para confirmar
				</label>
				<input id="totp-code" type="text" inputmode="numeric" autocomplete="one-time-code"
					bind:value={codigo} required minlength="6" maxlength="8"
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-center text-lg tracking-[0.3em]"
					placeholder="000000" />
				{#if error}
					<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
				{/if}
				<div class="flex gap-2">
					<button type="submit" disabled={cargando}
						class="flex-1 rounded-lg bg-emerald-600 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
						{cargando ? 'Verificando…' : 'Confirmar y activar'}
					</button>
					<button type="button" onclick={() => { setup = null; codigo = ''; error = ''; }}
						class="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-100">
						Cancelar
					</button>
				</div>
			</form>
		</div>
	{/if}
</div>

<Modal abierto={modalOff} titulo="Desactivar 2FA" onclose={() => (modalOff = false)}>
	<form onsubmit={desactivar} class="space-y-4">
		<p class="text-sm text-slate-600">
			Confirma tu contraseña para desactivar la verificación en dos pasos.
		</p>
		<div>
			<label for="pass-off" class="mb-1 block text-sm font-medium text-slate-700">Contraseña</label>
			<input id="pass-off" type="password" bind:value={passOff} required
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
		</div>
		{#if error}
			<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
		{/if}
		<button type="submit" disabled={cargando}
			class="w-full rounded-lg bg-red-600 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50">
			{cargando ? 'Desactivando…' : 'Desactivar'}
		</button>
	</form>
</Modal>
