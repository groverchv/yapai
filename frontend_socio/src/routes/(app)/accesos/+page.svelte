<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import type { PinConfig } from '#lib/types';

	let config = $state<PinConfig | null>(null);
	let error = $state('');
	let mensaje = $state('');

	let modalPin = $state<{ tipo: 'sucursal' | 'cajero'; id: number; nombre: string } | null>(null);
	let pin = $state('');
	let guardando = $state(false);
	let errorModal = $state('');

	async function cargar() {
		error = '';
		try {
			config = await api.get<PinConfig>('/socio/pin/config');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cargar';
		}
	}

	async function cambiarModo(modo: 'por_sucursal' | 'por_cajero') {
		error = '';
		mensaje = '';
		try {
			config = await api.put<PinConfig>('/socio/pin/config', { modo });
			mensaje = 'Modalidad actualizada';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cambiar modalidad';
		}
	}

	function abrirPin(tipo: 'sucursal' | 'cajero', id: number, nombre: string) {
		modalPin = { tipo, id, nombre };
		pin = '';
		errorModal = '';
	}

	async function guardarPin(e: SubmitEvent) {
		e.preventDefault();
		if (!modalPin) return;
		if (!/^\d{4}$/.test(pin)) {
			errorModal = 'El PIN debe tener exactamente 4 dígitos';
			return;
		}
		guardando = true;
		errorModal = '';
		try {
			await api.post(`/socio/pin/${modalPin.tipo}/${modalPin.id}`, { pin });
			modalPin = null;
			mensaje = 'PIN actualizado correctamente';
			cargar();
		} catch (err) {
			errorModal = err instanceof Error ? err.message : 'Error al guardar';
		} finally {
			guardando = false;
		}
	}

	onMount(cargar);
</script>

<div class="max-w-3xl space-y-6">
	<div class="rounded-xl border border-slate-200 bg-white p-5">
		<h3 class="font-semibold text-slate-800">Modalidad del PIN</h3>
		<p class="mt-1 text-sm text-slate-500">
			El PIN habilita la ruleta en las pantallas físicas del local.
		</p>
		<div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
			<button onclick={() => cambiarModo('por_sucursal')}
				class="rounded-xl border-2 p-4 text-left transition
					{config?.modo === 'por_sucursal' ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 hover:border-slate-300'}">
				<p class="font-semibold text-slate-800">PIN por sucursal</p>
				<p class="mt-1 text-xs text-slate-500">Un mismo código para todo el local.</p>
			</button>
			<button onclick={() => cambiarModo('por_cajero')}
				class="rounded-xl border-2 p-4 text-left transition
					{config?.modo === 'por_cajero' ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 hover:border-slate-300'}">
				<p class="font-semibold text-slate-800">PIN por cajero</p>
				<p class="mt-1 text-xs text-slate-500">Código individual por empleado; se registra quién habilitó el juego.</p>
			</button>
		</div>
	</div>

	{#if error}
		<p class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
	{/if}
	{#if mensaje}
		<p class="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{mensaje}</p>
	{/if}

	{#if config}
		{#if config.modo === 'por_sucursal'}
			<div class="rounded-xl border border-slate-200 bg-white p-5">
				<h3 class="font-semibold text-slate-800">PINs por sucursal</h3>
				<div class="mt-3 space-y-2">
					{#each config.sucursales as s}
						<div class="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
							<div class="flex items-center gap-2">
								<span class="text-sm font-medium text-slate-700">{s.nombre}</span>
								<Badge texto={s.pin_set ? 'PIN configurado' : 'Sin PIN'}
									variante={s.pin_set ? 'ok' : 'warn'} />
							</div>
							<button onclick={() => abrirPin('sucursal', s.id, s.nombre)}
								class="text-sm text-emerald-600 hover:underline">
								{s.pin_set ? 'Rotar PIN' : 'Configurar PIN'}
							</button>
						</div>
					{:else}
						<p class="text-sm text-slate-400">No tienes sucursales registradas.</p>
					{/each}
				</div>
			</div>
		{:else}
			<div class="rounded-xl border border-slate-200 bg-white p-5">
				<h3 class="font-semibold text-slate-800">PINs por cajero</h3>
				<div class="mt-3 space-y-2">
					{#each config.cajeros as c}
						<div class="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
							<div class="flex items-center gap-2">
								<span class="text-sm font-medium text-slate-700">{c.nombre}</span>
								<Badge texto={c.pin_set ? 'PIN configurado' : 'Sin PIN'}
									variante={c.pin_set ? 'ok' : 'warn'} />
							</div>
							<button onclick={() => abrirPin('cajero', c.id, c.nombre)}
								class="text-sm text-emerald-600 hover:underline">
								{c.pin_set ? 'Rotar PIN' : 'Configurar PIN'}
							</button>
						</div>
					{:else}
						<p class="text-sm text-slate-400">No tienes cajeros registrados.</p>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div>

<Modal abierto={modalPin !== null} titulo="Configurar PIN — {modalPin?.nombre ?? ''}"
	onclose={() => (modalPin = null)}>
	<form onsubmit={guardarPin} class="space-y-4">
		<div>
			<label for="pin" class="mb-1 block text-sm font-medium text-slate-700">PIN numérico (4 dígitos)</label>
			<input id="pin" type="password" bind:value={pin} required inputmode="numeric"
				maxlength="4" pattern="\d{'{'}4{'}'}"
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-center text-2xl tracking-[0.5em]" />
		</div>
		{#if errorModal}
			<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{errorModal}</p>
		{/if}
		<button type="submit" disabled={guardando}
			class="w-full rounded-lg bg-emerald-600 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
			{guardando ? 'Guardando…' : 'Guardar PIN'}
		</button>
	</form>
</Modal>
