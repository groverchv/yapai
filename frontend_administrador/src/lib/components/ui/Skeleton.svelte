<script lang="ts">
	let { clase = 'h-4 w-full' }: { clase?: string } = $props();
</script>

<div class="animate-pulse rounded bg-slate-200 {clase}" aria-hidden="true"></div>
