<script>
	import { Chart, registerables } from 'chart.js';
	import { SankeyController, Flow } from 'chartjs-chart-sankey';
	import { CHART_COLORS } from '$lib/constants.js';
	import TransactionDropdown from './TransactionDropdown.svelte';
	import TransactionForm from './TransactionForm.svelte';

	Chart.register(...registerables, SankeyController, Flow);

	let { transactions = [] } = $props();

	const SAVE_COLOR = '#4ECDC4';

	// All spend categories with stable color assignment (for filter buttons)
	const allCats = $derived.by(() => {
		const catObj = /** @type {Record<string,{id:number,name:string,total:number,subs:Record<string,number>}>} */ ({});
		transactions.filter(t => t.class_name === 'spend').forEach(t => {
			const key = String(t.category_id);
			if (!catObj[key]) {
				catObj[key] = {
					id: t.category_id,
					name: t.category_display_name || t.category_name || '기타',
					total: 0,
					subs: {}
				};
			}
			catObj[key].total += t.cost;
			const sn = t.sub_category_name || '미분류';
			catObj[key].subs[sn] = (catObj[key].subs[sn] || 0) + t.cost;
		});

		return Object.values(catObj)
			.sort((a, b) => b.total - a.total)
			.map((c, i) => ({
				id: c.id,
				name: c.name,
				total: c.total,
				color: CHART_COLORS[i % CHART_COLORS.length],
				subs: Object.entries(c.subs)
					.map(([name, val]) => ({ name, val }))
					.sort((a, b) => b.val - a.val)
			}));
	});

	// Which category IDs are toggled off
	let disabledCatIds = $state(/** @type {number[]} */ ([]));

	function toggleCat(catId) {
		if (disabledCatIds.includes(catId)) {
			disabledCatIds = disabledCatIds.filter(id => id !== catId);
		} else {
			disabledCatIds = [...disabledCatIds, catId];
		}
	}

	function catKey(catId) {
		return `cat:${catId}`;
	}
	function subKey(catId, subName) {
		return `sub:${catId}:${subName}`;
	}

	// Sankey flow data — only enabled categories
	const flowData = $derived.by(() => {
		const cats = allCats.filter(c => !disabledCatIds.includes(c.id));

		const earnTxs = transactions.filter(t => t.class_name === 'earn');
		const incomeTotal = earnTxs.reduce((s, t) => s + t.cost, 0);
		const spendTotal = cats.reduce((s, c) => s + c.total, 0);

		if (spendTotal === 0) return null;

		const effIncome = incomeTotal > 0 ? incomeTotal : 3200000;
		const saveAmount = Math.max(effIncome - spendTotal, 0);
		const hasSavings = saveAmount > 0;

		const flows = [];
		const labels = {};
		const colors = {};
		const priority = {};
		let subCount = 0;

		labels['income'] = `수입${incomeTotal > 0 ? '' : ' *'}\n${fmt(effIncome)}`;

		cats.forEach((c, i) => {
			const ck = catKey(c.id);
			flows.push({ from: 'income', to: ck, flow: c.total });
			labels[ck] = `${c.name}\n${fmt(c.total)}`;
			colors[ck] = c.color;
			priority[ck] = i;

			c.subs.forEach((sb) => {
				const sk = subKey(c.id, sb.name);
				flows.push({ from: ck, to: sk, flow: sb.val });
				labels[sk] = `${sb.name}\n${fmt(sb.val)}`;
				colors[sk] = c.color;
				priority[sk] = subCount++;
			});
		});

		if (hasSavings) {
			flows.push({ from: 'income', to: 'save', flow: saveAmount });
			labels['save'] = `저축\n${fmt(saveAmount)}`;
			colors['save'] = SAVE_COLOR;
			priority['save'] = cats.length;
		}

		return { flows, labels, colors, priority, subCount, catCount: cats.length };
	});

	// ── Chart instance ──────────────────────────────────────────────────
	let canvasEl = $state(null);
	let chartInstance = null;

	function nodeColor(key) {
		return flowData?.colors[key] || '#999';
	}

	function updateChart() {
		if (!canvasEl) return;

		if (chartInstance) {
			chartInstance.destroy();
			chartInstance = null;
		}

		if (!flowData) return;

		const style = getComputedStyle(canvasEl);
		const textColor = style.getPropertyValue('--text-primary').trim() || '#222';

		chartInstance = new Chart(canvasEl.getContext('2d'), {
			type: 'sankey',
			data: {
				datasets: [
					{
						data: flowData.flows,
						labels: flowData.labels,
						priority: flowData.priority,
						colorFrom: (c) => nodeColor(c.dataset.data[c.dataIndex].to),
						colorTo: (c) => nodeColor(c.dataset.data[c.dataIndex].to),
						alpha: 0.22,
						colorMode: 'to',
						nodeWidth: 14,
						nodePadding: 24,
						size: 'max',
						font: { family: 'Pretendard, sans-serif', size: 12 },
						nodeLabels: {
							color: textColor,
							position: 'auto'
						}
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				interaction: { mode: 'nearest', intersect: false },
				scales: {
					x: { display: false },
					y: { display: false }
				},
				plugins: {
					legend: { display: false },
					tooltip: { enabled: false }
				},
				onHover: (event, elements) => {
					canvasEl.style.cursor = elements.length ? 'pointer' : 'default';
					if (!elements.length) {
						hoveredNode = null;
						return;
					}
					const info = pickNodeInfo(elements[0], event);
					if (!info) {
						hoveredNode = null;
						return;
					}
					clearTimeout(clearTimer);
					hoveredNode = { ...info, txs: getTxs(info) };
					tipX = event.native.clientX + 14;
					tipY = event.native.clientY - 24;
					clampTip();
				},
				onClick: (event, elements) => {
					if (!elements.length) return;
					const info = pickNodeInfo(elements[0], event);
					if (!info) return;
					clickNode(info);
				}
			}
		});
	}

	$effect(() => {
		flowData;
		updateChart();
	});

	$effect(() => {
		return () => {
			if (chartInstance) chartInstance.destroy();
		};
	});

	// ── Resolve which node (from/to) a flow click/hover refers to ────────
	function parseKey(key) {
		if (key === 'income') return null; // income node has no drilldown, as before
		if (key === 'save') return { type: 'save', label: '저축', val: flowData.flows.find(f => f.to === 'save')?.flow ?? 0 };
		if (key.startsWith('sub:')) {
			const rest = key.slice(4);
			const idx = rest.indexOf(':');
			const catId = Number(rest.slice(0, idx));
			const subName = rest.slice(idx + 1);
			const f = flowData.flows.find(fl => fl.to === key);
			return { type: 'sub', catId, subName, label: subName, val: f?.flow ?? 0 };
		}
		if (key.startsWith('cat:')) {
			const catId = Number(key.slice(4));
			const cat = allCats.find(c => c.id === catId);
			return { type: 'cat', catId, label: cat?.name ?? '', val: cat?.total ?? 0 };
		}
		return null;
	}

	function pickNodeInfo(element, event) {
		const raw = element.element;
		const { x, x2 } = raw.getProps(['x', 'x2'], true);
		const mid = (x + x2) / 2;
		const dataPoint = flowData.flows[element.index];
		const key = event.x < mid ? dataPoint.from : dataPoint.to;
		return parseKey(key);
	}

	// ── Hover / tooltip ──────────────────────────────────────────────────
	let hoveredNode = $state(null);
	let tipX = $state(0), tipY = $state(0);
	let clearTimer = null;

	function clampTip() {
		const TW = 252;
		if (typeof window === 'undefined') return;
		if (tipX + TW > window.innerWidth - 8) tipX = tipX - TW - 28;
		if (tipY + 280 > window.innerHeight - 8) tipY = window.innerHeight - 288;
		if (tipY < 8) tipY = 8;
	}

	// ── Dropdown / form ──────────────────────────────────────────────────
	let ddVisible = $state(false);
	let ddTitle = $state('');
	let ddTxs = $state([]);
	let formOpen = $state(false);
	let editTx = $state(null);

	function getTxs(info) {
		if (info.type === 'cat') {
			return transactions
				.filter(t => t.class_name === 'spend' && t.category_id === info.catId)
				.sort((a, b) => b.cost - a.cost);
		}
		if (info.type === 'sub') {
			return transactions
				.filter(t =>
					t.class_name === 'spend' &&
					t.category_id === info.catId &&
					(t.sub_category_name || '미분류') === info.subName
				)
				.sort((a, b) => b.cost - a.cost);
		}
		if (info.type === 'save') {
			return transactions.filter(t => t.class_name === 'save').sort((a, b) => b.cost - a.cost);
		}
		return [];
	}

	function clickNode(info) {
		clearTimeout(clearTimer);
		hoveredNode = null;
		ddTitle = info.label + (info.type === 'save' ? ' 내역' : ' 지출 내역');
		ddTxs = getTxs(info);
		ddVisible = true;
	}

	function fmt(v) {
		if (!v) return '0';
		if (v >= 100000000) return (v / 100000000).toFixed(1) + '억';
		if (v >= 10000000) return (v / 10000000).toFixed(1) + '천만';
		if (v >= 1000000) return (v / 1000000).toFixed(1) + 'M';
		if (v >= 10000) return (v / 10000).toFixed(0) + '만';
		return Math.round(v).toLocaleString();
	}

	function fmtFull(v) {
		return new Intl.NumberFormat('ko-KR').format(Math.round(v)) + '원';
	}

	const chartHeight = $derived(
		flowData ? Math.max(420, flowData.subCount * 40 + flowData.catCount * 30 + 160) : 180
	);
</script>

<!-- Tooltip -->
{#if hoveredNode}
	<div class="s-tip" style="top:{tipY}px;left:{tipX}px">
		<div class="st-hdr">
			<span>{hoveredNode.label}</span>
			<span>{fmtFull(hoveredNode.val)}</span>
		</div>
		{#if hoveredNode.txs.length === 0}
			<div class="st-empty">거래 내역 없음</div>
		{:else}
			{#each hoveredNode.txs.slice(0, 8) as tx (tx.id)}
				<div class="st-row">
					<span class="st-date">{String(tx.date).slice(5)}</span>
					<span class="st-name">{tx.name}</span>
					<span class="st-amt">{fmt(tx.cost)}</span>
				</div>
			{/each}
			{#if hoveredNode.txs.length > 8}
				<div class="st-more">+{hoveredNode.txs.length - 8}건 더 · 클릭해서 보기</div>
			{/if}
		{/if}
	</div>
{/if}

<div class="sankey-root">
	<!-- Category filter buttons -->
	{#if allCats.length > 0}
		<div class="cat-filters">
			{#each allCats as cat (cat.id)}
				{@const isOff = disabledCatIds.includes(cat.id)}
				<button
					class="cat-btn"
					class:off={isOff}
					style="--cc: {cat.color}"
					onclick={() => toggleCat(cat.id)}
					title={isOff ? `${cat.name} 켜기` : `${cat.name} 끄기`}
				>
					<span class="cat-dot"></span>
					{cat.name}
				</button>
			{/each}
		</div>
	{/if}

	<div class="sankey-wrap">
		{#if !flowData}
			<div class="empty">
				{allCats.length > 0
					? '모든 카테고리가 숨겨진 상태입니다'
					: '이번 달 지출 내역이 없습니다'}
			</div>
		{:else}
			<div class="sankey-canvas-wrap" style="height: {chartHeight}px">
				<canvas
					bind:this={canvasEl}
					role="img"
					aria-label="수입/지출 흐름 다이어그램"
				></canvas>
			</div>
		{/if}
	</div>
</div>

<TransactionDropdown
	bind:visible={ddVisible}
	mode="list"
	title={ddTitle}
	transactions={ddTxs}
	onEditTransaction={(tx) => { editTx = tx; formOpen = true; ddVisible = false; }}
/>

{#if formOpen}
	<TransactionForm
		bind:isOpen={formOpen}
		initialTransaction={editTx}
		onSuccess={() => { formOpen = false; }}
	/>
{/if}

<style>
	.sankey-root {
		width: 100%;
	}

	/* ── Category filter buttons ────────────────────────────────── */
	.cat-filters {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-bottom: 14px;
	}

	.cat-btn {
		display: flex;
		align-items: center;
		gap: 5px;
		padding: 4px 10px;
		border-radius: 20px;
		border: 1.5px solid var(--cc);
		background: transparent;
		color: var(--text-primary);
		font-size: 0.8rem;
		cursor: pointer;
		transition:
			background 0.15s,
			border-color 0.15s,
			opacity 0.15s;
		font-family: Pretendard, sans-serif;
		line-height: 1.4;
	}

	.cat-btn:hover:not(.off) {
		background: color-mix(in srgb, var(--cc) 16%, transparent);
	}

	.cat-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--cc);
		flex-shrink: 0;
		transition: background 0.15s;
	}

	.cat-btn.off {
		border-color: var(--border-color);
		color: var(--text-secondary);
		opacity: 0.5;
	}

	.cat-btn.off .cat-dot {
		background: var(--border-color);
	}

	/* ── Sankey chart ───────────────────────────────────────────── */
	.sankey-wrap {
		width: 100%;
		min-height: 180px;
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
	}

	.sankey-canvas-wrap {
		width: 100%;
		min-width: 540px;
		position: relative;
	}

	.empty {
		width: 100%;
		height: 180px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-secondary);
		font-size: 0.9rem;
	}

	/* ── Hover tooltip ──────────────────────────────────────────── */
	.s-tip {
		position: fixed;
		z-index: 1000;
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		padding: 10px 12px;
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
		pointer-events: none;
		min-width: 220px;
		max-width: 252px;
	}

	.st-hdr {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		font-size: 0.85rem;
		font-weight: 500;
		color: var(--text-primary);
		padding-bottom: 7px;
		margin-bottom: 6px;
		border-bottom: 1px solid var(--border-color);
	}

	.st-row {
		display: grid;
		grid-template-columns: 36px 1fr auto;
		gap: 5px;
		font-size: 0.78rem;
		padding: 2px 0;
		align-items: center;
	}

	.st-date { color: var(--text-secondary); white-space: nowrap; }
	.st-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-primary); }
	.st-amt { text-align: right; white-space: nowrap; color: var(--text-primary); font-variant-numeric: tabular-nums; }

	.st-empty {
		font-size: 0.8rem;
		color: var(--text-secondary);
		text-align: center;
		padding: 4px 0;
	}

	.st-more {
		font-size: 0.75rem;
		color: var(--text-secondary);
		text-align: center;
		padding-top: 5px;
		margin-top: 3px;
		border-top: 1px solid var(--border-color);
	}
</style>
