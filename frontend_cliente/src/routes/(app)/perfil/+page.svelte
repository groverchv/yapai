<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '#lib/stores/auth.svelte';
	import { pwa } from '#lib/stores/pwa.svelte';
	import { toast } from '#lib/stores/toast.svelte';
	import { mensajeError } from '#lib/api/client';
	import { cloudinaryThumb, compartir, iniciales } from '#lib/utils/format';
	import Dialog from '#lib/components/ui/Dialog.svelte';
	import Icon from '#lib/components/ui/Icon.svelte';
	import Spinner from '#lib/components/ui/Spinner.svelte';

	const cliente = $derived(auth.cliente);

	let subiendo = $state(false);
	let confirmarEliminar = $state(false);
	let inputFoto: HTMLInputElement;

	async function subir(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		input.value = '';
		if (!file) return;
		subiendo = true;
		try {
			await auth.subirFoto(file);
		} catch (err) {
			toast.error(mensajeError(err) === 'Sin conexión' ? 'Error al subir la foto' : mensajeError(err));
		} finally {
			subiendo = false;
		}
	}

	async function copiarCodigo() {
		if (!cliente?.codigo_referido) return;
		await navigator.clipboard.writeText(cliente.codigo_referido);
		toast.exito('Código copiado');
	}

	async function compartirCodigo() {
		if (!cliente?.codigo_referido) return;
		const res = await compartir(`¡Únete a YAPAI con mi código ${cliente.codigo_referido} y gana puntos!`);
		if (res === 'copied') toast.exito('Código copiado');
	}

	async function instalar() {
		const acepto = await pwa.instalar();
		if (!acepto && !pwa.instalada) {
			toast.info('Abre el menú del navegador y elige "Instalar app" o "Añadir a pantalla de inicio"');
		}
	}

	async function salir() {
		await auth.cerrarSesion();
		goto('/login');
	}

	async function eliminar() {
		try {
			await auth.eliminarCuenta();
			goto('/login');
		} catch (e) {
			toast.error(mensajeError(e));
		}
	}
</script>

<input bind:this={inputFoto} type="file" accept="image/*" class="hidden" onchange={subir} />


<div class="space-y-4 p-4 lg:w-full lg:grid lg:grid-cols-3 lg:items-start lg:gap-5 lg:space-y-0 lg:p-8">
	<div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5">
		<div class="flex flex-col items-center">
			<button onclick={() => inputFoto.click()} class="relative" aria-label="Cambiar foto">
				<div class="flex h-[72px] w-[72px] items-center justify-center overflow-hidden rounded-full bg-green-50">
					{#if subiendo}
						<Spinner clase="h-6 w-6 text-green-700" />
					{:else if cliente?.foto_url}
						<img src={cloudinaryThumb(cliente.foto_url, 160)} alt="" class="h-full w-full object-cover" />
					{:else}
						<span class="text-3xl font-semibold text-green-700">{iniciales(cliente?.nombre).slice(0, 1)}</span>
					{/if}
				</div>
				<span class="absolute -bottom-0.5 -right-0.5 rounded-full border-2 border-white bg-green-700 p-1.5 text-white">
					<Icon name="camera" clase="h-3.5 w-3.5" />
				</span>
			</button>
			<p class="mt-3 text-xl font-bold">{cliente?.nombre ?? '—'}</p>
		</div>

		<div class="mt-4 space-y-1.5">
			{#each [
				{ icono: 'id-card', label: 'Cédula', valor: cliente?.ci ?? '—' },
				{ icono: 'phone', label: 'Teléfono', valor: cliente?.telefono ?? '—' },
				{ icono: 'star', label: 'Puntos acumulados', valor: `${cliente?.saldo_puntos ?? 0} pts` },
			] as f}
				<div class="flex items-center py-1.5">
					<Icon name={f.icono} clase="h-5 w-5 text-gray-400" />
					<span class="ml-3 text-sm text-gray-500">{f.label}:</span>
					<span class="ml-auto text-sm font-semibold">{f.valor}</span>
				</div>
			{/each}
		</div>
	</div>

	{#if cliente?.codigo_referido}
		<div class="rounded-xl bg-navy p-5 text-center">
			<p class="text-[13px] text-white/70">Tu código de referido</p>
			<p class="mt-1.5 text-[26px] font-bold tracking-[3px] text-white">{cliente.codigo_referido}</p>
			<p class="mt-1.5 text-xs text-white/70">Gana puntos por cada amigo que se registre con tu código</p>
			<div class="mt-3.5 grid grid-cols-2 gap-2.5">
				<button onclick={copiarCodigo}
					class="flex items-center justify-center gap-2 rounded-lg border border-white/30 bg-white/10 py-2.5 text-sm font-medium text-white hover:bg-white/20">
					<Icon name="copy" clase="h-4 w-4" /> Copiar
				</button>
				<button onclick={compartirCodigo}
					class="flex items-center justify-center gap-2 rounded-lg bg-white py-2.5 text-sm font-semibold text-navy hover:bg-gray-100">
					<Icon name="share-2" clase="h-4 w-4" /> Compartir
				</button>
			</div>
		</div>
	{/if}

	<div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5">
		<p class="text-sm font-semibold text-gray-800">Cuenta</p>
		{#if !pwa.instalada}
			<button onclick={instalar}
				class="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white hover:bg-indigo-700">
				<Icon name="download" clase="h-4 w-4" /> Instalar app
			</button>
		{/if}
		<button onclick={salir}
			class="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-gray-300 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50">
			<Icon name="log-out" clase="h-4 w-4" /> Cerrar sesión
		</button>

		<div class="mt-4 border-t border-gray-100 pt-4">
			<button onclick={() => (confirmarEliminar = true)}
				class="flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-medium text-red-600 hover:bg-red-50">
				<Icon name="trash-2" clase="h-4 w-4" /> Eliminar mi cuenta
			</button>
			<p class="mt-1 text-center text-[11px] text-gray-400">Al eliminar la cuenta pierdes tus puntos acumulados.</p>
		</div>
	</div>
</div>

<Dialog abierto={confirmarEliminar} titulo="Eliminar cuenta"
	texConfirmar="Eliminar definitivamente" peligroso
	oncerrar={() => (confirmarEliminar = false)}
	onConfirmar={eliminar}>
	Se eliminará tu cuenta de forma permanente y perderás todos tus puntos acumulados y pases activos.
	Esta acción no se puede deshacer.
</Dialog>
