<script lang="ts">
	import { onMount } from 'svelte';
	import { api, ApiError } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import Pagination from '#lib/components/ui/Pagination.svelte';
	import { toast } from '#lib/stores/toast.svelte';
	import type { FacturaOut, Pagina } from '#lib/types';
	import { formatDinero, formatFecha } from '#lib/utils/format';

	let datos = $state<Pagina<FacturaOut> | null>(null);
	let cargando = $state(false);
	let estado = $state('');
	let periodo = $state('');
	let page = $state(1);
	let pagarModal = $state<FacturaOut | null>(null);
	let anularModal = $state<FacturaOut | null>(null);
	let metodo = $state('transferencia');
	let referencia = $state('');

	const columnas = [
		{ key: 'socio_nombre', label: 'Socio' },
		{ key: 'periodo', label: 'Periodo' },
		{ key: 'plan_nombre', label: 'Plan' },
		{ key: 'monto', label: 'Monto' },
		{ key: 'emitida_en', label: 'Emitida' },
		{ key: 'vence_en', label: 'Vence' },
		{ key: 'estado', label: 'Estado' },
		{ key: 'metodo', label: 'Cobro' }
	];

	async function cargar() {
		cargando = true;
		try {
			const p = new URLSearchParams({ page: String(page), size: '10' });
			if (estado) p.set('estado', estado);
			if (periodo) p.set('periodo', periodo);
			datos = await api.get<Pagina<FacturaOut>>(`/admin/facturacion?${p}`);
		} finally {
			cargando = false;
		}
	}

	async function generar() {
		try {
			const p = periodo ? `?periodo=${periodo}` : '';
			const r = await api.post<{ periodo: string; emitidas: number }>(`/admin/facturacion/generar${p}`);
			toast.exito(`${r.emitidas} factura(s) emitidas para ${r.periodo}`);
			cargar();
		} catch (e) {
			toast.error(e instanceof ApiError ? e.detail : 'Error al generar');
		}
	}

	async function pagar() {
		if (!pagarModal) return;
		try {
			await api.post(`/admin/facturacion/${pagarModal.id}/pagar`, {
				metodo, referencia: referencia || null
			});
			toast.exito(`Factura #${pagarModal.id} marcada como pagada`);
			pagarModal = null;
			referencia = '';
			cargar();
		} catch (e) {
			toast.error(e instanceof ApiError ? e.detail : 'Error');
		}
	}

	async function anular() {
		if (!anularModal) return;
		try {
			await api.post(`/admin/facturacion/${anularModal.id}/anular`);
			toast.exito(`Factura #${anularModal.id} anulada`);
			anularModal = null;
			cargar();
		} catch (e) {
			toast.error(e instanceof ApiError ? e.detail : 'Error');
		}
	}

	function variante(e: string): 'ok' | 'warn' | 'bad' | 'neutral' {
		return e === 'pagada' ? 'ok' : e === 'pendiente' ? 'warn' : e === 'vencida' ? 'bad' : 'neutral';
	}

	onMount(cargar);
	const input = 'rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none';
</script>

<div class="mb-4 flex flex-wrap items-end gap-3">
	<div><label for="p" class="mb-1 block text-xs font-medium text-slate-500">Periodo</label>
		<input id="p" type="month" bind:value={periodo} onchange={cargar} class={input} /></div>
	<div><label for="e" class="mb-1 block text-xs font-medium text-slate-500">Estado</label>
		<select id="e" bind:value={estado} onchange={cargar} class={input}>
			<option value="">Todos</option>
			<option value="pendiente">Pendiente</option>
			<option value="pagada">Pagada</option>
			<option value="vencida">Vencida</option>
			<option value="anulada">Anulada</option>
		</select></div>
	<button onclick={generar}
		class="ml-auto rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
		Generar facturas del periodo
	</button>
</div>

<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
	<DataTable {columnas} filas={(datos?.items ?? []) as unknown as Record<string, unknown>[]} {cargando}>
		{#snippet celda({ key, fila })}
			{@const f = fila as unknown as FacturaOut}
			{#if key === 'monto'}
				<strong>{formatDinero(f.monto, f.moneda)}</strong>
			{:else if key === 'emitida_en' || key === 'vence_en'}
				{formatFecha(f[key])}
			{:else if key === 'estado'}
				<Badge texto={f.estado} variante={variante(f.estado)} />
			{:else if key === 'metodo'}
				{#if f.metodo}
					{f.metodo}{#if f.referencia} <span class="block text-xs text-slate-500">{f.referencia}</span>{/if}
				{:else}—{/if}
			{:else}{f[key as keyof FacturaOut]}{/if}
		{/snippet}
		{#snippet acciones(fila)}
			{@const f = fila as unknown as FacturaOut}
			{#if f.estado === 'pendiente' || f.estado === 'vencida'}
				<button onclick={() => { metodo = 'transferencia'; referencia = ''; pagarModal = f; }}
					class="text-xs font-medium text-green-600 hover:underline">Marcar pagada</button>
				<button onclick={() => (anularModal = f)}
					class="text-xs font-medium text-red-600 hover:underline">Anular</button>
			{:else}
				<span class="text-xs text-slate-300">—</span>
			{/if}
		{/snippet}
	</DataTable>
	{#if datos}
		<Pagination
			page={datos.page}
			total={datos.total}
			size={datos.size}
			onchange={(p) => { page = p; cargar(); }}
		/>
	{/if}
</div>

<Modal abierto={pagarModal !== null} titulo="Registrar cobro de factura" onclose={() => (pagarModal = null)}>
	{#if pagarModal}
		<p class="text-sm text-slate-600">
			Cobrar <strong>{formatDinero(pagarModal.monto, pagarModal.moneda)}</strong> a
			<strong>{pagarModal.socio_nombre}</strong> — {pagarModal.plan_nombre} ({pagarModal.periodo})
		</p>
		<div class="mt-4 space-y-3">
			<div>
				<label for="met" class="mb-1 block text-xs font-medium text-slate-500">Método de cobro</label>
				<select id="met" bind:value={metodo} class="{input} w-full">
					<option value="transferencia">Transferencia</option>
					<option value="qr">QR</option>
					<option value="efectivo">Efectivo</option>
					<option value="stripe">Stripe</option>
					<option value="otro">Otro</option>
				</select>
			</div>
			<div>
				<label for="ref" class="mb-1 block text-xs font-medium text-slate-500">Referencia (opcional)</label>
				<input id="ref" bind:value={referencia} placeholder="Nº de comprobante, txn id…" class="{input} w-full" />
			</div>
		</div>
		<div class="mt-5 flex justify-end gap-2">
			<button onclick={() => (pagarModal = null)} class="rounded-lg border border-slate-300 px-4 py-2 text-sm">Cancelar</button>
			<button onclick={pagar} class="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700">
				Confirmar cobro
			</button>
		</div>
	{/if}
</Modal>

<Modal abierto={anularModal !== null} titulo="Anular factura" onclose={() => (anularModal = null)}>
	{#if anularModal}
		<p class="text-sm text-slate-600">
			¿Anular la factura <strong>#{anularModal.id}</strong> de <strong>{anularModal.socio_nombre}</strong>
			({anularModal.periodo})? El socio dejará de verla en su estado de cuenta.
		</p>
		<div class="mt-5 flex justify-end gap-2">
			<button onclick={() => (anularModal = null)} class="rounded-lg border border-slate-300 px-4 py-2 text-sm">Cancelar</button>
			<button onclick={anular} class="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700">
				Anular factura
			</button>
		</div>
	{/if}
</Modal>
