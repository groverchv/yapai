<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { goto } from '$app/navigation';
	import { onMount, tick } from 'svelte';
	import { api, API_BASE, ApiError, fetchRed } from '#lib/api/client';
	import { auth } from '#lib/stores/auth.svelte';
	import { toast } from '#lib/stores/toast.svelte';
	import type { UsuarioMe } from '#lib/types';

	interface Contexto {
		cajero_id: number; cajero_nombre: string; rol: string;
		sucursales: { id: number; nombre: string }[];
		modo_pin: string; max_puntos_tx: number; max_puntos_dia_cajero: number;
		bonus_hoy: number;
	}
	interface Preview {
		pase_id: number; estado: string; cliente_nombre: string; cliente_ci: string;
		premio_nombre: string; puntos: number; comercio: string; expira_en: string | null;
	}
	interface ClienteBusq {
		id: number; nombre: string; ci: string; telefono: string; saldo_puntos: number;
	}

	let verificado = $state(false);
	let contexto = $state<Contexto | null>(null);
	let sucursalId = $state(0);
	let tab = $state<'canje' | 'bonus' | 'pantalla'>('canje');

	// --- Canje ---
	let codigo = $state('');
	let preview = $state<Preview | null>(null);
	let buscando = $state(false);
	let canjeando = $state(false);
	let errorCanje = $state('');
	let inputCodigo = $state<HTMLInputElement | null>(null);

	// --- Escáner QR por cámara (BarcodeDetector nativo, sin dependencias) ---
	let escaneando = $state(false);
	let videoEl = $state<HTMLVideoElement | null>(null);
	let mediaStream: MediaStream | null = null;
	let scanTimer: ReturnType<typeof setInterval> | null = null;
	let errorScan = $state('');

	type BarcodeDetectorCtor = new (opts?: { formats?: string[] }) => {
		detect(src: CanvasImageSource): Promise<{ rawValue: string }[]>;
	};

	async function iniciarEscaner() {
		errorScan = '';
		const Detector = (window as unknown as { BarcodeDetector?: BarcodeDetectorCtor })
			.BarcodeDetector;
		if (!Detector) {
			errorScan = 'Este navegador no soporta lectura de QR. Usa Chrome/Edge o escribe el PIN.';
			return;
		}
		try {
			mediaStream = await navigator.mediaDevices.getUserMedia({
				video: { facingMode: 'environment' },
			});
		} catch {
			errorScan = 'No se pudo acceder a la cámara. Revisa los permisos del navegador.';
			return;
		}
		escaneando = true;
		await tick();
		if (videoEl) {
			videoEl.srcObject = mediaStream;
			await videoEl.play();
		}
		const detector = new Detector({ formats: ['qr_code'] });
		scanTimer = setInterval(async () => {
			if (!videoEl || videoEl.readyState < 2) return;
			try {
				const codes = await detector.detect(videoEl);
				const valor = codes[0]?.rawValue?.trim();
				if (valor) {
					detenerEscaner();
					codigo = valor;
					await buscarPase();
				}
			} catch {
				/* frame ilegible, reintentar en el siguiente tick */
			}
		}, 350);
	}

	function detenerEscaner() {
		if (scanTimer) {
			clearInterval(scanTimer);
			scanTimer = null;
		}
		mediaStream?.getTracks().forEach((t) => t.stop());
		mediaStream = null;
		escaneando = false;
	}

	// Feed de actividad del turno (canjes + bonuses de esta sesión)
	let actividad = $state<{ hora: string; texto: string }[]>([]);
	function registrarActividad(texto: string) {
		const hora = new Date().toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' });
		actividad = [{ hora, texto }, ...actividad].slice(0, 10);
	}

	async function enfocarCodigo() {
		await tick();
		inputCodigo?.focus();
	}

	// --- Bonus ---
	let busqueda = $state('');
	let clientes = $state<ClienteBusq[]>([]);
	let clienteSel = $state<ClienteBusq | null>(null);
	let puntosBonus = $state(0);
	let motivo = $state('');
	let errorBonus = $state('');

	// --- Pantalla ---
	let deviceToken = $state('');
	let pinPantalla = $state('');
	let cajeroIdPin = $state(0);
	let cajerosPin = $state<{ id: number; nombre: string }[]>([]);
	let errorPin = $state('');

	onMount(() => {
		(async () => {
			if (!auth.autenticado) { goto('/login'); return; }
			try {
				const me = await api.get<{ tipo: string; usuario: UsuarioMe }>('/auth/me');
				if (me.tipo !== 'usuario' || (me.usuario.rol !== 'cajero' && me.usuario.rol !== 'owner')) {
					throw new Error('sin permisos');
				}
				contexto = await api.get<Contexto>('/caja/contexto');
				sucursalId = contexto.sucursales[0]?.id ?? 0;
				verificado = true;
				enfocarCodigo();
			} catch {
				auth.limpiar();
				goto('/login');
			}
		})();
		return detenerEscaner;
	});

	async function buscarPase() {
		if (!codigo.trim() || buscando) return;
		buscando = true;
		preview = null;
		errorCanje = '';
		try {
			preview = await api.get<Preview>(`/caja/pases/${encodeURIComponent(codigo.trim())}`);
			if (preview.estado !== 'activo') {
				errorCanje = `Este pase está ${preview.estado}`;
			}
		} catch (e) {
			errorCanje = e instanceof ApiError ? e.detail : 'Pase no encontrado';
		} finally {
			buscando = false;
		}
	}

	function limpiarCanje() {
		codigo = '';
		preview = null;
		errorCanje = '';
		enfocarCodigo();
	}

	function cambiarTab(t: typeof tab) {
		detenerEscaner();
		tab = t;
	}

	function teclaCodigo(e: KeyboardEvent) {
		if (e.key === 'Escape') return limpiarCanje();
		if (e.key !== 'Enter') return;
		if (preview?.estado === 'activo') confirmarCanje(); else buscarPase();
	}

	async function confirmarCanje() {
		if (!preview || preview.estado !== 'activo' || canjeando) return;
		canjeando = true;
		errorCanje = '';
		try {
			const res = await api.post<{ detail: string; saldo_cliente: number; stock_restante: number | null }>(
				`/caja/pases/${codigo.trim()}/canjear`, { sucursal_id: sucursalId });
			toast.exito(`${res.detail}: ${preview.premio_nombre} → ${preview.cliente_nombre}`);
			registrarActividad(`Canje: ${preview.premio_nombre} → ${preview.cliente_nombre} (−${preview.puntos} pts)`);
			limpiarCanje();
		} catch (e) {
			errorCanje = e instanceof ApiError ? e.detail : 'Error al canjear';
		} finally {
			canjeando = false;
		}
	}

	async function buscarCliente() {
		if (busqueda.trim().length < 3) return;
		errorBonus = '';
		try {
			clientes = await api.get<ClienteBusq[]>(`/caja/clientes/buscar?q=${encodeURIComponent(busqueda.trim())}`);
		} catch (e) {
			errorBonus = e instanceof ApiError ? e.detail : 'Error';
		}
	}

	async function darBonus() {
		if (!clienteSel || puntosBonus <= 0) return;
		errorBonus = '';
		try {
			const res = await api.post<{ detail: string; bonus_hoy: number; limite_dia: number }>(
				'/caja/bonus', {
					cliente_id: clienteSel.id, sucursal_id: sucursalId,
					puntos: puntosBonus, motivo,
				});
			toast.exito(`+${puntosBonus} pts para ${clienteSel.nombre} (${res.bonus_hoy}/${res.limite_dia} hoy)`);
			registrarActividad(`Bonus: +${puntosBonus} pts → ${clienteSel.nombre}`);
			if (contexto) contexto.bonus_hoy = res.bonus_hoy;
			clienteSel = null;
			puntosBonus = 0;
			motivo = '';
			busqueda = '';
			clientes = [];
		} catch (e) {
			errorBonus = e instanceof ApiError ? e.detail : 'Error al otorgar';
		}
	}

	async function cargarCajerosPin() {
		// Lista pública de cajeros para el modo por_cajero
		try {
			const info = await fetchRed(`${API_BASE}/kiosco/${deviceToken.trim()}/pin-info`)
				.then((r) => r.json());
			cajerosPin = info.cajeros ?? [];
			if (info.modo_pin === 'por_cajero' && cajerosPin.length > 0 && !cajeroIdPin) {
				cajeroIdPin = cajerosPin[0].id;
			}
		} catch { /* opcional */ }
	}

	async function habilitarPantalla() {
		errorPin = '';
		try {
			const res = await fetchRed(`${API_BASE}/caja/pantalla/habilitar`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					device_token: deviceToken.trim(), pin: pinPantalla,
					cajero_id: cajeroIdPin || null,
				}),
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? 'Error');
			toast.exito(`Pantalla "${data.pantalla}" habilitada hasta ${new Date(data.habilitada_hasta).toLocaleTimeString('es-BO')} por ${data.habilitada_por}`);
			registrarActividad(`Pantalla habilitada: ${data.pantalla}`);
			deviceToken = '';
			pinPantalla = '';
		} catch (e) {
			errorPin = e instanceof Error ? e.message : 'Error';
		}
	}

	async function logout() {
		if (auth.refreshToken) {
			await api.post('/auth/logout', { refresh_token: auth.refreshToken }).catch(() => {});
		}
		auth.limpiar();
		goto('/login');
	}
</script>

{#if verificado && contexto}
	<div class="min-h-screen bg-slate-900 text-white">
		<header class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-700 px-6 py-4">
			<div class="flex items-center gap-3">
				{#if auth.usuario?.tenant_logo}
					<div class="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-white p-1 shadow-sm">
						<img src={auth.usuario.tenant_logo} alt={auth.usuario?.tenant_nombre ?? 'Logo'}
							class="h-full w-full object-cover rounded" />
					</div>
				{:else}
					<div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-600 text-white font-bold text-sm shadow-sm">
						{(auth.usuario?.tenant_nombre || 'S')[0].toUpperCase()}
					</div>
				{/if}
				<div>
					<p class="text-sm font-bold text-white leading-tight">{auth.usuario?.tenant_nombre || 'Comercio'}</p>
					<span class="rounded bg-emerald-600/30 text-emerald-400 px-1.5 py-0.5 text-[10px] font-bold tracking-wider uppercase">TERMINAL DE CAJA</span>
				</div>
			</div>
			<div class="flex items-center gap-4">
				<div>
					<label for="suc" class="mr-2 text-xs text-slate-400">Sucursal</label>
					<select id="suc" bind:value={sucursalId}
						class="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm">
						{#each contexto.sucursales as s}
							<option value={s.id}>{s.nombre}</option>
						{/each}
					</select>
				</div>
				<span class="text-sm text-slate-400">{contexto.cajero_nombre}</span>
				<button onclick={logout} class="flex items-center gap-1.5 rounded-lg border border-slate-600 px-3 py-1.5 text-sm hover:bg-slate-800">
					<Icon name="log-out" clase="h-4 w-4" />Salir
				</button>
			</div>
		</header>

		<nav class="flex gap-1 border-b border-slate-700 px-6">
			{#each [
				['canje', 'Canjear pase', 'scan-line'],
				['bonus', 'Bonus por compra', 'gift'],
				['pantalla', 'Habilitar pantalla', 'lock-open']
			] as [t, label, ico]}
				<button onclick={() => cambiarTab(t as typeof tab)}
					class="flex items-center gap-2 px-4 py-3 text-sm font-medium transition
						{tab === t ? 'border-b-2 border-emerald-500 text-emerald-400' : 'text-slate-400 hover:text-white'}">
					<Icon name={ico} clase="h-4 w-4" /> {label}
				</button>
			{/each}
		</nav>

		<main class="mx-auto max-w-2xl p-4 sm:p-6">
			{#if tab === 'canje'}
				<div class="space-y-4">
					<div class="rounded-xl bg-slate-800 p-5">
						<label for="cod" class="mb-2 block text-sm text-slate-400">
							Escanea el QR o escribe el PIN del pase
							<span class="float-right text-xs">⏎ buscar/entregar · Esc cancelar</span>
						</label>
						<div class="flex gap-2">
							<input id="cod" type="text" bind:value={codigo} bind:this={inputCodigo} placeholder="QR o PIN (ej. JK6G5Q)"
								onkeydown={teclaCodigo} autocomplete="off"
								class="flex-1 rounded-xl border border-slate-600 bg-slate-900 px-4 py-3 font-mono text-lg uppercase tracking-widest focus:border-emerald-500 focus:outline-none" />
							<button onclick={buscarPase} disabled={buscando}
								class="rounded-xl bg-emerald-600 px-6 py-3 font-bold hover:bg-emerald-500 disabled:opacity-50">
								{buscando ? '…' : 'Buscar'}
							</button>
							<button onclick={escaneando ? detenerEscaner : iniciarEscaner}
								class="flex items-center gap-2 rounded-xl border border-slate-600 px-4 py-3 font-bold text-slate-300 hover:bg-slate-700"
								title="Leer el QR del pase con la cámara">
								<Icon name="scan-line" clase="h-5 w-5" />
								{escaneando ? 'Detener' : 'Escanear'}
							</button>
						</div>
					</div>

					{#if escaneando}
						<div class="overflow-hidden rounded-xl border border-slate-600 bg-black">
							<!-- svelte-ignore a11y_media_has_caption -->
							<video bind:this={videoEl} class="h-64 w-full object-cover" muted playsinline></video>
							<p class="px-4 py-2 text-center text-xs text-slate-400">
								Apunta la cámara al QR del pase del cliente
							</p>
						</div>
					{/if}

					{#if errorScan}
						<p class="rounded-xl bg-amber-900/40 px-4 py-3 text-sm text-amber-300">{errorScan}</p>
					{/if}

					{#if errorCanje}
						<p class="rounded-xl bg-red-900/50 px-4 py-3 text-sm text-red-300">{errorCanje}</p>
					{/if}

					{#if preview}
						<div class="rounded-xl border-2 {preview.estado === 'activo' ? 'border-emerald-500' : 'border-slate-600'} bg-slate-800 p-6">
							<div class="flex items-start justify-between gap-4">
								<div>
									<p class="text-xs uppercase tracking-wide text-slate-400">Cliente</p>
									<p class="text-2xl font-bold">{preview.cliente_nombre}</p>
									<p class="text-sm text-slate-400">CI {preview.cliente_ci}</p>
								</div>
								<div class="text-right">
									<p class="text-xs uppercase tracking-wide text-slate-400">Premio</p>
									<p class="text-2xl font-bold text-emerald-400">{preview.premio_nombre}</p>
									<p class="mt-1 text-3xl font-bold">{preview.puntos} pts</p>
								</div>
							</div>
							{#if preview.estado === 'activo'}
								<button onclick={confirmarCanje} disabled={canjeando}
									class="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 py-5 text-xl font-bold hover:bg-emerald-500 disabled:opacity-50">
									<Icon name="check" clase="h-6 w-6" />
									{canjeando ? 'Procesando…' : 'ENTREGAR PREMIO'}
								</button>
								<button onclick={limpiarCanje}
									class="mt-2 w-full rounded-xl border border-slate-600 py-2 text-sm text-slate-400 hover:text-white">
									Cancelar [Esc]
								</button>
							{:else}
								<p class="mt-4 rounded-lg bg-slate-700 px-4 py-3 text-center text-slate-300">
									Pase {preview.estado} — no se puede canjear
								</p>
							{/if}
						</div>
					{/if}
				</div>

			{:else if tab === 'bonus'}
				<div class="space-y-4">
					<div class="flex items-center justify-between rounded-xl bg-slate-800 px-5 py-3 text-sm">
						<span class="text-slate-400">Bonus usado hoy:</span>
						<span class="font-bold">{contexto.bonus_hoy} / {contexto.max_puntos_dia_cajero} pts</span>
					</div>

					{#if !clienteSel}
						<div class="rounded-xl bg-slate-800 p-5">
							<label for="bq" class="mb-2 block text-sm text-slate-400">
								Buscar cliente por CI o teléfono
							</label>
							<div class="flex gap-2">
								<input id="bq" type="text" bind:value={busqueda} placeholder="CI o teléfono…"
									onkeydown={(e) => e.key === 'Enter' && buscarCliente()}
									class="flex-1 rounded-xl border border-slate-600 bg-slate-900 px-4 py-3 focus:border-emerald-500 focus:outline-none" />
								<button onclick={buscarCliente}
									class="rounded-xl bg-emerald-600 px-6 py-3 font-bold hover:bg-emerald-500">
									Buscar
								</button>
							</div>
							{#each clientes as c}
								<button onclick={() => (clienteSel = c)}
									class="mt-2 flex w-full items-center justify-between rounded-lg bg-slate-700 px-4 py-3 text-left hover:bg-slate-600">
									<span><strong>{c.nombre}</strong> · CI {c.ci}</span>
									<span class="text-emerald-400">{c.saldo_puntos} pts</span>
								</button>
							{/each}
						</div>
					{:else}
						<div class="rounded-xl bg-slate-800 p-5">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-xl font-bold">{clienteSel.nombre}</p>
									<p class="text-sm text-slate-400">CI {clienteSel.ci} · saldo {clienteSel.saldo_puntos} pts</p>
								</div>
								<button onclick={() => (clienteSel = null)} class="text-sm text-slate-400 hover:text-white">Cambiar</button>
							</div>
							<div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
								<div>
									<label for="pb" class="mb-1 block text-sm text-slate-400">Puntos (máx {contexto.max_puntos_tx})</label>
									<input id="pb" type="number" bind:value={puntosBonus} min="1" max={contexto.max_puntos_tx}
										class="w-full rounded-xl border border-slate-600 bg-slate-900 px-4 py-3 focus:border-emerald-500 focus:outline-none" />
								</div>
								<div>
									<label for="mb" class="mb-1 block text-sm text-slate-400">Motivo (ticket/compra)</label>
									<input id="mb" type="text" bind:value={motivo} placeholder="Ticket #123"
										class="w-full rounded-xl border border-slate-600 bg-slate-900 px-4 py-3 focus:border-emerald-500 focus:outline-none" />
								</div>
							</div>
							<button onclick={darBonus} disabled={puntosBonus <= 0 || motivo.trim().length < 3}
								class="mt-4 w-full rounded-xl bg-emerald-600 py-4 text-lg font-bold hover:bg-emerald-500 disabled:opacity-50">
								Otorgar puntos
							</button>
						</div>
					{/if}

					{#if errorBonus}
						<p class="rounded-xl bg-red-900/50 px-4 py-3 text-sm text-red-300">{errorBonus}</p>
					{/if}
				</div>

			{:else}
				<div class="space-y-4 rounded-xl bg-slate-800 p-5">
					<p class="text-sm text-slate-400">
						Habilita una pantalla física del local con el PIN de caja para que muestre la ruleta.
					</p>
					<div>
						<label for="dt" class="mb-1 block text-sm text-slate-400">Token del dispositivo</label>
						<input id="dt" type="text" bind:value={deviceToken} placeholder="kiosco-…"
							onblur={cargarCajerosPin}
							class="w-full rounded-xl border border-slate-600 bg-slate-900 px-4 py-3 font-mono focus:border-emerald-500 focus:outline-none" />
					</div>
					{#if cajerosPin.length > 0}
						<div>
							<label for="cj" class="mb-1 block text-sm text-slate-400">¿Quién habilita?</label>
							<select id="cj" bind:value={cajeroIdPin}
								class="w-full rounded-xl border border-slate-600 bg-slate-900 px-4 py-3">
								{#each cajerosPin as c}
									<option value={c.id}>{c.nombre}</option>
								{/each}
							</select>
						</div>
					{/if}
					<div>
						<label for="pp" class="mb-1 block text-sm text-slate-400">PIN de caja (4 dígitos)</label>
						<input id="pp" type="password" bind:value={pinPantalla} maxlength="4" inputmode="numeric"
							class="w-full rounded-xl border border-slate-600 bg-slate-900 px-4 py-3 text-center text-2xl tracking-[0.5em] focus:border-emerald-500 focus:outline-none" />
					</div>
					<button onclick={habilitarPantalla} disabled={!deviceToken || pinPantalla.length !== 4}
						class="w-full rounded-xl bg-emerald-600 py-4 text-lg font-bold hover:bg-emerald-500 disabled:opacity-50">
						Habilitar pantalla
					</button>
					{#if errorPin}
						<p class="rounded-xl bg-red-900/50 px-4 py-3 text-sm text-red-300">{errorPin}</p>
					{/if}
				</div>
			{/if}

			{#if actividad.length > 0}
				<section class="mt-8 rounded-xl bg-slate-800/60 p-4">
					<h2 class="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">
						Actividad de tu turno
					</h2>
					<ul class="space-y-1.5 text-sm">
						{#each actividad as a}
							<li class="flex items-center gap-3 text-slate-300">
								<span class="font-mono text-xs text-slate-500">{a.hora}</span>
								<span>{a.texto}</span>
							</li>
						{/each}
					</ul>
				</section>
			{/if}
		</main>
	</div>
{:else}
	<div class="flex h-screen items-center justify-center bg-slate-900 text-slate-400">
		Verificando sesión…
	</div>
{/if}
