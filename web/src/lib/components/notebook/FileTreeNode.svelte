<script>
	import { getFolders, getFiles } from '$lib/api/notebook.js';
	import FileTreeNode from './FileTreeNode.svelte';
	
	let { item, level = 0, onSelectFile, onSelectFolder, currentPath, selectedFilePath } = $props();
	
	let expanded = $state(false);
	let children = $state([]);
	let loading = $state(false);
	let loaded = $state(false);

	async function toggle() {
		if (item.type === 'file') {
			onSelectFile(item);
			return;
		}

		// 폴더 선택 처리 (currentPath 업데이트용)
		onSelectFolder(item.path);

		expanded = !expanded;

		if (expanded && !loaded) {
			await loadChildren();
		}
	}

	async function loadChildren() {
		loading = true;
		try {
			const [folders, files] = await Promise.all([
				getFolders(item.path),
				getFiles(item.path)
			]);
			children = [
				...folders.map(f => ({ ...f, type: 'folder' })),
				...files.map(f => ({ ...f, type: 'file' }))
			];
			loaded = true;
		} catch (e) {
			console.error(e);
		} finally {
			loading = false;
		}
	}
</script>

<div class="node-wrapper">
	<button 
		class="explorer-item {item.type}" 
		class:active={item.type === 'file' ? selectedFilePath === item.path : currentPath === item.path}
		style="padding-left: {level * 12 + 8}px"
		onclick={toggle}
	>
		<span class="icon">
			{#if item.type === 'folder'}
				<span class="folder-arrow" class:expanded={expanded}>▶</span>
				{expanded ? '📂' : '📁'}
			{:else}
				<span class="spacer"></span>
				📄
			{/if}
		</span>
		<span class="name">{item.name}</span>
	</button>

	{#if expanded}
		{#if loading}
			<div class="loading-item" style="padding-left: {(level + 1) * 12 + 24}px">Loading...</div>
		{:else}
			{#each children as child}
				<FileTreeNode 
					item={child} 
					level={level + 1} 
					{onSelectFile} 
					{onSelectFolder}
					{currentPath}
					{selectedFilePath}
				/>
			{/each}
			{#if children.length === 0}
				<div class="empty-item" style="padding-left: {(level + 1) * 12 + 24}px">비어있음</div>
			{/if}
		{/if}
	{/if}
</div>

<style>
	@import '$lib/styles/module.css';

	.node-wrapper {
		display: flex;
		flex-direction: column;
	}

	.explorer-item {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 4px 8px;
		background: none;
		border: 1px solid transparent;
		border-radius: 0;
		cursor: pointer;
		text-align: left;
		width: 100%;
		color: var(--text-secondary);
		font-size: 0.9rem;
		transition: background-color 0.1s;
		height: 28px;
	}

	.explorer-item:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
	}

	.explorer-item.active {
		background: var(--bg-tertiary);
		color: var(--primary-color);
		font-weight: 300;
	}

	.icon {
		font-size: 0.9rem;
		display: flex;
		align-items: center;
		gap: 4px;
		flex-shrink: 0;
	}

	.folder-arrow {
		font-size: 0.6rem;
		transition: transform 0.2s;
		color: var(--text-tertiary);
		width: 10px;
		display: inline-block;
		text-align: center;
	}

	.folder-arrow.expanded {
		transform: rotate(90deg);
	}

	.spacer {
		width: 10px;
	}

	.name {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		flex: 1;
	}

	.loading-item, .empty-item {
		font-size: 0.8rem;
		color: var(--text-tertiary);
		padding: 4px 0;
	}
</style>
