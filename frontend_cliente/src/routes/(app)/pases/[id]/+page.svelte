<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { api, mensajeError } from '#lib/api/client';
	import type { Pase } from '#lib/types';
	import { fecha } from '#lib/utils/format';
	import AppTopBar from '#lib/components/AppTopBar.svelte';
	import Dialog from '#lib/components/ui/Dialog.svelte';
	import QrImg from '#lib/components/ui/QrImg.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import Spinner from '#lib/components/ui/Spinner.svelte';
	import { toast } from '#lib/stores/toast.svelte';
	import { onMount } from 'svelte';

	const id = $derived(Number(page.params.id));

	let pase = $state<Pase | null>(null);
	let cargando = $state(true);
	let error = $state('');
	let confirmarCancel = $state(false);
	let cancelando = $state(false);

	const activo = $derived(pase?.estado === 'activo');

	async function cargar() {
		cargando = true;
		error = '';
		try {
			const data = await api.get<Pase[]>('/cliente/pases');
			pase = data.find((p) => p.id === id) ?? null;
			if (!pase) error = 'Pase no encontrado';
		} catch (e) {
			error = mensajeError(e);
		} finally {
			cargando = false;
		}
	}

	async function cancelar() {
		if (!pase) return;
		cancelando = true;
		try {
			await api.post(`/cliente/pases/${pase.id}/cancelar`);
			toast.exito('Pase cancelado; puntos liberados');
			goto('/pases');
		} catch (e) {
			cancelando = false;
			toast.error(mensajeError(e));
		}
	}

	onMount(cargar);
</script>

<AppTopBar titulo="Pase digital" atras="/pases" />

{#if cargando}
	<div class="flex h-[60dvh] items-center justify-center text-indigo-600"><Spinner clase="h-8 w-8" /></div>
{:else if error || !pase}
	<div class="flex h-[60dvh] flex-col items-center justify-center gap-2">
		<p class="text-sm text-red-600">{error || 'Pase no encontrado'}</p>
		<button onclick={() => goto('/pases')} class="text-sm font-medium text-indigo-600 hover:underline">Volver a mis pases</button>
	</div>
{:else}
	<div class="mx-auto flex w-full max-w-lg flex-col items-center px-6 py-8 text-center lg:rounded-2xl lg:bg-white lg:p-10 lg:shadow-sm lg:ring-1 lg:ring-black/5">
		<h2 class="text-[22px] font-bold">{pase.premio_nombre}</h2>
		<p class="mt-1 text-sm text-gray-500">{pase.comercio} · {pase.puntos} pts</p>
		<span class="mt-2 rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-wide
			{activo ? 'bg-green-50 text-green-700' : 'bg-gray-200 text-gray-600'}">
			{pase.estado}
		</span>

		{#if activo}
			<div class="mt-6 rounded-2xl border border-gray-300 bg-white p-4">
				<QrImg data={pase.codigo_qr} size={240} />
			</div>
			<p class="mt-5 text-sm text-gray-600">Si la cámara falla, dicta este PIN al cajero:</p>
			<div class="mt-2 rounded-xl bg-gray-100 px-6 py-2.5">
				<span class="font-mono text-[32px] font-bold tracking-[6px]">{pase.pin_corto}</span>
			</div>
			<p class="mt-4 text-xs text-gray-400">Válido hasta {fecha(pase.expira_en)}</p>
			<button onclick={() => (confirmarCancel = true)} disabled={cancelando}
				class="mt-6 flex items-center gap-2 rounded-xl border border-red-300 px-5 py-2.5 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-60">
				<Icon name="x-circle" clase="h-4 w-4" />
				{cancelando ? 'Cancelando…' : 'Cancelar pase y liberar puntos'}
			</button>
		{:else}
			<div class="py-8">
				<Icon name={pase.estado === 'canjeado' ? 'check-circle' : 'x-circle'}
					clase="h-20 w-20 {pase.estado === 'canjeado' ? 'text-green-500' : 'text-gray-300'}" />
			</div>
		{/if}
	</div>
{/if}

<Dialog abierto={confirmarCancel} titulo="Cancelar pase"
	texConfirmar="Cancelar pase" peligroso
	oncerrar={() => (confirmarCancel = false)}
	onConfirmar={cancelar}>
	Se liberarán los puntos congelados y volverán a tu billetera de inmediato.
</Dialog>
