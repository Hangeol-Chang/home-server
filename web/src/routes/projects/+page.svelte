<script>
	import { onMount } from 'svelte';
	import {
		getTopFolders,
		getSubprojects,
		getGraph,
		saveGraph,
		getNodeContent,
		saveNode,
		saveFolderMeta
	} from '$lib/api/projects.js';
	import { pullRepository } from '$lib/api/notebook.js';
	import TuiEditor from '$lib/components/notebook/TuiEditor.svelte';
	import ProjectVisibilityManager from '$lib/components/projects/ProjectVisibilityManager.svelte';
	import '$lib/styles/module.css';
	import '$lib/styles/module-common.css';

	const STATUS_OPTIONS = [
		{ value: 'planned', label: '예정', color: '#9CA3AF' },
		{ value: 'in_progress', label: '진행중', color: '#3B82F6' },
		{ value: 'paused', label: '보류', color: '#F59E0B' },
		{ value: 'done', label: '완료', color: '#10B981' }
	];
	const DRAG_THRESHOLD = 5;

	function statusInfo(value) {
		return STATUS_OPTIONS.find((s) => s.value === value) || STATUS_OPTIONS[0];
	}

	let loading = $state(true);
	let error = $state('');
	let folders = $state([]); // 0_ 최상위 폴더 (탭)
	let currentFolder = $state('');
	let subprojects = $state([]); // 현재 폴더 바로 아래 프로젝트 목록 (숨김 포함) - 표시관리용
	let nodes = $state([]);
	let edges = $state([]);
	let connectMode = $state(false);
	let connectFrom = $state(null);
	let dirty = $state(false);
	let saving = $state(false);

	// 드래그 상태 (반응성 불필요 - 포인터 이벤트 내부에서만 사용)
	let dragState = null;

	// 사이드패널
	let panelNode = $state(null);
	let panelStatus = $state('planned');
	let panelStart = $state('');
	let panelEnd = $state('');
	let panelBody = $state('');
	let panelSaving = $state(false);

	$effect(() => {
		function handleBeforeUnload(e) {
			if (!dirty) return;
			e.preventDefault();
			e.returnValue = '';
		}
		window.addEventListener('beforeunload', handleBeforeUnload);
		return () => window.removeEventListener('beforeunload', handleBeforeUnload);
	});

	onMount(async () => {
		try {
			await pullRepository();
		} catch (e) {
			console.warn('git pull 실패, 로컬 상태로 계속 진행:', e);
		}
		try {
			folders = await getTopFolders();
			if (folders.length > 0) {
				await selectFolder(folders[0]);
			}
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	});

	async function refreshSubprojects() {
		try {
			subprojects = await getSubprojects(currentFolder);
		} catch (e) {
			error = e.message;
		}
	}

	async function handleToggleProjectHide(path, hide) {
		try {
			await saveFolderMeta({ path, hide });
			await Promise.all([refreshSubprojects(), reloadGraph()]);
		} catch (e) {
			error = e.message;
		}
	}

	async function reloadGraph() {
		const graph = await getGraph(currentFolder);
		nodes = graph.nodes;
		edges = graph.edges;
		dirty = false;
	}

	async function selectFolder(folder) {
		if (dirty && !confirm('저장하지 않은 위치/연결 변경사항이 있습니다. 이동하면 사라집니다. 계속할까요?')) {
			return;
		}
		currentFolder = folder;
		closePanel();
		loading = true;
		error = '';
		try {
			await Promise.all([reloadGraph(), refreshSubprojects()]);
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function edgeKey(a, b) {
		return [a, b].sort().join('|');
	}

	function nodeByPath(path) {
		return nodes.find((n) => n.path === path);
	}

	async function persistGraph() {
		if (saving) return;
		saving = true;
		const positions = {};
		for (const n of nodes) positions[n.path] = { x: n.x, y: n.y };
		const manualEdges = edges.filter((e) => e.type === 'manual');
		try {
			await saveGraph(currentFolder, positions, manualEdges);
			dirty = false;
		} catch (e) {
			error = e.message;
		} finally {
			saving = false;
		}
	}

	function handlePointerDown(e, node) {
		if (connectMode) return;
		e.preventDefault();
		dragState = {
			path: node.path,
			startX: e.clientX,
			startY: e.clientY,
			origX: node.x,
			origY: node.y,
			moved: false
		};
		window.addEventListener('pointermove', handlePointerMove);
		window.addEventListener('pointerup', handlePointerUp);
	}

	function handlePointerMove(e) {
		if (!dragState) return;
		const dx = e.clientX - dragState.startX;
		const dy = e.clientY - dragState.startY;
		if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) {
			dragState.moved = true;
		}
		const node = nodeByPath(dragState.path);
		if (node) {
			node.x = dragState.origX + dx;
			node.y = dragState.origY + dy;
			nodes = nodes;
		}
	}

	function handlePointerUp() {
		window.removeEventListener('pointermove', handlePointerMove);
		window.removeEventListener('pointerup', handlePointerUp);
		const moved = dragState?.moved;
		const path = dragState?.path;
		dragState = null;
		if (moved) {
			dirty = true;
		} else if (path) {
			openPanel(nodeByPath(path));
		}
	}

	function handleNodeClick(node) {
		if (!connectMode) return; // 드래그 흐름(pointerup)에서 클릭 오픈 처리하므로 여기선 연결모드만
		if (!connectFrom) {
			connectFrom = node.path;
			return;
		}
		if (connectFrom === node.path) {
			connectFrom = null;
			return;
		}
		const key = edgeKey(connectFrom, node.path);
		const treeEdge = edges.some((e) => e.type === 'tree' && edgeKey(e.source, e.target) === key);
		if (!treeEdge) {
			const existingIdx = edges.findIndex(
				(e) => e.type === 'manual' && edgeKey(e.source, e.target) === key
			);
			if (existingIdx >= 0) {
				edges = edges.filter((_, i) => i !== existingIdx);
			} else {
				edges = [...edges, { source: connectFrom, target: node.path, type: 'manual' }];
			}
			dirty = true;
		}
		connectFrom = null;
	}

	function toggleConnectMode() {
		connectMode = !connectMode;
		connectFrom = null;
	}

	async function openPanel(node) {
		if (!node) return;
		panelNode = node;
		panelStatus = node.status;
		panelStart = node.start_date || '';
		panelEnd = node.end_date || '';
		panelBody = '';
		if (node.type === 'file') {
			try {
				const content = await getNodeContent(node.path);
				panelBody = content.body;
			} catch (e) {
				error = e.message;
			}
		}
	}

	function closePanel() {
		panelNode = null;
	}

	async function savePanel() {
		if (!panelNode) return;
		panelSaving = true;
		try {
			if (panelNode.type === 'folder') {
				await saveFolderMeta({
					path: panelNode.path,
					status: panelStatus,
					start_date: panelStart || null,
					end_date: panelEnd || null
				});
			} else {
				await saveNode({
					path: panelNode.path,
					status: panelStatus,
					start_date: panelStart || null,
					end_date: panelEnd || null,
					content: panelBody
				});
			}
			const node = nodeByPath(panelNode.path);
			if (node) {
				node.status = panelStatus;
				node.start_date = panelStart || null;
				node.end_date = panelEnd || null;
				nodes = nodes;
			}
			closePanel();
		} catch (e) {
			error = e.message;
		} finally {
			panelSaving = false;
		}
	}
</script>

<div class="module-container projects-page">
	<div class="page-header">
		<div>
			<h1>프로젝트</h1>
			<p class="subtitle">obsidian-vault의 0_ 프로젝트 폴더를 다이어그램으로 봅니다</p>
		</div>
		<div class="toolbar-actions">
			<ProjectVisibilityManager projects={subprojects} onToggle={handleToggleProjectHide} />
			<button class="btn-secondary" class:active={connectMode} onclick={toggleConnectMode}>
				{connectMode ? '🔗 연결 모드 (클릭해서 종료)' : '🔗 노드 연결하기'}
			</button>
			<button class="btn-primary" onclick={persistGraph} disabled={!dirty || saving}>
				{saving ? '저장 중...' : dirty ? '💾 저장' : '저장됨'}
			</button>
		</div>
	</div>

	{#if error}
		<div class="error-message">{error}</div>
	{/if}

	<div class="tab-buttons">
		{#each folders as folder (folder)}
			<button
				class="tab-btn"
				class:active={folder === currentFolder}
				onclick={() => selectFolder(folder)}
			>
				{folder}
			</button>
		{/each}
	</div>

	{#if loading}
		<div class="spinner"></div>
	{:else}
		<div class="canvas-wrapper">
			<svg class="edges-layer">
				{#each edges as edge (edge.type + '|' + edge.source + '|' + edge.target)}
					{@const from = nodeByPath(edge.source)}
					{@const to = nodeByPath(edge.target)}
					{#if from && to}
						<line
							x1={from.x + 90}
							y1={from.y + 30}
							x2={to.x + 90}
							y2={to.y + 30}
							stroke={edge.type === 'manual' ? 'var(--accent)' : 'var(--border-color)'}
							stroke-width="2"
							stroke-dasharray={edge.type === 'manual' ? '6 4' : 'none'}
						/>
					{/if}
				{/each}
			</svg>

			{#each nodes as node (node.path)}
				<div
					class="project-node"
					class:folder-node={node.type === 'folder'}
					class:connect-selected={connectFrom === node.path}
					style="left: {node.x}px; top: {node.y}px; border-color: {statusInfo(node.status).color};"
					onpointerdown={(e) => handlePointerDown(e, node)}
					onclick={() => handleNodeClick(node)}
					onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && (connectMode ? handleNodeClick(node) : openPanel(node))}
					role="button"
					tabindex="0"
				>
					<div class="node-title">
						<span class="node-icon">{node.type === 'folder' ? '📁' : '📄'}</span>
						{node.name}
					</div>
					<span class="badge" style="background: {statusInfo(node.status).color}; color: white;">
						{statusInfo(node.status).label}
					</span>
					{#if node.start_date || node.end_date}
						<div class="node-dates">{node.start_date || '?'} ~ {node.end_date || '?'}</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

{#if panelNode}
	<div class="side-panel-overlay" onclick={closePanel} role="presentation"></div>
	<div class="side-panel">
		<div class="side-panel-header">
			<h2>{panelNode.name}</h2>
			<button class="btn-secondary" onclick={closePanel}>닫기</button>
		</div>

		<div class="form-row">
			<div class="form-group">
				<label for="panel-status">상태</label>
				<select id="panel-status" bind:value={panelStatus}>
					{#each STATUS_OPTIONS as opt (opt.value)}
						<option value={opt.value}>{opt.label}</option>
					{/each}
				</select>
			</div>
			<div class="form-group">
				<label for="panel-start">시작일</label>
				<input id="panel-start" type="date" bind:value={panelStart} />
			</div>
			<div class="form-group">
				<label for="panel-end">종료일</label>
				<input id="panel-end" type="date" bind:value={panelEnd} />
			</div>
		</div>

		{#if panelNode.type === 'file'}
			<div class="side-panel-editor">
				{#key panelNode.path}
					<TuiEditor bind:value={panelBody} height="100%" />
				{/key}
			</div>
		{:else}
			<p class="folder-panel-hint">폴더 노드는 상태/기간만 저장됩니다 ({panelNode.path}/.metadata).</p>
		{/if}

		<div class="side-panel-footer">
			<button class="btn-primary" onclick={savePanel} disabled={panelSaving}>
				{panelSaving ? '저장 중...' : '저장'}
			</button>
		</div>
	</div>
{/if}

<style>
	.projects-page {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.toolbar-actions {
		display: flex;
		gap: 8px;
	}

	.btn-secondary.active {
		background: var(--accent);
		color: white;
		border-color: var(--accent);
	}

	.canvas-wrapper {
		position: relative;
		width: 100%;
		height: 70vh;
		overflow: auto;
		border: 1px solid var(--border-color);
		border-radius: 8px;
		background: var(--bg-secondary);
	}

	.edges-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 3000px;
		height: 2000px;
		pointer-events: none;
	}

	.project-node {
		position: absolute;
		width: 180px;
		padding: 12px;
		background: var(--bg-primary);
		border: 2px solid var(--border-color);
		border-radius: 8px;
		box-shadow: var(--shadow-sm);
		cursor: grab;
		user-select: none;
		touch-action: none;
	}

	.project-node:active {
		cursor: grabbing;
	}

	.project-node.connect-selected {
		outline: 2px dashed var(--accent);
		outline-offset: 2px;
	}

	.project-node.folder-node {
		width: 200px;
		border-width: 3px;
		background: var(--bg-secondary);
		font-weight: 500;
	}

	.node-icon {
		margin-right: 4px;
	}

	.node-title {
		font-weight: 500;
		margin-bottom: 6px;
		word-break: break-word;
	}

	.node-dates {
		margin-top: 6px;
		font-size: 0.8rem;
		color: var(--text-tertiary);
	}

	.side-panel-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.4);
		z-index: 999;
	}

	.side-panel {
		position: fixed;
		top: 0;
		right: 0;
		bottom: 0;
		width: min(600px, 90vw);
		background: var(--bg-primary);
		box-shadow: var(--shadow-lg);
		z-index: 1000;
		display: flex;
		flex-direction: column;
		padding: 24px;
		gap: 16px;
	}

	.side-panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.side-panel .form-row {
		grid-template-columns: repeat(3, 1fr);
	}

	.side-panel .form-group {
		flex-direction: column;
		align-items: stretch;
	}

	.side-panel .form-group label {
		min-width: 0;
	}

	.side-panel-editor {
		flex: 1;
		min-height: 0;
	}

	.folder-panel-hint {
		color: var(--text-tertiary);
		font-size: 0.9rem;
	}

	.side-panel-footer {
		display: flex;
		justify-content: flex-end;
	}
</style>
