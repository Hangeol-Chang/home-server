<script>
	let { type = 'spend', size = 16 } = $props();
</script>

{#if type === 'earn'}
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="type-icon type-earn" aria-hidden="true">
		<polyline points="3 17 9 11 13 15 21 6"></polyline>
		<polyline points="15 6 21 6 21 12"></polyline>
	</svg>
{:else if type === 'save'}
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="type-icon type-save" aria-hidden="true">
		<path d="M3 21h18"></path>
		<path d="M5 21V10l7-6 7 6v11"></path>
		<path d="M9 21v-6h6v6"></path>
	</svg>
{:else}
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="type-icon type-spend" aria-hidden="true">
		<polyline points="3 7 9 13 13 9 21 18"></polyline>
		<polyline points="21 12 21 18 15 18"></polyline>
	</svg>
{/if}

<style>
	.type-icon {
		flex-shrink: 0;
	}

	.type-earn {
		color: #4caf50;
	}

	.type-spend {
		color: #f44336;
	}

	.type-save {
		color: #2196f3;
	}
</style>
