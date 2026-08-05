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
	const ZOOM_MIN = 0.4;
	const ZOOM_MAX = 2.5;

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
	let zoom = $state(1);
	let canvasWrapperEl = $state();

	// 드래그/핀치/팬 상태 (반응성 불필요 - 포인터/터치 이벤트 내부에서만 사용)
	let dragState = null;
	let pinchState = null;
	let panState = null;

	// 사이드패널: 'view' (메타데이터만) → 같은 노드 한번 더 클릭하면 'edit'
	let panelNode = $state(null);
	let panelMode = $state('view');
	let panelStatus = $state('planned');
	let panelStart = $state('');
	let panelEnd = $state('');
	let panelBody = $state('');
	let panelBodyLoaded = $state(false);
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
		if (connectMode || e.button !== 0) return;
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
		const dx = (e.clientX - dragState.startX) / zoom;
		const dy = (e.clientY - dragState.startY) / zoom;
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
			handleNodeActivate(nodeByPath(path));
		}
	}

	function handleNodeActivate(node) {
		if (!node) return;
		if (panelNode?.path === node.path) {
			enterEditMode();
		} else {
			openPanel(node);
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

	function nodeCenter(node) {
		const r = node.type === 'folder' ? 17 : 11;
		return { x: node.x + 28, y: node.y + r };
	}

	function handleWheelZoom(e) {
		e.preventDefault();
		const factor = Math.exp(-e.deltaY * 0.001);
		zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, zoom * factor));
	}

	function touchDistance(touches) {
		const [a, b] = touches;
		return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
	}

	function touchMidpoint(touches) {
		const [a, b] = touches;
		return { x: (a.clientX + b.clientX) / 2, y: (a.clientY + b.clientY) / 2 };
	}

	function handleTouchStart(e) {
		if (e.touches.length === 2) {
			pinchState = {
				dist: touchDistance(e.touches),
				zoom,
				mid: touchMidpoint(e.touches),
				scrollLeft: canvasWrapperEl.scrollLeft,
				scrollTop: canvasWrapperEl.scrollTop
			};
		}
	}

	function handleTouchMove(e) {
		if (pinchState && e.touches.length === 2) {
			e.preventDefault();
			const factor = touchDistance(e.touches) / pinchState.dist;
			zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, pinchState.zoom * factor));

			const mid = touchMidpoint(e.touches);
			canvasWrapperEl.scrollLeft = pinchState.scrollLeft - (mid.x - pinchState.mid.x);
			canvasWrapperEl.scrollTop = pinchState.scrollTop - (mid.y - pinchState.mid.y);
		}
	}

	function handleTouchEnd(e) {
		if (e.touches.length < 2) pinchState = null;
	}

	// PC: 휠 클릭(가운데 버튼) 드래그로 캔버스 이동
	function handleWrapperPointerDown(e) {
		if (e.button !== 1) return;
		e.preventDefault();
		panState = {
			startX: e.clientX,
			startY: e.clientY,
			scrollLeft: canvasWrapperEl.scrollLeft,
			scrollTop: canvasWrapperEl.scrollTop
		};
		window.addEventListener('pointermove', handleWrapperPointerMove);
		window.addEventListener('pointerup', handleWrapperPointerUp);
	}

	function handleWrapperPointerMove(e) {
		if (!panState) return;
		canvasWrapperEl.scrollLeft = panState.scrollLeft - (e.clientX - panState.startX);
		canvasWrapperEl.scrollTop = panState.scrollTop - (e.clientY - panState.startY);
	}

	function handleWrapperPointerUp() {
		panState = null;
		window.removeEventListener('pointermove', handleWrapperPointerMove);
		window.removeEventListener('pointerup', handleWrapperPointerUp);
	}

	function openPanel(node) {
		if (!node) return;
		panelNode = node;
		panelMode = 'view';
		panelStatus = node.status;
		panelStart = node.start_date || '';
		panelEnd = node.end_date || '';
		panelBody = '';
		panelBodyLoaded = false;
	}

	async function enterEditMode() {
		panelMode = 'edit';
		if (panelNode?.type === 'file' && !panelBodyLoaded) {
			try {
				const content = await getNodeContent(panelNode.path);
				panelBody = content.content;
				panelBodyLoaded = true;
			} catch (e) {
				error = e.message;
			}
		}
	}

	function closePanel() {
		panelNode = null;
		panelMode = 'view';
	}

	// 파일 원문 맨 위 --- ~ --- 블록만 가볍게 파싱 (다이어그램 뱃지 갱신용, 서버 파싱 로직과 동일한 규칙)
	function parseLeadingFrontmatter(text) {
		const lines = text.split('\n');
		if (lines[0]?.trim() !== '---') return {};
		let end = -1;
		for (let i = 1; i < lines.length; i++) {
			if (lines[i].trim() === '---') {
				end = i;
				break;
			}
		}
		if (end < 0) return {};
		const meta = {};
		for (const line of lines.slice(1, end)) {
			const idx = line.indexOf(':');
			if (idx < 0) continue;
			meta[line.slice(0, idx).trim()] = line
				.slice(idx + 1)
				.trim()
				.replace(/^["']|["']$/g, '');
		}
		return meta;
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
				const node = nodeByPath(panelNode.path);
				if (node) {
					node.status = panelStatus;
					node.start_date = panelStart || null;
					node.end_date = panelEnd || null;
					nodes = nodes;
				}
			} else {
				await saveNode({ path: panelNode.path, content: panelBody });
				const meta = parseLeadingFrontmatter(panelBody);
				const node = nodeByPath(panelNode.path);
				if (node) {
					node.status = STATUS_OPTIONS.some((s) => s.value === meta.status) ? meta.status : 'planned';
					node.start_date = meta.start_date || null;
					node.end_date = meta.end_date || null;
					nodes = nodes;
				}
			}
			closePanel();
		} catch (e) {
			error = e.message;
		} finally {
			panelSaving = false;
		}
	}
</script>

<div class="projects-page">
	<div class="page-header">
		<div>
			<h1>프로젝트</h1>
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
		<div
			class="canvas-wrapper"
			bind:this={canvasWrapperEl}
			onwheel={handleWheelZoom}
			onpointerdown={handleWrapperPointerDown}
			ontouchstart={handleTouchStart}
			ontouchmove={handleTouchMove}
			ontouchend={handleTouchEnd}
		>
			<div class="canvas-content" style="transform: scale({zoom});">
				<svg class="edges-layer">
					{#each edges as edge (edge.type + '|' + edge.source + '|' + edge.target)}
						{@const from = nodeByPath(edge.source)}
						{@const to = nodeByPath(edge.target)}
						{#if from && to}
							{@const a = nodeCenter(from)}
							{@const b = nodeCenter(to)}
							<line
								x1={a.x}
								y1={a.y}
								x2={b.x}
								y2={b.y}
								stroke={edge.type === 'manual' ? 'var(--accent)' : 'var(--border-color-dark)'}
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
						class:selected={panelNode?.path === node.path}
						style="left: {node.x}px; top: {node.y}px;"
						onpointerdown={(e) => handlePointerDown(e, node)}
						onclick={() => handleNodeClick(node)}
						onkeydown={(e) =>
							(e.key === 'Enter' || e.key === ' ') &&
							(connectMode ? handleNodeClick(node) : handleNodeActivate(node))}
						role="button"
						tabindex="0"
					>
						<div class="node-circle" style="background: {statusInfo(node.status).color};">
							{node.type === 'folder' ? '📁' : '📄'}
						</div>
						<div class="node-name">{node.name}</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

{#if panelNode}
	<div class="side-panel">
		<div class="side-panel-header">
			<h2>
				<span class="node-icon">{panelNode.type === 'folder' ? '📁' : '📄'}</span>
				{panelNode.name}
			</h2>
			<button class="btn-secondary" onclick={closePanel}>닫기</button>
		</div>

		{#if panelMode === 'view'}
			<dl class="meta-view">
				<dt>상태</dt>
				<dd>
					<span class="badge" style="background: {statusInfo(panelNode.status).color}; color: white;">
						{statusInfo(panelNode.status).label}
					</span>
				</dd>
				<dt>시작일</dt>
				<dd>{panelNode.start_date || '-'}</dd>
				<dt>종료일</dt>
				<dd>{panelNode.end_date || '-'}</dd>
				<dt>경로</dt>
				<dd class="meta-path">{panelNode.path}</dd>
			</dl>
			<p class="edit-hint">한 번 더 클릭하면 편집할 수 있습니다.</p>
			<div class="side-panel-footer">
				<button class="btn-primary" onclick={enterEditMode}>✏️ 편집</button>
			</div>
		{:else if panelNode.type === 'folder'}
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
			<p class="folder-panel-hint">폴더 노드는 상태/기간만 저장됩니다 ({panelNode.path}/.metadata).</p>

			<div class="side-panel-footer">
				<button class="btn-primary" onclick={savePanel} disabled={panelSaving}>
					{panelSaving ? '저장 중...' : '저장'}
				</button>
			</div>
		{:else}
			<p class="edit-hint">맨 위 --- ~ --- 블록에서 status / start_date / end_date를 직접 수정할 수 있습니다.</p>
			<div class="side-panel-editor">
				{#key panelNode.path}
					<TuiEditor bind:value={panelBody} height="100%" previewStyle="tab" />
				{/key}
			</div>

			<div class="side-panel-footer">
				<button class="btn-primary" onclick={savePanel} disabled={panelSaving}>
					{panelSaving ? '저장 중...' : '저장'}
				</button>
			</div>
		{/if}
	</div>
{/if}

<style>
	.projects-page {
		display: flex;
		flex-direction: column;
		gap: 12px;
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
		height: calc(100vh - 200px);
		min-height: 480px;
		overflow: auto;
		background: var(--bg-white);
		touch-action: none;
	}

	.canvas-content {
		position: relative;
		width: 3000px;
		height: 2000px;
		transform-origin: 0 0;
	}

	.edges-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.project-node {
		position: absolute;
		width: 56px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 3px;
		cursor: grab;
		user-select: none;
		touch-action: none;
	}

	.project-node:active {
		cursor: grabbing;
	}

	.node-circle {
		width: 22px;
		height: 22px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 11px;
		box-shadow: var(--shadow-sm);
		transition: box-shadow 0.15s, transform 0.1s;
	}

	.project-node.folder-node .node-circle {
		width: 34px;
		height: 34px;
		font-size: 15px;
		border: 2px solid var(--bg-white);
		outline: 2px solid var(--border-color-dark);
	}

	.project-node:hover .node-circle {
		transform: translateY(-2px);
		box-shadow: var(--shadow-md);
	}

	.project-node.connect-selected .node-circle {
		outline: 2px dashed var(--accent);
		outline-offset: 2px;
	}

	.project-node.selected .node-circle {
		outline: 2px solid var(--accent);
		outline-offset: 2px;
	}

	.node-name {
		font-size: 0.65rem;
		text-align: center;
		word-break: break-word;
		color: var(--text-primary);
	}

	.node-icon {
		margin-right: 4px;
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
		padding: 10px 12px;
		gap: 8px;
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

	.meta-view {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 10px 16px;
	}

	.meta-view dt {
		color: var(--text-tertiary);
		font-size: 0.9rem;
	}

	.meta-view dd {
		color: var(--text-primary);
	}

	.meta-path {
		font-size: 0.85rem;
		word-break: break-all;
		color: var(--text-secondary);
	}

	.edit-hint {
		color: var(--text-tertiary);
		font-size: 0.85rem;
	}

	.side-panel-footer {
		display: flex;
		justify-content: flex-end;
	}
</style>
