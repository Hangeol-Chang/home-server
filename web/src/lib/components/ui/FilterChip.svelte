<script>
	import { Check } from '@lucide/svelte';

	let { active = false, color = '', onclick, title = '', children } = $props();
</script>

<button type="button" class="filter-chip" class:active aria-pressed={active} {title} {onclick}>
	<span class="check-icon">
		{#if active}<Check size={14} strokeWidth={1.75} />{/if}
	</span>
	{#if color}<span class="dot" style="background: {color}"></span>{/if}
	{@render children?.()}
</button>

<style>
	.filter-chip {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		padding: 3px 10px 3px 6px;
		border: 1px solid transparent;
		border-radius: var(--radius-md);
		background: var(--surface);
		color: var(--text-primary);
		font-size: 0.8rem;
		font-weight: 300;
		cursor: pointer;
		user-select: none;
	}
	.filter-chip:hover {
		background: var(--primary-weak);
	}
	.filter-chip.active {
		border-color: var(--color-main-4);
	}
	.filter-chip:focus-visible {
		outline: 2px solid var(--primary);
		outline-offset: 1px;
	}
	.check-icon {
		display: inline-flex;
		width: 14px;
		height: 14px;
	}
	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}
	@media (max-width: 768px) {
		.filter-chip {
			min-height: 44px;
		}
	}
</style>
