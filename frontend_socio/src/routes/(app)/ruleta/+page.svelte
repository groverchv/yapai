<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import type { Segmento } from '#lib/types';

	let segmentos = $state<Segmento[]>([]);
	let cargando = $state(true);
	let error = $state('');
	let mensaje = $state('');

	let modal = $state<'crear' | 'editar' | null>(null);
	let seleccionado = $state<Segmento | null>(null);
	let formEtiqueta = $state('');
	let formPuntos = $state(0);
	let formPeso = $state(1);
	let formColor = $state('');
	let guardando = $state(false);
	let errorModal = $state('');

	const PESO_TOTAL_REF = 'La probabilidad de cada segmento es peso ÷ suma de pesos activos.';

	async function cargar() {
		cargando = true;
		error = '';
		try {
			segmentos = await api.get<Segmento[]>('/socio/ruleta/segmentos');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error al cargar';
		} finally {
			cargando = false;
		}
	}

	function abrirCrear() {
		seleccionado = null;
		formEtiqueta = '';
		formPuntos = 0;
		formPeso = 1;
		formColor = '';
		errorModal = '';
		modal = 'crear';
	}

	function abrirEditar(s: Segmento) {
		seleccionado = s;
		formEtiqueta = s.etiqueta;
		formPuntos = s.puntos;
		formPeso = s.peso;
		formColor = s.color ?? '';
		errorModal = '';
		modal = 'editar';
	}

	async function guardar(e: SubmitEvent) {
		e.preventDefault();
		guardando = true;
		errorModal = '';
		try {
			const body = {
				etiqueta: formEtiqueta,
				puntos: formPuntos,
				peso: formPeso,
				color: formColor || null
			};
			if (modal === 'crear') await api.post('/socio/ruleta/segmentos', { ...body, activo: true });
			else if (seleccionado) await api.patch(`/socio/ruleta/segmentos/${seleccionado.id}`, body);
			modal = null;
			cargar();
		} catch (err) {
			errorModal = err instanceof Error ? err.message : 'Error al guardar';
		} finally {
			guardando = false;
		}
	}

	async function toggleActivo(s: Segmento) {
		error = '';
		try {
			await api.patch(`/socio/ruleta/segmentos/${s.id}`, { activo: !s.activo });
			cargar();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error';
		}
	}

	async function eliminar(s: Segmento) {
		error = '';
		mensaje = '';
		try {
			await api.delete(`/socio/ruleta/segmentos/${s.id}`);
			mensaje = `Segmento "${s.etiqueta}" eliminado`;
			cargar();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error';
		}
	}

	let pesoTotal = $derived(segmentos.filter((s) => s.activo).reduce((a, s) => a + s.peso, 0));

	onMount(cargar);
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<p class="max-w-xl text-sm text-slate-500">{PESO_TOTAL_REF}</p>
		<button onclick={abrirCrear}
			class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
			+ Nuevo segmento
		</button>
	</div>

	{#if error}
		<p class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
	{/if}
	{#if mensaje}
		<p class="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{mensaje}</p>
	{/if}

	{#if cargando}
		<p class="text-slate-500">Cargando…</p>
	{:else}
		<div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
			<table class="w-full text-left text-sm">
				<thead>
					<tr class="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
						<th class="px-4 py-3 font-semibold">Etiqueta</th>
						<th class="px-4 py-3 font-semibold">Puntos</th>
						<th class="px-4 py-3 font-semibold">Peso</th>
						<th class="px-4 py-3 font-semibold">Probabilidad</th>
						<th class="px-4 py-3 font-semibold">Estado</th>
						<th class="px-4 py-3 text-right font-semibold">Acciones</th>
					</tr>
				</thead>
				<tbody>
					{#each segmentos as s}
						<tr class="border-b border-slate-100 hover:bg-slate-50">
							<td class="px-4 py-3">
								<span class="mr-2 inline-block h-4 w-4 rounded-full align-middle"
									style="background:{s.color ?? '#94a3b8'}"></span>
								{s.etiqueta}
							</td>
							<td class="px-4 py-3 font-semibold text-emerald-600">{s.puntos} pts</td>
							<td class="px-4 py-3">{s.peso}</td>
							<td class="px-4 py-3 text-slate-500">
								{s.activo && pesoTotal > 0 ? `${((s.peso / pesoTotal) * 100).toFixed(1)}%` : '—'}
							</td>
							<td class="px-4 py-3">
								<Badge texto={s.activo ? 'Activo' : 'Inactivo'} variante={s.activo ? 'ok' : 'neutral'} />
							</td>
							<td class="px-4 py-3">
								<div class="flex justify-end gap-2 text-xs">
									<button onclick={() => abrirEditar(s)} class="text-emerald-600 hover:underline">Editar</button>
									<button onclick={() => toggleActivo(s)} class="text-sky-600 hover:underline">
										{s.activo ? 'Desactivar' : 'Activar'}
									</button>
									<button onclick={() => eliminar(s)} class="text-red-600 hover:underline">Eliminar</button>
								</div>
							</td>
						</tr>
					{:else}
						<tr><td colspan="6" class="px-4 py-10 text-center text-slate-500">Sin segmentos</td></tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>

<Modal abierto={modal !== null} titulo={modal === 'crear' ? 'Nuevo segmento' : 'Editar segmento'}
	onclose={() => (modal = null)}>
	<form onsubmit={guardar} class="space-y-4">
		<div>
			<label for="et" class="mb-1 block text-sm font-medium text-slate-700">Etiqueta (texto en la ruleta)</label>
			<input id="et" type="text" bind:value={formEtiqueta} required placeholder="Ej: 50 pts"
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
		</div>
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
			<div>
				<label for="pt" class="mb-1 block text-sm font-medium text-slate-700">Puntos que otorga</label>
				<input id="pt" type="number" bind:value={formPuntos} required min="0"
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
			</div>
			<div>
				<label for="pe" class="mb-1 block text-sm font-medium text-slate-700">Peso (probabilidad)</label>
				<input id="pe" type="number" bind:value={formPeso} required min="1"
					class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
			</div>
		</div>
		<div>
			<label for="co" class="mb-1 block text-sm font-medium text-slate-700">Color (hex, opcional)</label>
			<input id="co" type="text" bind:value={formColor} placeholder="#1abc9c"
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
		</div>
		{#if errorModal}
			<p class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{errorModal}</p>
		{/if}
		<button type="submit" disabled={guardando}
			class="w-full rounded-lg bg-emerald-600 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
			{guardando ? 'Guardando…' : 'Guardar segmento'}
		</button>
	</form>
</Modal>
