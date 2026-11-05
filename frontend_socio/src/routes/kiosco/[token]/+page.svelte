<script lang="ts">
	import Icon from '#lib/components/ui/Icon.svelte';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { API_BASE, fetchRed } from '#lib/api/client';

	interface Segmento { etiqueta: string; puntos: number; peso: number; color: string | null }
	interface Oferta { titulo: string; descripcion: string | null; imagen_url: string }
	interface Config {
		comercio: string; logo_url: string | null; sucursal: string; pantalla: string;
		habilitada_hasta: string; puntos_registro: number; segmentos: Segmento[];
		ofertas: Oferta[];
	}
	interface Resultado { etiqueta: string; puntos: number; color: string | null; saldo: number; indice: number }

	const token = $derived(page.params.token ?? '');

	type Paso = 'cargando' | 'error' | 'pin' | 'identificacion' | 'ruleta' | 'resultado';
	let paso = $state<Paso>('cargando');
	let config = $state<Config | null>(null);
	let error = $state('');

	// --- Desbloqueo por PIN de caja ---
	interface PinInfo {
		comercio: string; sucursal: string; pantalla: string;
		modo_pin: 'por_sucursal' | 'por_cajero';
		cajeros: { id: number; nombre: string }[];
	}
	let pinInfo = $state<PinInfo | null>(null);
	let pinDigitos = $state('');
	let cajeroPin = $state(0);
	let desbloqueando = $state(false);

	let nombre = $state('');
	let ci = $state('');
	let telefono = $state('');
	let acepta = $state(false);
	let cargandoForm = $state(false);

	let clienteId = $state(0);
	let clienteNombre = $state('');
	let saldo = $state(0);
	let bienvenida = $state('');

	let girando = $state(false);
	let resultado = $state<Resultado | null>(null);
	let rotacion = $state(0);

	// Paleta anclada en marca YAPAI (navy + verde) con complementarios para la rueda
	const PALETA = ['#1abc9c', '#1b2a63', '#f5a623', '#2bd3b4', '#5e6fb6', '#ef4444', '#f97316', '#8fa0d6'];

	// Ángulos acumulados por peso (la rueda parte con el segmento 0 arriba)
	let geometria = $derived.by(() => {
		if (!config) return [];
		const total = config.segmentos.reduce((a, s) => a + s.peso, 0) || 1;
		let acc = 0;
		return config.segmentos.map((s, i) => {
			const span = (s.peso / total) * 360;
			const g = { inicio: acc, medio: acc + span / 2, span, color: s.color ?? PALETA[i % PALETA.length], s };
			acc += span;
			return g;
		});
	});

	let conicGradient = $derived(
		'conic-gradient(' + geometria.map(g => `${g.color} ${g.inicio}deg ${g.inicio + g.span}deg`).join(', ') + ')'
	);

	async function cargar() {
		try {
			const res = await fetchRed(`${API_BASE}/kiosco/${token}/config`);
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? 'Pantalla no disponible');
			config = data;
			paso = 'identificacion';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error de conexión';
			if (error.includes('PIN') || error.includes('habilitada')) {
				await cargarPinInfo();
				paso = 'pin';
			} else {
				paso = 'error';
			}
		}
	}

	async function cargarPinInfo() {
		try {
			const res = await fetchRed(`${API_BASE}/kiosco/${token}/pin-info`);
			pinInfo = await res.json();
			if (pinInfo && pinInfo.cajeros.length > 0) cajeroPin = pinInfo.cajeros[0].id;
		} catch { /* se muestra el formulario genérico */ }
	}

	async function desbloquear() {
		if (pinDigitos.length !== 4 || desbloqueando) return;
		desbloqueando = true;
		error = '';
		try {
			const res = await fetchRed(`${API_BASE}/caja/pantalla/habilitar`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					device_token: token, pin: pinDigitos,
					cajero_id: cajeroPin || null,
				}),
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? 'PIN incorrecto');
			pinDigitos = '';
			await cargar();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Error';
			pinDigitos = '';
		} finally {
			desbloqueando = false;
		}
	}

	async function identificar(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		cargandoForm = true;
		try {
			const res = await fetchRed(`${API_BASE}/kiosco/${token}/registro`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ nombre, ci, telefono, acepto_terminos: acepta })
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? 'Error de registro');
			clienteId = data.cliente_id;
			clienteNombre = data.nombre;
			saldo = data.saldo;
			bienvenida = data.nuevo
				? `¡Bienvenido! Ganaste ${data.puntos_otorgados} pts por registrarte`
				: `¡Hola de nuevo, ${data.nombre.split(' ')[0]}!`;
			paso = 'ruleta';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error de conexión';
		} finally {
			cargandoForm = false;
		}
	}

	async function girar() {
		if (girando) return;
		error = '';
		girando = true;
		try {
			const res = await fetchRed(`${API_BASE}/kiosco/${token}/ruleta/girar`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ cliente_id: clienteId })
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? 'No se pudo girar');
			resultado = data;
			saldo = data.saldo;

			// Animación: 6 vueltas + posicionar el segmento ganador bajo el puntero
			const g = geometria[data.indice];
			const jitter = (Math.random() - 0.5) * g.span * 0.7;
			const destino = 360 - (g.medio + jitter);
			rotacion = Math.floor(rotacion / 360) * 360 + 360 * 6 + destino;
			setTimeout(() => { paso = 'resultado'; girando = false; }, 4600);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error de conexión';
			girando = false;
		}
	}

	function siguiente() {
		paso = 'identificacion';
		resultado = null;
		nombre = ''; ci = ''; telefono = ''; acepta = false;
		error = '';
		cargar(); // revalida que siga habilitada
	}

	// --- Modo atracción: tras 45s sin tocar, slideshow de ofertas + invitación ---
	const IDLE_SEG = 45;
	const SLIDE_SEG = 6;
	let idle = $state(false);
	let idleTimer: ReturnType<typeof setTimeout>;
	let slideIdx = $state(0);
	let slideTimer: ReturnType<typeof setInterval>;

	// Con ofertas: slideshow. Sin ofertas: mensajes genéricos rotando.
	const slide = $derived.by(() => {
		const ofs = config?.ofertas ?? [];
		if (ofs.length > 0) return { tipo: 'oferta' as const, oferta: ofs[slideIdx % ofs.length] };
		const mensajes = [
			{ titulo: '¡Toca la pantalla!', desc: 'Regístrate y gira la ruleta para ganar puntos' },
			{ titulo: `Gana ${config?.puntos_registro ?? 0} pts`, desc: 'Solo por registrarte hoy' },
		];
		return { tipo: 'mensaje' as const, msg: mensajes[slideIdx % mensajes.length] };
	});

	function reiniciarIdle() {
		idle = false;
		slideIdx = 0;
		clearTimeout(idleTimer);
		clearInterval(slideTimer);
		idleTimer = setTimeout(() => {
			if (paso === 'identificacion' || paso === 'ruleta' || paso === 'resultado') {
				idle = true;
				slideTimer = setInterval(() => { slideIdx += 1; }, SLIDE_SEG * 1000);
			}
		}, IDLE_SEG * 1000);
	}

	onMount(() => {
		reiniciarIdle();
		cargar();
		return () => { clearTimeout(idleTimer); clearInterval(slideTimer); };
	});
</script>

<svelte:window onpointerdown={reiniciarIdle} onkeydown={reiniciarIdle} />

<div class="relative flex min-h-screen flex-col items-center justify-center bg-slate-950 p-6 text-white">
	<div class="absolute left-5 top-5 flex items-center gap-2.5 rounded-xl bg-white/95 px-3 py-1.5 shadow-md backdrop-blur-sm">
		{#if config?.logo_url}
			<img src={config.logo_url} alt={config.comercio} class="h-8 max-w-[120px] object-contain rounded" />
		{:else}
			<img src="/logo.png" alt="YAPAI" class="h-7" />
		{/if}
		{#if config?.comercio}
			<span class="text-xs font-bold text-slate-800">{config.comercio}</span>
		{/if}
	</div>

	{#if idle}
		<button onclick={reiniciarIdle} aria-label="Tocar para comenzar"
			class="absolute inset-0 z-50 flex flex-col items-center justify-center overflow-hidden bg-slate-950">
			{#if slide.tipo === 'oferta' && slide.oferta}
				<!-- Slideshow: oferta a pantalla completa -->
				<img src={slide.oferta.imagen_url} alt="" class="absolute inset-0 h-full w-full object-cover opacity-60" />
				<div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent"></div>
				<div class="relative z-10 flex flex-col items-center px-8 text-center">
					<span class="rounded-full bg-emerald-500 px-4 py-1 text-sm font-bold uppercase tracking-wide text-slate-950">Oferta</span>
					<span class="mt-4 max-w-2xl text-4xl font-bold drop-shadow-lg lg:text-5xl">{slide.oferta.titulo}</span>
					{#if slide.oferta.descripcion}
						<span class="mt-3 max-w-xl text-xl text-slate-300">{slide.oferta.descripcion}</span>
					{/if}
				</div>
			{:else if slide.tipo === 'mensaje' && slide.msg}
				<span class="animate-pulse text-center text-4xl font-bold text-emerald-400 lg:text-5xl">{slide.msg.titulo}</span>
				<span class="mt-3 text-xl text-slate-300">{slide.msg.desc}</span>
			{/if}
			<!-- CTA fijo abajo: siempre visible -->
			<div class="absolute bottom-10 flex flex-col items-center">
				<Icon name="tap" clase="h-14 w-14 animate-bounce text-emerald-400" />
				<span class="mt-2 text-2xl font-bold text-emerald-400">¡Toca para participar!</span>
				<span class="mt-1 text-sm text-slate-400">Gana {config?.puntos_registro ?? 0} pts al registrarte</span>
			</div>
		</button>
	{/if}

	{#if paso === 'cargando'}
		<p class="animate-pulse text-xl text-slate-400">Cargando…</p>

	{:else if paso === 'error'}
		<div class="max-w-md text-center">
			<Icon name="lock" clase="h-16 w-16 text-slate-500" />
			<h1 class="mt-4 text-2xl font-bold">Pantalla no disponible</h1>
			<p class="mt-2 text-slate-400">{error}</p>
			<button onclick={cargar}
				class="mt-6 rounded-xl bg-emerald-600 px-8 py-3 font-semibold hover:bg-emerald-500">
				Reintentar
			</button>
		</div>

	{:else if paso === 'pin'}
		<!-- Desbloqueo de pantalla por PIN de caja -->
		<div class="w-full max-w-sm text-center">
			<Icon name="keypad" clase="h-12 w-12 text-emerald-400" />
			<h1 class="mt-4 text-2xl font-bold">{pinInfo?.comercio ?? 'YAPAI'}</h1>
			<p class="mt-1 text-slate-400">{pinInfo?.sucursal ?? ''} · {pinInfo?.pantalla ?? ''}</p>
			<p class="mt-4 text-slate-300">Cajero: ingresa el PIN de caja para habilitar la ruleta</p>

			{#if pinInfo?.modo_pin === 'por_cajero' && pinInfo.cajeros.length > 0}
				<select bind:value={cajeroPin}
					class="mt-4 w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-lg">
					{#each pinInfo.cajeros as c}
						<option value={c.id}>{c.nombre}</option>
					{/each}
				</select>
			{/if}

			<div class="mt-6 flex justify-center gap-3">
				{#each [0, 1, 2, 3] as i}
					<div class="flex h-14 w-14 items-center justify-center rounded-xl border-2 text-2xl font-bold
						{pinDigitos.length > i ? 'border-emerald-500 bg-emerald-950' : 'border-slate-700'}">
						{pinDigitos.length > i ? '●' : ''}
					</div>
				{/each}
			</div>
			<div class="mx-auto mt-6 grid max-w-xs grid-cols-3 gap-3">
				{#each ['1','2','3','4','5','6','7','8','9','','0','⌫'] as d}
					{#if d === ''}<span></span>{:else}
						<button onclick={() => {
								if (d === '⌫') pinDigitos = pinDigitos.slice(0, -1);
								else if (pinDigitos.length < 4) pinDigitos += d;
								if (pinDigitos.length === 4) desbloquear();
							}}
							class="rounded-xl bg-slate-800 py-4 text-2xl font-bold hover:bg-slate-700 active:bg-emerald-700">
							{d}
						</button>
					{/if}
				{/each}
			</div>

			{#if error}
				<p class="mt-4 rounded-lg bg-red-900/50 px-4 py-2 text-sm text-red-300">{error}</p>
			{/if}
			{#if desbloqueando}
				<p class="mt-4 text-slate-400">Verificando PIN…</p>
			{/if}
		</div>

	{:else if config}
		<div class="mb-6 text-center">
			{#if config.logo_url}
				<img src={config.logo_url} alt={config.comercio} class="mx-auto mb-2 h-16 object-contain" />
			{/if}
			<h1 class="text-3xl font-bold">{config.comercio}</h1>
			<p class="text-slate-400">{config.sucursal} · Regístrate y gira la ruleta para ganar puntos</p>
		</div>

		{#if error}
			<p class="mb-4 rounded-lg bg-red-900/50 px-4 py-2 text-sm text-red-300">{error}</p>
		{/if}

		{#if paso === 'identificacion'}
			<form onsubmit={identificar} class="w-full max-w-sm space-y-4 rounded-2xl bg-slate-900 p-6">
				<h2 class="text-center text-xl font-semibold">Ingresa tus datos</h2>
				<div>
					<label for="kn" class="mb-1 block text-sm text-slate-400">Nombre completo</label>
					<input id="kn" type="text" bind:value={nombre} required minlength="2"
						class="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-lg focus:border-emerald-500 focus:outline-none" />
				</div>
				<div>
					<label for="kc" class="mb-1 block text-sm text-slate-400">Cédula de identidad</label>
					<input id="kc" type="text" bind:value={ci} required minlength="3"
						class="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-lg focus:border-emerald-500 focus:outline-none" />
				</div>
				<div>
					<label for="kt" class="mb-1 block text-sm text-slate-400">Teléfono</label>
					<input id="kt" type="tel" bind:value={telefono} required minlength="4"
						class="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-lg focus:border-emerald-500 focus:outline-none" />
				</div>
				<label class="flex items-start gap-2.5 text-xs text-slate-400">
					<input type="checkbox" bind:checked={acepta}
						class="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-600 bg-slate-800 accent-emerald-500" />
					<span>
						Acepto los <a href="/legal/terminos" target="_blank" class="text-emerald-400 underline">Términos</a>
						y la <a href="/legal/privacidad" target="_blank" class="text-emerald-400 underline">Política de privacidad</a>,
						y el uso de mis datos para el programa de puntos.
					</span>
				</label>
				<button type="submit" disabled={cargandoForm || !acepta}
					class="w-full rounded-xl bg-emerald-600 py-4 text-lg font-bold hover:bg-emerald-500 disabled:opacity-50">
					{cargandoForm ? 'Registrando…' : `Continuar (gana ${config.puntos_registro} pts)`}
				</button>
			</form>

		{:else}
			<!-- Ruleta -->
			<div class="flex flex-col items-center">
				<p class="mb-1 text-lg font-medium text-emerald-400">{bienvenida}</p>
				<p class="mb-6 text-sm text-slate-400">Tu saldo: <strong class="text-white">{saldo} pts</strong></p>

				<div class="relative">
					<!-- Puntero -->
					<div class="absolute -top-3 left-1/2 z-10 -translate-x-1/2">
						<div class="h-0 w-0 border-x-[14px] border-t-[22px] border-x-transparent border-t-white drop-shadow"></div>
					</div>
					<!-- Rueda -->
					<div class="relative h-80 w-80 overflow-hidden rounded-full border-8 border-slate-700 shadow-2xl transition-transform duration-[4400ms] ease-[cubic-bezier(0.15,0.9,0.25,1)]"
						style="background: {conicGradient}; transform: rotate({rotacion}deg)">
						{#each geometria as g}
							<div class="absolute left-1/2 top-1/2 origin-bottom font-bold text-white drop-shadow-md"
								style="transform: translate(-50%, -100%) rotate({g.medio}deg) translateY(-118px)">
								<span class="inline-block -rotate-90">{g.s.etiqueta}</span>
							</div>
						{/each}
					</div>
					<div class="absolute left-1/2 top-1/2 h-14 w-14 -translate-x-1/2 -translate-y-1/2 rounded-full bg-slate-900 shadow-inner flex items-center justify-center">
						<Icon name="target" clase="h-6 w-6 text-emerald-400" />
					</div>
				</div>

				{#if paso === 'ruleta'}
					<button onclick={girar} disabled={girando}
						class="mt-8 rounded-2xl bg-emerald-600 px-12 py-4 text-2xl font-bold shadow-lg hover:bg-emerald-500 disabled:opacity-50 animate-bounce">
						¡GIRAR!
					</button>
				{:else if girando}
					<p class="mt-8 text-xl text-slate-300">Girando…</p>
				{/if}

				{#if paso === 'resultado' && resultado}
					<div class="mt-6 text-center">
						{#if resultado.puntos > 0}
							<p class="flex items-center justify-center gap-3 text-5xl font-bold text-emerald-400"><Icon name="trophy" clase="h-12 w-12" /> ¡Ganaste {resultado.puntos} puntos!</p>
							<p class="mt-1 text-slate-400">Nuevo saldo: {resultado.saldo} pts</p>
						{:else}
							<p class="text-3xl font-bold text-slate-300">{resultado.etiqueta}</p>
							<p class="mt-1 text-slate-500">Sigue participando en tu próxima visita</p>
						{/if}
						<p class="mt-3 text-xs text-slate-500">
							Descarga la app YAPAI e ingresa con tu CI y teléfono para canjear tus puntos.
						</p>
						<button onclick={siguiente}
							class="mt-5 rounded-xl border border-slate-600 px-8 py-3 font-semibold text-slate-300 hover:bg-slate-800">
							Siguiente cliente <Icon name="arrow-right" clase="inline h-5 w-5 align-middle" />
						</button>
					</div>
				{/if}
			</div>
		{/if}
	{/if}
</div>
