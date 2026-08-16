<script>
	let { projects = [], onToggle } = $props();
	let open = $state(false);

	function close() {
		open = false;
	}

	function handleClickOutside(e) {
		if (!e.target.closest('.visibility-manager')) close();
	}
</script>

<svelte:window onclick={open ? handleClickOutside : undefined} />

<div class="visibility-manager">
	<button class="btn-secondary" onclick={() => (open = !open)}>프로젝트 표시 관리</button>

	{#if open}
		<div class="visibility-dropdown">
			{#if projects.length === 0}
				<p class="empty-message">프로젝트 없음</p>
			{/if}
			{#each projects as project (project.path)}
				<label class="visibility-item">
					<input
						type="checkbox"
						checked={!project.hide}
						onchange={(e) => onToggle(project.path, !e.target.checked)}
					/>
					<span class="visibility-name">{project.name}</span>
					{#if project.hide}<span class="hidden-tag">숨김</span>{/if}
				</label>
			{/each}
		</div>
	{/if}
</div>

<style>
	.visibility-manager {
		position: relative;
	}

	.visibility-dropdown {
		position: absolute;
		right: 0;
		top: calc(100% + 8px);
		min-width: 240px;
		max-height: 320px;
		overflow-y: auto;
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		box-shadow: var(--shadow-lg);
		padding: 8px;
		z-index: 1000;
	}

	.visibility-item {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 10px;
		border-radius: 4px;
		cursor: pointer;
	}

	.visibility-item:hover {
		background: var(--bg-secondary);
	}

	.visibility-name {
		flex: 1;
		color: var(--text-primary);
	}

	.hidden-tag {
		font-size: 0.75rem;
		color: var(--text-tertiary);
	}
</style>
