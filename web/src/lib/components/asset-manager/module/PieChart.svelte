<script>
	import { Chart, registerables } from 'chart.js';
	import { device } from '$lib/stores/device';

	Chart.register(...registerables);

	let {
		tierSegments = [],
		spend = 0,
		circleRadius = 80,
		onTierClick = () => {}
	} = $props();

	let canvasEl = $state(null);
	let chartInstance = null;

	let hoveredTier = $state(null);
	let tooltipPosition = $state({ x: 0, y: 0 });

	function formatCurrency(value) {
		return new Intl.NumberFormat('ko-KR').format(value) + '원';
	}

	function cssVar(canvas, name, fallback) {
		return getComputedStyle(canvas).getPropertyValue(name).trim() || fallback;
	}

	// Static background disc + "total" track ring, drawn under the tier arcs.
	function drawBackground(chart) {
		const arc0 = chart.getDatasetMeta(0).data[0];
		if (!arc0) return;
		const { x: cx, y: cy, outerRadius } = arc0.getProps(['x', 'y', 'outerRadius'], true);
		const pxPerUnit = outerRadius / (circleRadius + 7);
		const ctx = chart.ctx;

		ctx.save();

		ctx.beginPath();
		ctx.arc(cx, cy, pxPerUnit * circleRadius, 0, Math.PI * 2);
		ctx.fillStyle = cssVar(chart.canvas, '--bg-secondary', '#f5f5f5');
		ctx.fill();

		const trackOuter = pxPerUnit * (circleRadius + 1);
		const trackInner = pxPerUnit * (circleRadius - 29);
		ctx.beginPath();
		ctx.arc(cx, cy, (trackOuter + trackInner) / 2, 0, Math.PI * 2);
		ctx.lineWidth = trackOuter - trackInner;
		ctx.strokeStyle = cssVar(chart.canvas, '--bg-tertiary', '#e0e0e0');
		ctx.stroke();

		ctx.restore();
	}

	// Segment labels + center text, drawn over the tier arcs.
	function drawForeground(chart) {
		const arc0 = chart.getDatasetMeta(0).data[0];
		if (!arc0) return;
		const { x: cx, y: cy, outerRadius } = arc0.getProps(['x', 'y', 'outerRadius'], true);
		const pxPerUnit = outerRadius / (circleRadius + 7);
		const ctx = chart.ctx;

		ctx.save();
		ctx.textAlign = 'center';
		ctx.textBaseline = 'middle';

		ctx.font = `300 ${11 * pxPerUnit}px Pretendard, sans-serif`;
		tierSegments.forEach((tier) => {
			if (parseFloat(tier.percent) <= 3) return;
			const lx = cx + (tier.labelX - 120) * pxPerUnit;
			const ly = cy + (tier.labelY - 120) * pxPerUnit;
			ctx.fillStyle = tier.color;
			ctx.fillText(tier.display_name, lx, ly);
		});

		ctx.fillStyle = cssVar(chart.canvas, '--text-secondary', '#666');
		ctx.font = `400 ${10 * pxPerUnit}px Pretendard, sans-serif`;
		ctx.fillText('총 지출', cx, cy - 8 * pxPerUnit);

		ctx.fillStyle = cssVar(chart.canvas, '--text-primary', '#222');
		ctx.font = `400 ${11 * pxPerUnit}px Pretendard, sans-serif`;
		ctx.fillText(formatCurrency(spend), cx, cy + 7 * pxPerUnit);

		ctx.restore();
	}

	function updateChart() {
		if (!canvasEl) return;

		if (chartInstance) {
			chartInstance.destroy();
			chartInstance = null;
		}

		const radiusPct = ((circleRadius + 7) / 120) * 100;
		const cutoutPct = ((circleRadius - 7) / (circleRadius + 7)) * 100;

		chartInstance = new Chart(canvasEl.getContext('2d'), {
			type: 'doughnut',
			data: {
				labels: tierSegments.map((t) => t.display_name),
				datasets: [
					{
						data: tierSegments.map((t) => t.total),
						backgroundColor: tierSegments.map((t) => t.color),
						borderWidth: 0,
						borderRadius: 6,
						spacing: 2,
						hoverOffset: 6
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: true,
				aspectRatio: 1,
				rotation: 0,
				radius: `${radiusPct}%`,
				cutout: `${cutoutPct}%`,
				interaction: { mode: 'nearest', intersect: true },
				plugins: {
					legend: { display: false },
					tooltip: { enabled: false }
				},
				onHover: (event, elements) => {
					canvasEl.style.cursor = elements.length ? 'pointer' : 'default';
					if (elements.length) {
						hoveredTier = tierSegments[elements[0].index];
						tooltipPosition = { x: event.native.clientX, y: event.native.clientY };
					} else {
						hoveredTier = null;
					}
				},
				onClick: (event, elements) => {
					if (elements.length) onTierClick(tierSegments[elements[0].index]);
				}
			},
			plugins: [
				{
					id: 'pieChartExtras',
					beforeDatasetsDraw: drawBackground,
					afterDatasetsDraw: drawForeground
				}
			]
		});
	}

	$effect(() => {
		// track dependencies explicitly so re-renders happen on data change
		tierSegments;
		spend;
		circleRadius;
		updateChart();
	});

	$effect(() => {
		return () => {
			if (chartInstance) chartInstance.destroy();
		};
	});
</script>

<div class="pie-chart-wrapper" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<div class="circular-chart">
		<canvas bind:this={canvasEl}></canvas>
	</div>

	<!-- 툴팁 -->
	{#if hoveredTier}
		<div class="chart-tooltip" style="top: {tooltipPosition.y}px; left: {tooltipPosition.x}px;">
			<div class="tooltip-header" style="border-bottom-color: {hoveredTier.color}">
				<span class="tooltip-title">{hoveredTier.display_name}</span>
				<span class="tooltip-total">{formatCurrency(hoveredTier.total)}</span>
			</div>
			<div class="tooltip-body">
				{#each hoveredTier.categoryList as cat (cat.name)}
					<div class="tooltip-row">
						<span>{cat.name}</span>
						<span>{formatCurrency(cat.value)}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	/* 동심원 차트 컨테이너 */
	.pie-chart-wrapper {
		display: flex;
		justify-content: center;
		align-items: center;
		width: 100%;
	}

	.circular-chart {
		max-width: 320px;
		width: 100%;
		margin: 0;
	}

	/* 툴팁 스타일 */
	.chart-tooltip {
		position: fixed;
		z-index: 1000;
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		padding: 12px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		pointer-events: none;
		transform: translate(15px, 15px);
		min-width: 180px;
	}

	.tooltip-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-bottom: 8px;
		margin-bottom: 8px;
		border-bottom: 2px solid;
		font-weight: 400;
	}

	.tooltip-title {
		color: var(--text-primary);
	}

	.tooltip-total {
		color: var(--text-primary);
	}

	.tooltip-body {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.tooltip-row {
		display: flex;
		justify-content: space-between;
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	/* Tablet/Mobile (< 768px) */
	.pie-chart-wrapper {
		&.tablet {
			.circular-chart {
				max-width: 70%;
			}
		}

		&.mobile {
			.circular-chart {
				max-width: 200px;
			}
		}
	}
</style>
