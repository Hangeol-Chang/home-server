<script>
	let { options = [], value = $bindable(), onchange, 'aria-label': ariaLabel = '' } = $props();

	let root;

	function select(v) {
		if (v === value) return;
		value = v;
		onchange?.(v);
	}

	function onkeydown(e) {
		const d = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
		if (!d) return;
		e.preventDefault();
		const i = options.findIndex((o) => o.value === value);
		const next = options[(i + d + options.length) % options.length];
		select(next.value);
		root.querySelectorAll('[role="radio"]')[options.indexOf(next)]?.focus();
	}
</script>

<div class="segmented" role="radiogroup" aria-label={ariaLabel} bind:this={root} {onkeydown}>
	{#each options as o (o.value)}
		<button
			type="button"
			role="radio"
			aria-checked={value === o.value}
			tabindex={value === o.value ? 0 : -1}
			class:active={value === o.value}
			onclick={() => select(o.value)}>{o.label}</button
		>
	{/each}
</div>

<style>
	.segmented {
		display: inline-flex;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface, #fff);
		overflow: hidden;
	}
	button {
		min-height: 44px;
		padding: 0 var(--spacing-md, 12px);
		border: none;
		border-left: 1px solid var(--line);
		background: transparent;
		color: var(--ink-muted);
		font: inherit;
		font-size: 0.85rem;
		cursor: pointer;
		white-space: nowrap;
	}
	button:first-child {
		border-left: none;
	}
	button.active {
		background: var(--primary);
		color: var(--primary-foreground);
		font-weight: 600;
	}
	@media (min-width: 769px) {
		button {
			min-height: 32px;
		}
	}
</style>
