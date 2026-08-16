<script>
	import { onMount } from 'svelte';
	import {
		getTopFolders,
		getSubprojects,
		getGraph,
		saveGraph,
		getNodeContent,
		saveNode,
		saveFolderMeta,
		createNode
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
	const LONG_PRESS_MS = 550;

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
	let longPressTimer = null;

	// 노드 하나: PC는 hover, 모바일은 첫 탭에서 이 경로의 메타데이터 툴팁을 보여준다
	let metaNode = $state(null);

	// 폴더 노드 우클릭(PC) / 꾹 누르기(모바일)로 뜨는 생성 메뉴
	let contextMenu = $state(null); // { node, x, y }

	// 사이드패널은 항상 편집 모드로 연다 (PC 클릭 / 모바일 두번째 탭)
	let panelNode = $state(null);
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
		if (connectMode || e.button !== 0) return;
		e.preventDefault();
		dragState = {
			path: node.path,
			pointerType: e.pointerType,
			startX: e.clientX,
			startY: e.clientY,
			clientX: e.clientX,
			clientY: e.clientY,
			origX: node.x,
			origY: node.y,
			moved: false,
			longPress: false
		};
		window.addEventListener('pointermove', handlePointerMove);
		window.addEventListener('pointerup', handlePointerUp);

		if (e.pointerType === 'touch') {
			const ds = dragState;
			longPressTimer = setTimeout(() => {
				if (dragState === ds && !ds.moved) {
					ds.longPress = true;
					openContextMenu(node, ds.clientX, ds.clientY);
				}
			}, LONG_PRESS_MS);
		}
	}

	function handlePointerMove(e) {
		if (!dragState) return;
		dragState.clientX = e.clientX;
		dragState.clientY = e.clientY;
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
		clearTimeout(longPressTimer);
		const moved = dragState?.moved;
		const path = dragState?.path;
		const pointerType = dragState?.pointerType;
		const longPress = dragState?.longPress;
		dragState = null;
		if (longPress) return; // 메뉴는 이미 떴으니 탭/클릭 처리 안함
		if (moved) {
			dirty = true;
			return;
		}
		const node = path && nodeByPath(path);
		if (!node) return;
		if (pointerType === 'touch') {
			handleNodeTap(node);
		} else {
			openEditPanel(node);
		}
	}

	// PC: 노드 우클릭 → 생성 메뉴 (파일 노드는 같은 부모폴더에 생성 + 클릭한 파일과 연결)
	function handleContextMenu(e, node) {
		if (connectMode) return;
		e.preventDefault();
		e.stopPropagation(); // 캔버스 배경 우클릭 메뉴와 겹쳐 뜨지 않게
		openContextMenu(node, e.clientX, e.clientY);
	}

	// PC: 빈 캔버스 우클릭 → 새 프로젝트 폴더 생성 메뉴 (currentFolder 바로 아래)
	function handleCanvasContextMenu(e) {
		if (connectMode) return;
		e.preventDefault();
		openContextMenu(null, e.clientX, e.clientY);
	}

	function parentPathOf(node) {
		if (!node) return currentFolder;
		if (node.type === 'folder') return node.path;
		const idx = node.path.lastIndexOf('/');
		return idx >= 0 ? node.path.slice(0, idx) : '';
	}

	function openContextMenu(node, x, y) {
		metaNode = null;
		contextMenu = { node, x, y };
	}

	function closeContextMenu() {
		contextMenu = null;
	}

	async function handleCreateNode(type) {
		const node = contextMenu?.node ?? null;
		closeContextMenu();
		if (dirty && !confirm('저장하지 않은 위치/연결 변경사항이 있습니다. 새로 만들면 사라집니다. 계속할까요?')) {
			return;
		}
		const name = prompt(`생성할 ${type === 'folder' ? '폴더' : '파일'} 이름`);
		if (!name || !name.trim()) return;
		try {
			await createNode({
				parent_path: parentPathOf(node),
				name: name.trim(),
				type,
				link_from: node?.type === 'file' ? node.path : undefined
			});
			await reloadGraph();
		} catch (e) {
			error = e.message;
		}
	}

	// 모바일: 첫 탭엔 메타데이터 툴팁만 띄우고, 그 노드를 다시 탭하면 편집창을 연다
	function handleNodeTap(node) {
		if (metaNode === node.path) {
			metaNode = null;
			openEditPanel(node);
		} else {
			metaNode = node.path;
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
		// 노드 아이콘(circle)이 row 레이아웃 맨 왼쪽에 있으므로 중심은 (x+r, y+r)
		const r = node.type === 'folder' ? 17 : 11;
		return { x: node.x + r, y: node.y + r };
	}

	// 두 노드 중심을 잇는 3차 베지어 스플라인. 두 노드 중 더 벌어진 축(가로/세로)으로만
	// 진입/진출하게 컨트롤포인트를 맞춰서, 각 노드에서 선이 상하좌우 90도로만 붙게 한다.
	function edgePath(a, b) {
		const dx = b.x - a.x;
		const dy = b.y - a.y;
		const offset = Math.min(Math.max(Math.max(Math.abs(dx), Math.abs(dy)) * 0.5, 24), 60);
		const horizontal = Math.abs(dx) >= Math.abs(dy);
		const sx = Math.sign(dx) || 1;
		const sy = Math.sign(dy) || 1;
		const c1x = horizontal ? a.x + sx * offset : a.x;
		const c1y = horizontal ? a.y : a.y + sy * offset;
		const c2x = horizontal ? b.x - sx * offset : b.x;
		const c2y = horizontal ? b.y : b.y - sy * offset;
		return `M ${a.x} ${a.y} C ${c1x} ${c1y} ${c2x} ${c2y} ${b.x} ${b.y}`;
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

	// 폴더 노드는 그 폴더의 README.md를 곧 자기 자신처럼 편집한다 (폴더 == README.md 파일노드)
	function panelNotePath(node) {
		return node.type === 'folder' ? `${node.path}/README.md` : node.path;
	}

	async function openEditPanel(node) {
		if (!node) return;
		panelNode = node;
		panelBody = '';
		metaNode = null;
		try {
			const content = await getNodeContent(panelNotePath(node));
			// frontmatter가 아직 없는 파일(= status 등을 한번도 저장한 적 없는 파일)은 기본 블록을 붙여서 보여준다
			panelBody = content.content.startsWith('---')
				? content.content
				: `---\nstatus: ${node.status}\n---\n\n${content.content}`;
		} catch (e) {
			error = e.message;
		}
	}

	function closePanel() {
		panelNode = null;
		metaNode = null;
	}

	async function savePanel() {
		if (!panelNode) return;
		panelSaving = true;
		try {
			await saveNode({ path: panelNotePath(panelNode), content: panelBody });

			// 서버가 실제로 저장한 값을 다시 읽어와 캔버스에 반영 (프론트에서 frontmatter를 다시 파싱해 추측하지 않음)
			const fresh = await getGraph(currentFolder);
			const freshNode = fresh.nodes.find((n) => n.path === panelNode.path);
			const node = nodeByPath(panelNode.path);
			if (freshNode && node) {
				node.status = freshNode.status;
				node.start_date = freshNode.start_date;
				node.end_date = freshNode.end_date;
				nodes = [...nodes]; // 새 배열 참조로 캔버스 리렌더 강제
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
			<h1>Projects</h1>
		</div>
		<div class="toolbar-actions">
			<ProjectVisibilityManager projects={subprojects} onToggle={handleToggleProjectHide} />
			<button class="btn-secondary" class:active={connectMode} onclick={toggleConnectMode}>
				{connectMode ? '연결 모드 (클릭해서 종료)' : '노드 연결하기'}
			</button>
			<button class="btn-primary" onclick={persistGraph} disabled={!dirty || saving}>
				{saving ? '저장 중...' : dirty ? '저장' : '저장됨'}
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
			role="presentation"
			bind:this={canvasWrapperEl}
			onwheel={handleWheelZoom}
			onpointerdown={handleWrapperPointerDown}
			oncontextmenu={handleCanvasContextMenu}
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
							<path
								d={edgePath(a, b)}
								fill="none"
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
						class:meta-active={metaNode === node.path}
						style="left: {node.x}px; top: {node.y}px;"
						onpointerdown={(e) => handlePointerDown(e, node)}
						onclick={() => handleNodeClick(node)}
						oncontextmenu={(e) => handleContextMenu(e, node)}
						onkeydown={(e) =>
							(e.key === 'Enter' || e.key === ' ') &&
							(connectMode ? handleNodeClick(node) : openEditPanel(node))}
						role="button"
						tabindex="0"
					>
						<div class="node-circle" style="background: {statusInfo(node.status).color};">
							{node.type === 'folder' ? '📁' : '📄'}
						</div>
						<div class="node-label">
							<span class="node-name">{node.name}</span>
							<div class="node-meta-tooltip">
								<span
									class="badge"
									style="background: {statusInfo(node.status).color}; color: white;"
								>
									{statusInfo(node.status).label}
								</span>
								<span class="node-meta-dates">{node.start_date || '-'} ~ {node.end_date || '-'}</span>
							</div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

{#if contextMenu}
	<div
		class="context-menu-overlay"
		role="presentation"
		onclick={closeContextMenu}
		oncontextmenu={(e) => {
			e.preventDefault();
			closeContextMenu();
		}}
	></div>
	<div class="context-menu" style="left: {contextMenu.x}px; top: {contextMenu.y}px;">
		{#if contextMenu.node}
			<button onclick={() => handleCreateNode('file')}>파일 생성</button>
		{/if}
		<button onclick={() => handleCreateNode('folder')}>폴더 생성</button>
	</div>
{/if}

{#if panelNode}
	<div class="side-panel">
		<div class="side-panel-header">
			<h2>
				<span class="node-icon">{panelNode.type === 'folder' ? '📁' : '📄'}</span>
				{panelNode.name}
			</h2>
			<button class="btn-secondary" onclick={savePanel} disabled={panelSaving}>닫기</button>
		</div>
		
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
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64'%3E%3Cpath d='M64 0H0V64' fill='none' stroke='%238D8C8A' stroke-opacity='0.45' stroke-width='1' stroke-dasharray='4 4'/%3E%3C/svg%3E");
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
		width: max-content;
		max-width: 160px;
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 6px;
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
		flex-shrink: 0;
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

	.node-label {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 2px;
		min-width: 0;
	}

	.node-name {
		font-size: 0.7rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 130px;
		color: var(--text-primary);
	}

	.node-meta-tooltip {
		display: none;
		align-items: center;
		gap: 6px;
		font-size: 0.65rem;
		white-space: nowrap;
	}

	.node-meta-tooltip .badge {
		padding: 1px 6px;
		border-radius: 8px;
		font-size: 0.6rem;
	}

	.node-meta-dates {
		color: var(--text-tertiary);
	}

	.project-node:hover .node-meta-tooltip,
	.project-node.meta-active .node-meta-tooltip {
		display: flex;
	}

	.node-icon {
		margin-right: 4px;
	}

	.context-menu-overlay {
		position: fixed;
		inset: 0;
		z-index: 1100;
	}

	.context-menu {
		position: fixed;
		z-index: 1101;
		display: flex;
		flex-direction: column;
		min-width: 140px;
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		box-shadow: var(--shadow-lg);
		padding: 4px;
	}

	.context-menu button {
		background: none;
		border: none;
		text-align: left;
		padding: 8px 10px;
		border-radius: 6px;
		font-size: 0.9rem;
		color: var(--text-primary);
		cursor: pointer;
	}

	.context-menu button:hover {
		background: var(--bg-secondary);
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

	.side-panel-editor {
		flex: 1;
		min-height: 0;
	}

	.side-panel-footer {
		display: flex;
		justify-content: flex-end;
	}
</style>
