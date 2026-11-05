<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, mensajeError } from '#lib/api/client';
	import { auth } from '#lib/stores/auth.svelte';
	import { toast } from '#lib/stores/toast.svelte';
	import type { Comunicado, Movimiento, Pagina, ProximoPremio, Wallet } from '#lib/types';
	import { cloudinaryThumb, compartir, fecha, vence } from '#lib/utils/format';
	import TarjetaId from '#lib/components/TarjetaId.svelte';
	import ProximoPremioCard from '#lib/components/ProximoPremioCard.svelte';
	import OfertaTile from '#lib/components/OfertaTile.svelte';
	import MovimientoTile from '#lib/components/MovimientoTile.svelte';
	import BottomSheet from '#lib/components/ui/BottomSheet.svelte';
	import QrImg from '#lib/components/ui/QrImg.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import Skeleton from '#lib/components/ui/Skeleton.svelte';
	import PullRefresh from '#lib/components/ui/PullRefresh.svelte';
	import { onMount } from 'svelte';

	let wallet = $state<Wallet | null>(null);
	let proximo = $state<ProximoPremio | null>(null);
	let movimientos = $state<Movimiento[]>([]);
	let comunicados = $state<Comunicado[]>([]);
	let error = $state('');
	let cargando = $state(true);
	let subiendoFoto = $state(false);

	let verHistorial = $state(false);
	let verQr = $state(false);
	let ofertaSel = $state<Comunicado | null>(null);
	let inputFoto: HTMLInputElement;

	const cliente = $derived(auth.cliente);
	const codigoRef = $derived(cliente?.codigo_referido ?? (cliente ? `YAPAI-${cliente.id}` : ''));

	async function cargar() {
		cargando = true;
		error = '';
		try {
			const [w, m, c] = await Promise.all([
				api.get<Wallet>('/cliente/wallet'),
				api.get<Pagina<Movimiento>>('/cliente/movimientos?size=50'),
				api.get<Pagina<Comunicado>>('/cliente/comunicados?size=30'),
			]);
			let p: ProximoPremio | null = null;
			try {
				p = await api.get<ProximoPremio>('/cliente/proximo-premio');
			} catch {
				p = null; // 404: aún no hay premios publicados
			}
			wallet = w;
			movimientos = m.items;
			comunicados = c.items;
			proximo = p;
		} catch (e) {
			error = mensajeError(e);
		} finally {
			cargando = false;
		}
	}

	async function cambiarFoto(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		input.value = '';
		if (!file) return;
		subiendoFoto = true;
		try {
			await auth.subirFoto(file);
		} catch (err) {
			toast.error(mensajeError(err) === 'Sin conexión' ? 'Error al subir' : mensajeError(err));
		} finally {
			subiendoFoto = false;
		}
	}

	async function compartirCodigo() {
		const res = await compartir(
			`¡Únete a YAPAI con mi código ${codigoRef} y gana puntos en tus comercios favoritos!`
		);
		if (res === 'copied') toast.exito('Código copiado');
	}

	onMount(cargar);
</script>

<input bind:this={inputFoto} type="file" accept="image/*" class="hidden" onchange={cambiarFoto} />


<PullRefresh onRefresh={cargar}>
	<div class="p-4 lg:grid lg:w-full lg:grid-cols-[minmax(340px,420px)_1fr] lg:items-start lg:gap-8 lg:p-8">
		<div class="space-y-4">
			<TarjetaId {cliente} {wallet} {subiendoFoto}
				onQr={cliente ? () => (verQr = true) : null}
				onAvatar={() => inputFoto.click()}
				onHistorial={() => (verHistorial = true)} />

			{#if proximo}
				<ProximoPremioCard {proximo} onTap={() => goto(`/comercio/${proximo?.tenant_id}`)} />
			{/if}
		</div>

		<div class="mt-4 space-y-4 lg:mt-0">
			<section>
				<h2 class="mb-2 text-base font-semibold">Ofertas</h2>
				{#if cargando}
					<div class="grid grid-cols-[repeat(auto-fill,minmax(100px,1fr))] gap-2 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7" aria-busy="true">
						{#each { length: 6 } as _}
							<Skeleton clase="aspect-square w-full !rounded-xl" />
						{/each}
					</div>
				{:else if comunicados.length === 0}
					<div class="flex flex-col items-center rounded-xl bg-white p-6 shadow-sm ring-1 ring-black/5">
						<Icon name="tag" clase="h-10 w-10 text-gray-300" />
						<p class="mt-2 text-sm text-gray-500">Aún no hay ofertas publicadas</p>
					</div>
				{:else}
					<div class="grid grid-cols-[repeat(auto-fill,minmax(100px,1fr))] gap-2 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7">
						{#each comunicados as c (c.id)}
							<OfertaTile comunicado={c} onTap={() => (ofertaSel = c)} />
						{/each}
					</div>
				{/if}
			</section>

			{#if error}
				<div class="flex flex-col items-center gap-2 rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5">
					<p class="text-sm text-red-600">{error}</p>
					<button onclick={cargar} class="text-sm font-medium text-indigo-600 hover:underline">Reintentar</button>
				</div>
			{/if}
		</div>
	</div>
</PullRefresh>

<!-- Sheet: historial de movimientos -->
<BottomSheet bind:abierto={verHistorial} altura="max-h-[92dvh]">
	<h3 class="text-xl font-semibold">Historial de movimientos</h3>
	<div class="mt-3">
		{#if movimientos.length === 0}
			<p class="py-8 text-center text-sm text-gray-500">Sin movimientos todavía</p>
		{:else}
			{#each movimientos as m (m.id)}
				<MovimientoTile movimiento={m} fechaTxt={fecha(m.created_at)} />
			{/each}
		{/if}
	</div>
</BottomSheet>

<!-- Sheet: mi código QR de referido -->
<BottomSheet bind:abierto={verQr}>
	<div class="flex flex-col items-center text-center">
		<h3 class="text-xl font-semibold">Mi código YAPAI</h3>
		<p class="mt-1 text-[13px] text-gray-500">Compártelo y gana puntos por cada amigo que se registre</p>
		<div class="mt-4 rounded-2xl border border-gray-300 bg-white p-4">
			<QrImg data="yapai:ref:{codigoRef}" size={200} color="#14213d" />
		</div>
		<p class="mt-3 text-xl font-bold tracking-[2px]">{codigoRef}</p>
		<button onclick={compartirCodigo}
			class="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 font-semibold text-white hover:bg-indigo-700">
			<Icon name="share-2" clase="h-4 w-4" /> Compartir mi código
		</button>
	</div>
</BottomSheet>

<!-- Sheet: detalle de oferta -->
<BottomSheet abierto={ofertaSel !== null} altura="max-h-[92dvh]" oncerrar={() => (ofertaSel = null)}>
	{#if ofertaSel}
		<div class="overflow-hidden rounded-2xl bg-gray-200">
			<img src={cloudinaryThumb(ofertaSel.imagen_url, 800)} alt="" class="max-h-72 w-full object-cover"
				onerror={(e) => { const t = e.target as HTMLImageElement; t.style.display = 'none'; t.parentElement?.classList.add('flex','items-center','justify-center','h-40'); }} />
		</div>
		<div class="mt-4 flex items-center gap-2">
			<div class="h-8 w-8 shrink-0 overflow-hidden rounded-full bg-gray-100">
				{#if ofertaSel.logo_url}
					<img src={cloudinaryThumb(ofertaSel.logo_url, 64)} alt="" class="h-full w-full object-cover" />
				{:else}
					<div class="flex h-full w-full items-center justify-center text-gray-500">
						<Icon name="store" clase="h-4 w-4" />
					</div>
				{/if}
			</div>
			<p class="flex-1 text-[13px] text-gray-600">{ofertaSel.comercio}</p>
			{#if ofertaSel.vigencia_hasta}
				<span class="rounded-full bg-gray-100 px-2.5 py-1 text-[11px] text-gray-600">
					Vence {vence(ofertaSel.vigencia_hasta)}
				</span>
			{/if}
		</div>
		<h3 class="mt-3 text-2xl font-semibold">{ofertaSel.titulo}</h3>
		{#if ofertaSel.descripcion}
			<p class="mt-2 text-sm leading-relaxed text-gray-700">{ofertaSel.descripcion}</p>
		{/if}
		<button
			onclick={() => { const t = ofertaSel?.tenant_id; ofertaSel = null; if (t) goto(`/comercio/${t}`); }}
			class="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 font-semibold text-white hover:bg-indigo-700">
			<Icon name="gift" clase="h-4 w-4" />
			{ofertaSel.premio_id ? `Ver premio en ${ofertaSel.comercio}` : `Ver ${ofertaSel.comercio}`}
		</button>
	{/if}
</BottomSheet>
