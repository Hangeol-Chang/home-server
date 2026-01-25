<script>
	import { device } from '$lib/stores/device';

	let { 
		tierSegments = [], 
		circumference = 0, 
		spend = 0,
		circleRadius = 80,
		onTierClick = () => {}
	} = $props();

	let hoveredTier = $state(null);
	let tooltipPosition = $state({ x: 0, y: 0 });

	function formatCurrency(value) {
		return new Intl.NumberFormat('ko-KR').format(value) + '원';
	}

	function handleMouseEnter(event, tier) {
		hoveredTier = tier;
		updateTooltipPosition(event);
	}

	function handleMouseMove(event) {
		if (hoveredTier) {
			updateTooltipPosition(event);
		}
	}

	function handleMouseLeave() {
		hoveredTier = null;
	}

	function updateTooltipPosition(event) {
		tooltipPosition = {
			x: event.clientX,
			y: event.clientY
		};
	}
</script>

<div class="pie-chart-wrapper" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<svg class="circular-chart" viewBox="0 0 240 240">
		<!-- 배경 -->
		<circle class="circle-bg" cx="120" cy="120" r="{circleRadius}"/>
		
		<!-- 내부 원 (총 지출) - 100% -->
		<circle class="circle-inner" cx="120" cy="120" r="{circleRadius - 14}" 
			stroke-dasharray="{circumference} {0}"
		/>

		<!-- 외부 원 - 티어별 세그먼트 -->
		{#each tierSegments as tier}
		<circle class="circle-outer" cx="120" cy="120" r="{circleRadius}"
			stroke-dasharray="{tier.dash} {circumference}"
			transform="rotate({tier.rotation} 120 120)"
			stroke={tier.color}
			onmouseenter={(e) => handleMouseEnter(e, tier)}
			onmousemove={handleMouseMove}
			onmouseleave={handleMouseLeave}
			onclick={() => onTierClick(tier)}
			role="button"
			tabindex="0"
			onkeydown={(e) => e.key === 'Enter' && onTierClick(tier)}
			aria-label="{tier.display_name}"
		/>
		<!-- 라벨 텍스트 (3% 이상일 때만 표시) -->
		{#if parseFloat(tier.percent) > 3}
			<text x={tier.labelX} y={tier.labelY} class="chart-label" 
				  text-anchor="middle" dominant-baseline="middle"
				  fill={tier.color}>
				{tier.display_name}
			</text>
		{/if}
		{/each}

		<!-- 중앙 텍스트 -->
		<text x="120" y="115" class="chart-center-label">총 지출</text>
		<text x="120" y="130" class="chart-center-value">
			{formatCurrency(spend)}
		</text>
	</svg>

	<!-- 툴팁 -->
	{#if hoveredTier}
		<div class="chart-tooltip" style="top: {tooltipPosition.y}px; left: {tooltipPosition.x}px;">
			<div class="tooltip-header" style="border-bottom-color: {hoveredTier.color}">
				<span class="tooltip-title">{hoveredTier.display_name}</span>
				<span class="tooltip-total">{formatCurrency(hoveredTier.total)}</span>
			</div>
			<div class="tooltip-body">
				{#each hoveredTier.categoryList as cat}
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

	/* SVG 차트 */
	.circular-chart {
		max-width: 320px;
		width: 100%;
		margin: 0;
	}

	/* 원 배경 */
	.circle-bg {
		fill: var(--bg-secondary);
	}

	/* 내부 원 (총 지출) */
	.circle-inner {
		fill: none;
		stroke: var(--bg-tertiary); /* 은은한 배경색 */
		stroke-width: 30;
	}

	/* 외부 원 세그먼트 */
	.circle-outer {
		fill: none;
		stroke-width: 14;
		stroke-linecap: round;
		transition: all 0.3s ease;
		filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
		cursor: pointer;
	}

	.circle-outer:hover {
		stroke-width: 18;
		filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
	}

	.circle-outer:focus {
		outline: none;
	}

	/* 중앙 텍스트 */
	.chart-center-label {
		font-size: 10px;
		fill: var(--text-secondary);
		text-anchor: middle;
		font-weight: 400;
	}

	.chart-center-value {
		font-size: 11px;
		fill: var(--text-primary);
		text-anchor: middle;
		font-weight: 400;
	}

	.chart-label {
		font-size: 11px;
		font-weight: 300;
		pointer-events: none;
		text-shadow: 0 1px 2px var(--bg-primary);
	}

	/* 툴팁 스타일 */
	.chart-tooltip {
		position: fixed;
		z-index: 1000;
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		padding: 12px;
		box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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

			.chart-center-label {
				font-size: 9px;
			}

			.chart-center-value {
				font-size: 10px;
			}
		}

		&.mobile {
			.circular-chart {
				max-width: 200px;
			}

			.chart-center-label {
				font-size: 8px;
			}

			.chart-center-value {
				font-size: 9px;
			}
		}
	}
</style>