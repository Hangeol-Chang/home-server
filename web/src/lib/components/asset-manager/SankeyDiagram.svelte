<script>
	import { CHART_COLORS } from '$lib/constants.js';
	import TransactionDropdown from './TransactionDropdown.svelte';
	import TransactionForm from './TransactionForm.svelte';

	let { transactions = [] } = $props();

	// Layout constants (SVG user units)
	const W = 800, H_MIN = 420, NW = 16, PY = 32;
	const X1 = 60, X2 = 310, X3 = 570;
	const CAT_GAP = 16, SUB_GAP = 10, SAVE_GAP = 22;
	const MIN_CAT_H = 28;
	const MIN_SUB_H = 22;

	// All spend categories with stable color assignment (for filter buttons)
	// All sub-categories included — no top-N limit
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
				// All subs sorted by value — no slice limit
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

	// Sankey layout — only enabled categories
	const data = $derived.by(() => {
		const cats = allCats.filter(c => !disabledCatIds.includes(c.id));

		const earnTxs = transactions.filter(t => t.class_name === 'earn');
		const incomeTotal = earnTxs.reduce((s, t) => s + t.cost, 0);
		const spendTotal = cats.reduce((s, c) => s + c.total, 0);

		if (spendTotal === 0) return null;

		const effIncome = incomeTotal > 0 ? incomeTotal : 3200000;
		const saveAmount = Math.max(effIncome - spendTotal, 0);
		const hasSavings = saveAmount > 0;

		// Proportional scale — based on reference value vs available height
		const catGapsH = Math.max(cats.length - 1, 0) * CAT_GAP;
		const gapOverhead = catGapsH + (hasSavings ? SAVE_GAP : 0);
		const refVal = Math.max(effIncome, spendTotal);
		const tentativeAH = H_MIN - 2 * PY;
		const scale = (tentativeAH - gapOverhead) / refVal;

		// Sub-cat heights: proportional with minimum enforcement
		// catHeight = sum of its sub-cat heights (no gaps) so flows match exactly
		const subHeightsByCat = cats.map(c =>
			c.subs.map(sb => Math.max(sb.val * scale, MIN_SUB_H))
		);

		// Category height = sum of outgoing flow heights (= sum of sub-cat heights)
		// For categories without sub-cats, use proportional height directly
		const catHeights = cats.map((c, i) => {
			const subHs = subHeightsByCat[i];
			if (!subHs.length) return Math.max(c.total * scale, MIN_CAT_H);
			return Math.max(subHs.reduce((s, h) => s + h, 0), MIN_CAT_H);
		});

		const saveH = hasSavings ? Math.max(saveAmount * scale, MIN_CAT_H) : 0;

		// Col-2 total height (nodes + gaps between them)
		const col2Total =
			catHeights.reduce((s, h) => s + h, 0) +
			catGapsH +
			(hasSavings ? saveH + SAVE_GAP : 0);

		// Income node height = total flow quantity (no gaps)
		const incomeH = catHeights.reduce((s, h) => s + h, 0) + saveH;

		// SVG expands if minimum heights push beyond H_MIN
		const svgH = Math.max(H_MIN, col2Total + 2 * PY);
		const dynamicAH = svgH - 2 * PY;

		// Income node — centered vertically against col-2
		const incomeNode = {
			y: PY + (dynamicAH - incomeH) / 2,
			h: incomeH,
			effVal: effIncome,
			hasReal: incomeTotal > 0
		};

		// Category nodes stacked from PY
		let col2Y = PY;
		const catNodes = cats.map((c, i) => {
			const h = catHeights[i];
			const node = { y: col2Y, h, label: c.name, val: c.total, color: c.color, catId: c.id };
			col2Y += h + (i < cats.length - 1 ? CAT_GAP : 0);
			return node;
		});

		// Savings node
		let saveNode = null;
		if (hasSavings) {
			col2Y += SAVE_GAP;
			saveNode = { y: col2Y, h: saveH, label: '저축', val: saveAmount, color: '#4ECDC4' };
		}

		// Sub-category nodes — centered on their parent category's midpoint
		// (may extend above/below the category rect; flows fan out via bezier)
		const subNodes = [];
		cats.forEach((c, ci) => {
			const cn = catNodes[ci];
			if (!c.subs.length) return;
			const subHs = subHeightsByCat[ci];
			// Visual span including gaps
			const totalVisualH = subHs.reduce((s, h) => s + h, 0) + (c.subs.length - 1) * SUB_GAP;
			// Center sub-cat column on category midpoint
			let sy = cn.y + cn.h / 2 - totalVisualH / 2;
			c.subs.forEach((sb, si) => {
				const sh = subHs[si];
				subNodes.push({
					y: sy, h: sh,
					label: sb.name, val: sb.val,
					color: cn.color,
					catId: c.id,
					subName: sb.name
				});
				sy += sh + SUB_GAP;
			});
		});

		// Flows: income → categories (packed at departure, fanning at arrival)
		const flows = [];
		let fy = incomeNode.y;
		catNodes.forEach(cn => {
			flows.push({ x1: X1 + NW, y1t: fy, y1b: fy + cn.h, x2: X2, y2t: cn.y, y2b: cn.y + cn.h, color: cn.color });
			fy += cn.h;
		});
		if (saveNode) {
			flows.push({
				x1: X1 + NW, y1t: fy, y1b: fy + saveNode.h,
				x2: X2, y2t: saveNode.y, y2b: saveNode.y + saveNode.h,
				color: saveNode.color
			});
		}

		// Flows: categories → sub-categories
		// Departure side: packed contiguously from cn.y (cn.h = sum of sub-cat heights)
		// Arrival side: each sub-cat node's actual position (with gaps)
		let si = 0;
		catNodes.forEach((cn, ci) => {
			if (!cats[ci].subs.length) return;
			let cfy = cn.y;
			cats[ci].subs.forEach(() => {
				const sn = subNodes[si++];
				flows.push({
					x1: X2 + NW, y1t: cfy, y1b: cfy + sn.h,
					x2: X3, y2t: sn.y, y2b: sn.y + sn.h,
					color: cn.color
				});
				cfy += sn.h;
			});
		});

		return { incomeNode, catNodes, saveNode, subNodes, flows, svgH };
	});

	// ── Hover / tooltip ──────────────────────────────────────────────────
	let hoveredNode = $state(null);
	let tipX = $state(0), tipY = $state(0);
	let clearTimer = null;

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

	function positionTip(e) {
		const TW = 252;
		let x = e.clientX + 14;
		let y = e.clientY - 24;
		if (typeof window !== 'undefined') {
			if (x + TW > window.innerWidth - 8) x = e.clientX - TW - 10;
			if (y + 280 > window.innerHeight - 8) y = window.innerHeight - 288;
			if (y < 8) y = 8;
		}
		tipX = x;
		tipY = y;
	}

	function enterNode(e, info) {
		clearTimeout(clearTimer);
		hoveredNode = { ...info, txs: getTxs(info) };
		positionTip(e);
	}

	function leaveNode() {
		clearTimer = setTimeout(() => { hoveredNode = null; }, 60);
	}

	function clickNode(info) {
		clearTimeout(clearTimer);
		hoveredNode = null;
		ddTitle = info.label + (info.type === 'save' ? ' 내역' : ' 지출 내역');
		ddTxs = getTxs(info);
		ddVisible = true;
	}

	function svgMouseMove(e) {
		if (hoveredNode) positionTip(e);
	}

	function bezier({ x1, y1t, y1b, x2, y2t, y2b }) {
		const mx = (x1 + x2) / 2;
		return `M${x1},${y1t}C${mx},${y1t},${mx},${y2t},${x2},${y2t}L${x2},${y2b}C${mx},${y2b},${mx},${y1b},${x1},${y1b}Z`;
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
		{#if !data}
			<div class="empty">
				{allCats.length > 0
					? '모든 카테고리가 숨겨진 상태입니다'
					: '이번 달 지출 내역이 없습니다'}
			</div>
		{:else}
			<svg
				viewBox="0 0 {W} {data.svgH}"
				class="sankey-svg"
				role="img"
				aria-label="수입/지출 흐름 다이어그램"
				onmousemove={svgMouseMove}
				onmouseleave={() => { clearTimeout(clearTimer); hoveredNode = null; }}
			>
				<!-- Flows -->
				{#each data.flows as f, i (i)}
					<path d={bezier(f)} fill={f.color} fill-opacity="0.22" />
				{/each}

				<!-- Income node -->
				<rect x={X1} y={data.incomeNode.y} width={NW} height={data.incomeNode.h} fill="#4caf50" rx="1" />
				<text x={X1 - 8} y={data.incomeNode.y + data.incomeNode.h / 2 - 8} text-anchor="end" class="nlbl">
					수입{#if !data.incomeNode.hasReal} *{/if}
				</text>
				<text x={X1 - 8} y={data.incomeNode.y + data.incomeNode.h / 2 + 8} text-anchor="end" class="nval">
					{fmt(data.incomeNode.effVal)}
				</text>

				<!-- Spend category nodes -->
				{#each data.catNodes as n (n.label)}
					{@const ni = { type: 'cat', label: n.label, val: n.val, catId: n.catId }}
					<g
						onmouseenter={(e) => enterNode(e, ni)}
						onmouseleave={leaveNode}
						onclick={() => clickNode(ni)}
						role="button"
						tabindex="0"
						onkeydown={(e) => e.key === 'Enter' && clickNode(ni)}
						style="cursor:pointer"
					>
						<rect x={X2 - 140} y={n.y - 3} width={140 + NW + 3} height={n.h + 6} fill="transparent" />
						<rect x={X2} y={n.y} width={NW} height={n.h} fill={n.color} rx="1" />
						<text x={X2 - 8} y={n.y + n.h / 2 - 7} text-anchor="end" class="nlbl">{n.label}</text>
						<text x={X2 - 8} y={n.y + n.h / 2 + 7} text-anchor="end" class="nval">{fmt(n.val)}</text>
					</g>
				{/each}

				<!-- Savings node -->
				{#if data.saveNode}
					{@const sn = data.saveNode}
					{@const ni = { type: 'save', label: sn.label, val: sn.val }}
					<g
						onmouseenter={(e) => enterNode(e, ni)}
						onmouseleave={leaveNode}
						onclick={() => clickNode(ni)}
						role="button"
						tabindex="0"
						onkeydown={(e) => e.key === 'Enter' && clickNode(ni)}
						style="cursor:pointer"
					>
						<rect x={X2 - 140} y={sn.y - 3} width={140 + NW + 3} height={sn.h + 6} fill="transparent" />
						<rect x={X2} y={sn.y} width={NW} height={sn.h} fill={sn.color} rx="1" />
						<text x={X2 - 8} y={sn.y + sn.h / 2 - 7} text-anchor="end" class="nlbl">{sn.label}</text>
						<text x={X2 - 8} y={sn.y + sn.h / 2 + 7} text-anchor="end" class="nval">{fmt(sn.val)}</text>
					</g>
				{/if}

				<!-- Sub-category nodes -->
				{#each data.subNodes as n, i (i)}
					{@const ni = { type: 'sub', label: n.label, val: n.val, catId: n.catId, subName: n.subName }}
					<g
						onmouseenter={(e) => enterNode(e, ni)}
						onmouseleave={leaveNode}
						onclick={() => clickNode(ni)}
						role="button"
						tabindex="0"
						onkeydown={(e) => e.key === 'Enter' && clickNode(ni)}
						style="cursor:pointer"
					>
						<rect x={X3 - 4} y={n.y - 3} width={NW + 178} height={n.h + 6} fill="transparent" />
						<rect x={X3} y={n.y} width={NW} height={n.h} fill={n.color} fill-opacity="0.8" rx="1" />
						<text x={X3 + NW + 8} y={n.y + n.h / 2 - 6} text-anchor="start" class="nlbl">{n.label}</text>
						<text x={X3 + NW + 8} y={n.y + n.h / 2 + 7} text-anchor="start" class="nval">{fmt(n.val)}</text>
					</g>
				{/each}
			</svg>
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

	/* ── Sankey SVG ─────────────────────────────────────────────── */
	.sankey-wrap {
		width: 100%;
		min-height: 180px;
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
	}

	.sankey-svg {
		width: 100%;
		min-width: 540px;
		height: auto;
	}

	.nlbl {
		font-size: 13px;
		fill: var(--text-primary);
		font-family: Pretendard, sans-serif;
		pointer-events: none;
	}

	.nval {
		font-size: 11px;
		fill: var(--text-secondary);
		font-family: Pretendard, sans-serif;
		pointer-events: none;
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
