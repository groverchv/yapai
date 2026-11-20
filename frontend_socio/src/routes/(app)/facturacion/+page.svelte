<script lang="ts">
	import { onMount } from 'svelte';
	import { api, ApiError } from '#lib/api/client';
	import Badge from '#lib/components/ui/Badge.svelte';
	import DataTable from '#lib/components/ui/DataTable.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import { toast } from '#lib/stores/toast.svelte';
	import type { EstadoCuenta, FacturaSocio } from '#lib/types';
	import { formatDinero, formatFecha } from '#lib/utils/format';

	let cuenta = $state<EstadoCuenta | null>(null);
	let cargando = $state(true);
	let pagando = $state(false);

	async function pagarEnLinea() {
		pagando = true;
		try {
			const { url } = await api.post<{ url: string }>('/socio/facturacion/checkout', {});
			window.location.href = url;
		} catch (e) {
			toast.error(e instanceof ApiError ? e.detail : 'No se pudo iniciar el pago en línea');
			pagando = false;
		}
	}

	let subiendoComprobante = $state<number | null>(null);
	let inputComprobante: HTMLInputElement;
	let facturaComprobante = $state<number | null>(null);

	function pedirComprobante(facturaId: number) {
		facturaComprobante = facturaId;
		inputComprobante?.click();
	}

	async function subirComprobante(e: Event) {
		const file = (e.target as HTMLInputElement).files?.[0];
		if (!file || !facturaComprobante) return;
		subiendoComprobante = facturaComprobante;
		try {
			const form = new FormData();
			form.append('file', file);
			form.append('tipo', 'general');
			const { url } = await api.upload<{ url: string }>('/socio/media/upload', form);
			await api.post(`/socio/facturacion/${facturaComprobante}/comprobante`, { url });
			toast.exito('Comprobante registrado — lo confirmaremos en 24 h hábiles');
			cuenta = await api.get('/socio/facturacion');
		} catch (err) {
			toast.error(err instanceof ApiError ? err.detail : 'No se pudo subir el comprobante');
		} finally {
			subiendoComprobante = null;
			facturaComprobante = null;
			(e.target as HTMLInputElement).value = '';
		}
	}

	const columnas = [
		{ key: 'periodo', label: 'Periodo' },
		{ key: 'plan_nombre', label: 'Plan' },
		{ key: 'monto', label: 'Monto' },
		{ key: 'emitida_en', label: 'Emitida' },
		{ key: 'vence_en', label: 'Vence' },
		{ key: 'estado', label: 'Estado' },
		{ key: 'pago', label: 'Pago' },
		{ key: 'comprobante', label: 'Comprobante' }
	];

	const ESTADOS = {
		al_dia: { titulo: 'Estás al día', texto: 'No tienes facturas pendientes de pago.', cls: 'border-emerald-200 bg-emerald-50 text-emerald-800', icono: 'check' },
		pendiente: { titulo: 'Factura pendiente', texto: 'Tienes una factura dentro del plazo de pago.', cls: 'border-amber-200 bg-amber-50 text-amber-800', icono: 'alert-triangle' },
		vencida: { titulo: 'Pago vencido', texto: 'Tienes una factura vencida. Regulariza tu pago para evitar la suspensión del servicio.', cls: 'border-red-200 bg-red-50 text-red-800', icono: 'alert-triangle' }
	} as const;

	function variante(e: string): 'ok' | 'warn' | 'bad' {
		return e === 'pagada' ? 'ok' : e === 'pendiente' ? 'warn' : 'bad';
	}

	onMount(async () => {
		try {
			cuenta = await api.get('/socio/facturacion');
		} catch (e) {
			toast.error(e instanceof ApiError ? e.detail : 'Error al cargar tu facturación');
		} finally {
			cargando = false;
		}
	});
</script>

<input bind:this={inputComprobante} type="file" accept="image/*" class="hidden"
	onchange={subirComprobante} aria-label="Subir comprobante de pago" />

{#if cargando}
	<div class="space-y-4">
		<div class="h-24 animate-pulse rounded-xl bg-slate-100"></div>
		<div class="h-64 animate-pulse rounded-xl bg-slate-100"></div>
	</div>
{:else if cuenta}
	{@const est = ESTADOS[cuenta.estado]}
	<div class="mb-6 flex items-start gap-3 rounded-xl border {est.cls} p-4">
		<Icon name={est.icono} clase="mt-0.5 h-5 w-5 shrink-0" />
		<div>
			<p class="font-semibold">{est.titulo}</p>
			<p class="text-sm opacity-90">{est.texto}</p>
		</div>
	</div>

	{#if cuenta.estado !== 'al_dia'}
		{#if cuenta.pago_online}
			<button onclick={pagarEnLinea} disabled={pagando}
				class="mb-6 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 py-3 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
				<Icon name="credit-card" clase="h-5 w-5" />
				{pagando ? 'Conectando con la pasarela…' : 'Pagar en línea ahora'}
			</button>
		{/if}
		<div class="mb-6 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600 shadow-sm">
			<p class="mb-1 font-semibold text-slate-800">¿Cómo pagar?</p>
			<p>Realiza una transferencia o pago QR por el monto de tu factura y envía el comprobante a
				<strong>soporte@yapai.com</strong> indicando tu negocio y el periodo. Tu pago se registra
				en un máximo de 24 h hábiles.</p>
		</div>
	{/if}

	<div class="rounded-xl border border-slate-200 bg-white shadow-sm">
		<DataTable {columnas} filas={(cuenta.facturas ?? []) as unknown as Record<string, unknown>[]} cargando={false}>
			{#snippet celda({ key, fila })}
				{@const f = fila as unknown as FacturaSocio}
				{#if key === 'monto'}
					<strong>{formatDinero(f.monto, f.moneda)}</strong>
				{:else if key === 'emitida_en' || key === 'vence_en'}
					{formatFecha(f[key])}
				{:else if key === 'estado'}
					<Badge texto={f.estado} variante={variante(f.estado)} />
				{:else if key === 'pago'}
					{#if f.pagada_en}
						{f.metodo ?? '—'} <span class="block text-xs text-slate-500">{formatFecha(f.pagada_en)}</span>
					{:else}—{/if}
				{:else if key === 'comprobante'}
					{#if f.comprobante_url}
						<a href={f.comprobante_url} target="_blank" rel="noopener noreferrer"
							class="text-xs font-medium text-indigo-600 hover:underline">Ver comprobante</a>
					{:else if f.estado === 'pendiente' || f.estado === 'vencida'}
						<button onclick={() => pedirComprobante(f.id)} disabled={subiendoComprobante === f.id}
							class="text-xs font-medium text-emerald-700 hover:underline disabled:opacity-50">
							{subiendoComprobante === f.id ? 'Subiendo…' : 'Subir comprobante'}
						</button>
					{:else}—{/if}
				{:else}{f[key as keyof FacturaSocio]}{/if}
			{/snippet}
		</DataTable>
	</div>
{/if}
