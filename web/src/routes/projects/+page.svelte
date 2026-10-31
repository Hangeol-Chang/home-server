<script>
	import { Folder, FileText } from '@lucide/svelte';
	import { onMount } from 'svelte';
	import {
		getTopFolders,
		getSubprojects,
		getGraph,
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
	const ZOOM_MIN = 0.2;
	const ZOOM_MAX = 3;
	const LONG_PRESS_MS = 550;

	// force layout 파라미터 (d3-force 기본값 계열). 화면이 너무 빽빽/헐겁다면 여기만 조정
	const REPULSION = 400; // 노드끼리 밀어내는 힘 (1/d)
	const LINK_DISTANCE = { tree: 70, link: 110 };
	const LINK_STRENGTH = 0.3;
	const GRAVITY = 0.06; // 원점으로 당기는 힘 — 떨어진 덩어리가 멀리 날아가지 않게
	const VELOCITY_DECAY = 0.6;
	const ALPHA_DECAY = 0.977;
	const ALPHA_MIN = 0.002;

	function statusInfo(value) {
		return STATUS_OPTIONS.find((s) => s.value === value) || STATUS_OPTIONS[0];
	}

	function nodeRadius(node) {
		return node.type === 'folder' ? 17 : 11;
	}

	let loading = $state(true);
	let error = $state('');
	let folders = $state([]); // 0_ 최상위 폴더 (탭)
	let currentFolder = $state('');
	let subprojects = $state([]); // 현재 폴더 바로 아래 프로젝트 목록 (숨김 포함) - 표시관리용
	let nodes = $state([]);
	let edges = $state([]);
	let pos = $state.raw({}); // path -> {x, y} 노드 중심 (시뮬레이션이 매 프레임 새 객체로 교체)
	let zoom = $state(1);
	let panX = $state(0);
	let panY = $state(0);
	let canvasWrapperEl = $state();

	// 시뮬레이션/드래그/핀치/팬 상태 (반응성 불필요)
	let sim = null; // { list, byPath, links, alpha }
	let simFrame = null;
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

	onMount(() => {
		(async () => {
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
		})();
		return () => cancelAnimationFrame(simFrame);
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
		startSimulation();
	}

	async function selectFolder(folder) {
		currentFolder = folder;
		closePanel();
		sim = null; // 다른 폴더는 처음부터 다시 배치
		centerView();
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

	function nodeByPath(path) {
		return nodes.find((n) => n.path === path);
	}

	// ===== Force layout =====
	// 기존 노드는 현재 위치를 유지하고, 새 노드는 연결된 노드 근처(없으면 원점 주변 나선)에 놓은 뒤 시뮬레이션을 다시 돌린다
	function startSimulation() {
		const prev = sim?.byPath ?? new Map();
		// eslint-disable-next-line svelte/prefer-svelte-reactivity -- 시뮬레이션 내부용, 반응성 불필요
		const byPath = new Map();
		const list = nodes.map((n, i) => {
			const old = prev.get(n.path);
			const s = old
				? { ...old, fx: null, fy: null }
				: { path: n.path, x: 0, y: 0, vx: 0, vy: 0, fx: null, fy: null, placed: false, i };
			byPath.set(n.path, s);
			return s;
		});
		const links = edges
			.map((e) => ({
				s: byPath.get(e.source),
				t: byPath.get(e.target),
				dist: LINK_DISTANCE[e.type]
			}))
			.filter((l) => l.s && l.t);

		// 트리 순서(부모가 먼저 나옴)대로 배치하므로 대부분 부모 옆에 자리 잡는다
		for (const s of list) {
			if (s.placed !== false) continue;
			const anchor = links.find(
				(l) => (l.t === s && l.s.placed !== false) || (l.s === s && l.t.placed !== false)
			);
			const base = anchor ? (anchor.t === s ? anchor.s : anchor.t) : { x: 0, y: 0 };
			const angle = s.i * 2.39996; // golden angle
			const r = anchor ? 30 : 12 * Math.sqrt(s.i + 1);
			s.x = base.x + r * Math.cos(angle);
			s.y = base.y + r * Math.sin(angle);
			delete s.placed;
		}

		sim = { list, byPath, links, alpha: prev.size ? 0.5 : 1 };
		runSimulation();
	}

	function runSimulation() {
		if (simFrame) return;
		const step = () => {
			tick();
			if (sim.alpha < ALPHA_MIN && !dragState) {
				simFrame = null;
				return;
			}
			simFrame = requestAnimationFrame(step);
		};
		simFrame = requestAnimationFrame(step);
	}

	// ponytail: O(n²) 반발력 — 수백 노드까진 충분, 그 이상이면 Barnes-Hut(quadtree) 근사로 교체
	function tick() {
		const { list, links } = sim;
		const a = sim.alpha;
		for (let i = 0; i < list.length; i++) {
			const p = list[i];
			for (let j = i + 1; j < list.length; j++) {
				const q = list[j];
				let dx = q.x - p.x;
				let dy = q.y - p.y;
				if (dx === 0 && dy === 0) dx = Math.random() - 0.5;
				const d2 = Math.max(dx * dx + dy * dy, 25);
				const f = (REPULSION * a) / d2;
				p.vx -= dx * f;
				p.vy -= dy * f;
				q.vx += dx * f;
				q.vy += dy * f;
			}
		}
		for (const { s, t, dist } of links) {
			const dx = t.x + t.vx - s.x - s.vx;
			const dy = t.y + t.vy - s.y - s.vy;
			const d = Math.hypot(dx, dy) || 1;
			const f = ((d - dist) / d) * LINK_STRENGTH * a * 0.5;
			s.vx += dx * f;
			s.vy += dy * f;
			t.vx -= dx * f;
			t.vy -= dy * f;
		}
		const next = {};
		for (const p of list) {
			p.vx -= p.x * GRAVITY * a;
			p.vy -= p.y * GRAVITY * a;
			if (p.fx != null) {
				p.x = p.fx;
				p.y = p.fy;
				p.vx = p.vy = 0;
			} else {
				p.vx *= VELOCITY_DECAY;
				p.vy *= VELOCITY_DECAY;
				p.x += p.vx;
				p.y += p.vy;
			}
			next[p.path] = { x: p.x, y: p.y };
		}
		pos = next;
		sim.alpha *= ALPHA_DECAY;
	}

	// ===== 좌표 변환 / 뷰 =====
	function toWorld(clientX, clientY) {
		const rect = canvasWrapperEl.getBoundingClientRect();
		return { x: (clientX - rect.left - panX) / zoom, y: (clientY - rect.top - panY) / zoom };
	}

	function centerView() {
		if (!canvasWrapperEl) return;
		panX = canvasWrapperEl.clientWidth / 2;
		panY = canvasWrapperEl.clientHeight / 2;
	}

	// (clientX, clientY) 아래 지점을 고정한 채로 줌
	function zoomAt(clientX, clientY, newZoom) {
		const w = toWorld(clientX, clientY);
		const rect = canvasWrapperEl.getBoundingClientRect();
		zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, newZoom));
		panX = clientX - rect.left - w.x * zoom;
		panY = clientY - rect.top - w.y * zoom;
	}

	// ===== 노드 드래그 (Obsidian처럼 드래그 중엔 고정, 놓으면 다시 시뮬레이션에 맡긴다) =====
	function handlePointerDown(e, node) {
		if (e.button !== 0) return;
		e.preventDefault();
		e.stopPropagation(); // 배경 팬이 같이 시작되지 않게
		dragState = {
			path: node.path,
			pointerType: e.pointerType,
			startX: e.clientX,
			startY: e.clientY,
			clientX: e.clientX,
			clientY: e.clientY,
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
		if (!dragState || dragState.longPress) return;
		dragState.clientX = e.clientX;
		dragState.clientY = e.clientY;
		if (
			!dragState.moved &&
			Math.hypot(e.clientX - dragState.startX, e.clientY - dragState.startY) <= DRAG_THRESHOLD
		) {
			return;
		}
		dragState.moved = true;
		const s = sim?.byPath.get(dragState.path);
		if (!s) return;
		const w = toWorld(e.clientX, e.clientY);
		s.fx = w.x;
		s.fy = w.y;
		sim.alpha = Math.max(sim.alpha, 0.3);
		runSimulation();
	}

	function handlePointerUp() {
		window.removeEventListener('pointermove', handlePointerMove);
		window.removeEventListener('pointerup', handlePointerUp);
		clearTimeout(longPressTimer);
		const { moved, path, pointerType, longPress } = dragState ?? {};
		dragState = null;
		const s = path && sim?.byPath.get(path);
		if (s) s.fx = s.fy = null;
		if (longPress || moved) return; // 메뉴가 이미 떴거나 드래그였으면 탭/클릭 처리 안함
		const node = path && nodeByPath(path);
		if (!node) return;
		if (pointerType === 'touch') {
			handleNodeTap(node);
		} else {
			openEditPanel(node);
		}
	}

	// PC: 노드 우클릭 → 생성 메뉴 (파일 노드는 같은 부모폴더에 생성 + 클릭한 파일 본문에 [[링크]] 추가)
	function handleContextMenu(e, node) {
		e.preventDefault();
		e.stopPropagation(); // 캔버스 배경 우클릭 메뉴와 겹쳐 뜨지 않게
		openContextMenu(node, e.clientX, e.clientY);
	}

	// PC: 빈 캔버스 우클릭 → 새 프로젝트 폴더 생성 메뉴 (currentFolder 바로 아래)
	function handleCanvasContextMenu(e) {
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

	// ===== 캔버스 팬/줌 =====
	function handleWheelZoom(e) {
		e.preventDefault();
		zoomAt(e.clientX, e.clientY, zoom * Math.exp(-e.deltaY * 0.001));
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
			handleWrapperPointerUp(); // 한 손가락 팬 취소, 핀치로 전환
			const mid = touchMidpoint(e.touches);
			pinchState = { dist: touchDistance(e.touches), zoom, world: toWorld(mid.x, mid.y) };
		}
	}

	function handleTouchMove(e) {
		if (pinchState && e.touches.length === 2) {
			e.preventDefault();
			const mid = touchMidpoint(e.touches);
			const rect = canvasWrapperEl.getBoundingClientRect();
			zoom = Math.min(
				ZOOM_MAX,
				Math.max(ZOOM_MIN, (pinchState.zoom * touchDistance(e.touches)) / pinchState.dist)
			);
			panX = mid.x - rect.left - pinchState.world.x * zoom;
			panY = mid.y - rect.top - pinchState.world.y * zoom;
		}
	}

	function handleTouchEnd(e) {
		if (e.touches.length < 2) pinchState = null;
	}

	// 빈 배경 드래그(왼쪽/휠 버튼, 한 손가락 터치)로 캔버스 이동
	function handleWrapperPointerDown(e) {
		if (e.button !== 0 && e.button !== 1) return;
		if (pinchState) return;
		e.preventDefault();
		panState = { startX: e.clientX, startY: e.clientY, panX, panY };
		window.addEventListener('pointermove', handleWrapperPointerMove);
		window.addEventListener('pointerup', handleWrapperPointerUp);
	}

	function handleWrapperPointerMove(e) {
		if (!panState) return;
		panX = panState.panX + (e.clientX - panState.startX);
		panY = panState.panY + (e.clientY - panState.startY);
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
			// 상태/기간뿐 아니라 본문 [[링크]]도 바뀌었을 수 있으니 그래프 전체를 다시 받는다 (위치는 유지)
			await reloadGraph();
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
			<button class="btn-secondary" onclick={centerView}>가운데로</button>
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
		{#if loading}
			<div class="spinner"></div>
		{/if}
		<div class="canvas-content" style="transform: translate({panX}px, {panY}px) scale({zoom});">
			<svg class="edges-layer">
				{#each edges as edge (edge.type + '|' + edge.source + '|' + edge.target)}
					{@const a = pos[edge.source]}
					{@const b = pos[edge.target]}
					{#if a && b}
						<line
							x1={a.x}
							y1={a.y}
							x2={b.x}
							y2={b.y}
							stroke={edge.type === 'link' ? 'var(--accent)' : 'var(--border-color-dark)'}
							stroke-width="1.5"
						/>
					{/if}
				{/each}
			</svg>

			{#each nodes as node (node.path)}
				{@const p = pos[node.path]}
				{#if p}
					<div
						class="project-node"
						class:folder-node={node.type === 'folder'}
						class:selected={panelNode?.path === node.path}
						class:meta-active={metaNode === node.path}
						style="left: {p.x}px; top: {p.y - nodeRadius(node)}px;"
						onpointerdown={(e) => handlePointerDown(e, node)}
						oncontextmenu={(e) => handleContextMenu(e, node)}
						onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && openEditPanel(node)}
						role="button"
						tabindex="0"
					>
						<div class="node-circle" style="background: {statusInfo(node.status).color};">
							{#if node.type === 'folder'}<Folder size={16} strokeWidth={1.75} />{:else}<FileText size={16} strokeWidth={1.75} />{/if}
						</div>
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
				{/if}
			{/each}
		</div>
	</div>
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
				<span class="node-icon">{#if panelNode.type === 'folder'}<Folder size={16} strokeWidth={1.75} />{:else}<FileText size={16} strokeWidth={1.75} />{/if}</span>
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

	.canvas-wrapper {
		position: relative;
		width: 100%;
		height: calc(100vh - 200px);
		min-height: 480px;
		overflow: hidden;
		background: var(--bg-white);
		touch-action: none;
		cursor: move;
	}

	.canvas-wrapper .spinner {
		position: absolute;
		inset: 0;
		margin: auto;
	}

	/* 원점(0,0)이 시뮬레이션 중심, pan/zoom은 transform으로 */
	.canvas-content {
		position: absolute;
		top: 0;
		left: 0;
		width: 0;
		height: 0;
		transform-origin: 0 0;
	}

	.edges-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 1px;
		height: 1px;
		overflow: visible;
		pointer-events: none;
	}

	.project-node {
		position: absolute;
		width: max-content;
		max-width: 160px;
		transform: translateX(-50%);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
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
		transition:
			box-shadow 0.15s,
			transform 0.1s;
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

	.project-node.selected .node-circle {
		outline: 2px solid var(--accent);
		outline-offset: 2px;
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
		border-radius: var(--radius-md);
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
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-lg);
		padding: 4px;
	}

	.context-menu button {
		background: none;
		border: none;
		text-align: left;
		padding: 8px 10px;
		border-radius: var(--radius-md);
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
