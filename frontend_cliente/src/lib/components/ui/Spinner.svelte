<script lang="ts">
	let { clase = 'h-6 w-6' }: { clase?: string } = $props();
</script>

<svg class="animate-spin {clase}" viewBox="0 0 24 24" fill="none" aria-label="Cargando">
	<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity="0.25" stroke-width="3" />
	<path d="M21 12a9 9 0 1 1-6.219-8.56" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
</svg>
