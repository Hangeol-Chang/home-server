<script>
	import { getFolders, getFiles } from '$lib/api/notebook.js';
	import FileTreeNode from './FileTreeNode.svelte';

	let { item, level = 0, onSelectFile, onSelectFolder, currentPath, selectedFilePath, onContextMenu, showHidden = false, onDrop } = $props();

	let expanded = $state(false);
	let children = $state([]);
	let loading = $state(false);
	let loaded = $state(false);
	let dragOver = $state(false);

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

	export async function loadChildren() {
		loading = true;
		try {
			const [folders, files] = await Promise.all([
				getFolders(item.path, showHidden),
				getFiles(item.path, showHidden)
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

	function getFileIcon(name) {
		const ext = name.split('.').pop()?.toLowerCase();
		const icons = {
			md: '📝', markdown: '📝',
			txt: '📄',
			csv: '📊', tsv: '📊',
			json: '🔧', yaml: '🔧', yml: '🔧', toml: '🔧',
			js: '🟨', ts: '🟦', jsx: '🟨', tsx: '🟦',
			py: '🐍', sh: '⚙️', bash: '⚙️',
			html: '🌐', css: '🎨', scss: '🎨',
			png: '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️', svg: '🖼️', webp: '🖼️',
			pdf: '📕',
			zip: '📦', tar: '📦', gz: '📦',
		};
		return icons[ext] ?? '📄';
	}

	function handleContextMenu(e) {
		e.preventDefault();
		e.stopPropagation();
		if (onContextMenu) onContextMenu({ event: e, item });
	}

	function handleDragStart(e) {
		e.stopPropagation();
		e.dataTransfer.effectAllowed = 'move';
		e.dataTransfer.setData('application/notebook-item', JSON.stringify({ path: item.path, type: item.type, name: item.name }));
	}

	function handleDragOver(e) {
		if (item.type !== 'folder') return;
		const data = e.dataTransfer.types.includes('application/notebook-item');
		if (!data) return;
		e.preventDefault();
		e.dataTransfer.dropEffect = 'move';
		dragOver = true;
	}

	function handleDragLeave(e) {
		// 자식 요소로 이동할 때 flickering 방지
		if (e.currentTarget.contains(e.relatedTarget)) return;
		dragOver = false;
	}

	function handleDrop(e) {
		e.preventDefault();
		e.stopPropagation();
		dragOver = false;
		if (item.type !== 'folder') return;
		const raw = e.dataTransfer.getData('application/notebook-item');
		if (!raw) return;
		const src = JSON.parse(raw);
		if (src.path === item.path) return;
		if (onDrop) onDrop({ srcPath: src.path, destFolder: item.path });
	}
</script>

<div
	class="node-wrapper"
	class:drag-over={dragOver}
	role="treeitem"
	aria-selected={item.type === 'file' ? selectedFilePath === item.path : currentPath === item.path}
	tabindex="-1"
	ondragover={handleDragOver}
	ondragleave={handleDragLeave}
	ondrop={handleDrop}
>
	<button
		class="explorer-item {item.type}"
		class:active={item.type === 'file' ? selectedFilePath === item.path : currentPath === item.path}
		style="padding-left: {level * 12 + 8}px"
		draggable="true"
		onclick={toggle}
		oncontextmenu={handleContextMenu}
		ondragstart={handleDragStart}
	>
		<span class="icon">
			{#if item.type === 'folder'}
				<span class="folder-arrow" class:expanded={expanded}>▶</span>
				{expanded ? '📂' : '📁'}
			{:else}
				<span class="spacer"></span>
				{getFileIcon(item.name)}
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
					{onContextMenu}
					{showHidden}
					{onDrop}
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
		color: var(--color-impact-3);
		font-weight: 600;
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

	.node-wrapper.drag-over > .explorer-item.folder {
		background: rgba(59, 186, 156, 0.15);
		outline: 1px solid var(--color-impact-3);
		color: var(--color-impact-3);
	}

	.explorer-item[draggable="true"] {
		cursor: grab;
	}

	.explorer-item[draggable="true"]:active {
		cursor: grabbing;
		opacity: 0.6;
	}
</style>
