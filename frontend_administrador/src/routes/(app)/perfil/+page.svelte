<script lang="ts">
	import { auth } from '#lib/stores/auth.svelte';
	import { i18n, type Locale } from '#lib/i18n.svelte';
	import Seguridad2fa from '#lib/components/ui/Seguridad2fa.svelte';

	const idiomas: { code: Locale; nombre: string }[] = [
		{ code: 'es', nombre: 'Español' },
		{ code: 'en', nombre: 'English' }
	];
</script>

<div class="max-w-2xl space-y-6">
	<div class="rounded-xl border border-slate-200 bg-white p-6">
		<h3 class="font-semibold text-slate-800">Mi cuenta</h3>
		<div class="mt-4 space-y-2 text-sm">
			<p><span class="text-slate-400">Nombre:</span> <strong class="text-slate-700">{auth.usuario?.nombre}</strong></p>
			<p><span class="text-slate-400">Correo:</span> <strong class="text-slate-700">{auth.usuario?.email}</strong></p>
			<p><span class="text-slate-400">Rol:</span> <strong class="text-slate-700">Administrador de plataforma</strong></p>
			<p>
				<span class="text-slate-400">Idioma:</span>
				{#each idiomas as idioma}
					<button onclick={() => i18n.set(idioma.code)}
						class="ml-2 rounded-full px-3 py-0.5 text-xs font-semibold transition
							{i18n.locale === idioma.code ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}">
						{idioma.nombre}
					</button>
				{/each}
			</p>
		</div>
	</div>

	<Seguridad2fa />
</div>
