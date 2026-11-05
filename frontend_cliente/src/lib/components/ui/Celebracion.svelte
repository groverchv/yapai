<script lang="ts">
	// Overlay de celebración: check + count-up de puntos + confetti CSS.
	// Se muestra ~1.4s y llama onfin para continuar el flujo.
	import { onMount } from 'svelte';

	let {
		puntos = 0,
		titulo = '¡Pase generado!',
		subtitulo = '',
		onfin
	}: {
		puntos?: number;
		titulo?: string;
		subtitulo?: string;
		onfin: () => void;
	} = $props();

	let mostrado = $state(0);
	let visible = $state(true);

	const CONFETTI = Array.from({ length: 14 }, (_, i) => ({
		x: (i * 7) % 100,
		d: 0.9 + (i % 5) * 0.22,
		delay: (i % 4) * 0.12,
		color: ['#4f46e5', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'][i % 5],
		rot: (i * 47) % 360
	}));

	onMount(() => {
		navigator.vibrate?.(60);
		// Count-up: 0 → puntos en ~700ms
		const t0 = performance.now();
		const tick = (t: number) => {
			const k = Math.min(1, (t - t0) / 700);
			mostrado = Math.round(puntos * (1 - (1 - k) ** 3)); // ease-out cubic
			if (k < 1) requestAnimationFrame(tick);
		};
		requestAnimationFrame(tick);
		const fin = setTimeout(() => { visible = false; onfin(); }, 1400);
		return () => clearTimeout(fin);
	});
</script>

{#if visible}
	<div class="fixed inset-0 z-[90] flex flex-col items-center justify-center bg-navy/95 px-6 backdrop-blur-sm">
		{#each CONFETTI as c}
			<span class="confetti" style="left:{c.x}%; animation-duration:{c.d}s; animation-delay:{c.delay}s;
				background:{c.color}; transform:rotate({c.rot}deg)"></span>
		{/each}
		<div class="celebra-check flex h-20 w-20 items-center justify-center rounded-full bg-emerald-500">
			<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" class="h-10 w-10"
				stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
				<path d="M20 6 9 17l-5-5" />
			</svg>
		</div>
		<p class="mt-5 text-2xl font-bold text-white">{titulo}</p>
		{#if puntos > 0}
			<p class="mt-1 text-4xl font-extrabold text-amber-400" aria-live="polite">−{mostrado} pts</p>
		{/if}
		{#if subtitulo}
			<p class="mt-2 text-center text-sm text-white/70">{subtitulo}</p>
		{/if}
	</div>
{/if}

<style>
	.celebra-check {
		animation: pop 0.45s cubic-bezier(0.2, 1.6, 0.4, 1) both;
	}
	@keyframes pop {
		from { transform: scale(0); }
		to { transform: scale(1); }
	}
	.confetti {
		position: absolute;
		top: -12px;
		width: 10px;
		height: 14px;
		border-radius: 2px;
		animation-name: caer;
		animation-timing-function: ease-in;
		animation-fill-mode: both;
	}
	@keyframes caer {
		to { transform: translateY(105vh) rotate(540deg); }
	}
	@media (prefers-reduced-motion: reduce) {
		.celebra-check, .confetti { animation: none; }
	}
</style>
