<script>
	import { getTransactions } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	let { year = new Date().getFullYear(), month = new Date().getMonth() + 1 } = $props();

	// 기본 수익 가정값 (수익이 0일 때 사용)
	let defaultIncome = $state(3200000);
	let transactions = $state([]);
	let loading = $state(true);
	let error = $state('');
    
    // Tooltip state
    let hoveredTier = $state(null);
    let tooltipPosition = $state({ x: 0, y: 0 });

	const circleRadius = 80; // 외부 원의 반지름
    const TIER_COLORS = [
        '#FF6B6B', // Red
        '#4ECDC4', // Teal
        '#45B7D1', // Blue
        '#FFA07A', // Light Salmon
        '#98D8C8', // Mint
        '#F7DC6F', // Yellow
        '#BB8FCE', // Purple
        '#F1948A', // Light Red
    ];

	onMount(async () => {
		await loadStatistics();
	});

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

	async function loadStatistics() {
		loading = true;
		error = '';
		try {
            // 해당 월의 시작일과 종료일 계산
            const startDate = new Date(year, month - 1, 1);
            const endDate = new Date(year, month, 0);
            
            const formatDate = (date) => {
                const y = date.getFullYear();
                const m = String(date.getMonth() + 1).padStart(2, '0');
                const d = String(date.getDate()).padStart(2, '0');
                return `${y}-${m}-${d}`;
            };

			transactions = await getTransactions({
                start_date: formatDate(startDate),
                end_date: formatDate(endDate),
                limit: 10000 // 충분히 큰 수
            });
		} catch (err) {
			error = '데이터를 불러오는 중 오류가 발생했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	function formatCurrency(value) {
		return new Intl.NumberFormat('ko-KR').format(value) + '원';
	}

	// 차트 데이터 계산
	const chartData = $derived(() => {
		if (!transactions) return null;

        let earn_total = 0;
        let spend_total = 0;
        let save_total = 0;
        const spendByTier = {};

        // 트랜잭션 집계
        transactions.forEach(tx => {
            const cost = tx.cost;
            if (tx.class_name === 'earn') {
                earn_total += cost;
            } else if (tx.class_name === 'spend') {
                spend_total += cost;
                
                // 티어별 집계
                const tierName = tx.tier_name;
                const tierDisplayName = tx.tier_display_name || tierName;
                const categoryName = tx.category_display_name || tx.category_name;
                
                if (!spendByTier[tierName]) {
                    spendByTier[tierName] = {
                        name: tierName,
                        display_name: tierDisplayName,
                        total: 0,
                        categories: {}
                    };
                }
                spendByTier[tierName].total += cost;

                if (!spendByTier[tierName].categories[categoryName]) {
                    spendByTier[tierName].categories[categoryName] = 0;
                }
                spendByTier[tierName].categories[categoryName] += cost;
            } else if (tx.class_name === 'save') {
                save_total += cost;
            }
        });

		const income = earn_total > 0 ? earn_total : defaultIncome;
		const spend = spend_total;
		const save = save_total;
		const balance = earn_total - spend_total - save_total;

		const spendPercent = (spend / income) * 100;
		const savePercent = (save / income) * 100;
		const balancePercent = (balance / income) * 100;

        // 티어 배열로 변환 및 정렬 (금액 내림차순)
        const tiers = Object.values(spendByTier).sort((a, b) => b.total - a.total);

		// SVG 원형 차트를 위한 각도 계산 (시작점은 -90도, 즉 12시 방향)
		const circumference = 2 * Math.PI * circleRadius; // 외부 원의 둘레 (반지름 80)
        const labelRadius = circleRadius * 1.3; // 라벨 위치 반지름
        const cx = 120;
        const cy = 120;
        
        let currentRotation = -90;
        
        const tierSegments = tiers.map((tier, index) => {
            const percent = spend > 0 ? (tier.total / spend) * 100 : 0;
            const angleSize = (percent / 100) * 360;
            const dash = (percent / 100) * circumference;
            const rotation = currentRotation;
            
            // 라벨 위치 계산 (세그먼트의 중간 각도)
            const midAngleDeg = rotation + (angleSize / 2);
            const midAngleRad = (midAngleDeg * Math.PI) / 180;
            
            const labelX = cx + labelRadius * Math.cos(midAngleRad);
            const labelY = cy + labelRadius * Math.sin(midAngleRad);

            // 카테고리 정렬 (금액 내림차순)
            const categoryList = Object.entries(tier.categories)
                .map(([name, value]) => ({ name, value }))
                .sort((a, b) => b.value - a.value);

            currentRotation += angleSize;
            
            return {
                ...tier,
                percent: percent.toFixed(1),
                dash,
                rotation,
                color: TIER_COLORS[index % TIER_COLORS.length],
                labelX,
                labelY,
                categoryList
            };
        });

		return {
			income,
			spend,
			save,
			balance,
			spendPercent: spendPercent.toFixed(1),
			savePercent: savePercent.toFixed(1),
			balancePercent: balancePercent.toFixed(1),
            tierSegments,
			circumference,
			usingDefault: earn_total === 0
		};
	});

	$effect(() => {
		loadStatistics();
	});
</script>

<div class="monthly-report">
	<div class="report-header">
		<h2>
			📊 {year}년 {month}월 지출 분석
		</h2>
		<button class="refresh-btn" onclick={loadStatistics} disabled={loading} aria-label="새로고침">
			<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class:spinning={loading}>
				<polyline points="23 4 23 10 17 10"></polyline>
				<polyline points="1 20 1 14 7 14"></polyline>
				<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
			</svg>
		</button>
	</div>

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>데이터를 불러오는 중...</p>
		</div>
	{:else if error}
		<div class="error">
			<p>⚠️ {error}</p>
			<button class="retry-btn" onclick={loadStatistics}>다시 시도</button>
		</div>
	{:else if transactions && chartData()}
		<!-- 동심원 차트 -->
		<div class="circular-chart-container">
			<svg class="circular-chart" viewBox="0 0 240 240">
				<!-- 배경 -->
				<circle class="circle-bg" cx="120" cy="120" r="{circleRadius}"/>
				
                <!-- 내부 원 (총 지출) - 100% -->
				<circle class="circle-inner" cx="120" cy="120" r="{circleRadius - 14}" 
					stroke-dasharray="{chartData().circumference} {0}"
				/>

				<!-- 외부 원 - 티어별 세그먼트 -->
                {#each chartData().tierSegments as tier}
				<circle class="circle-outer" cx="120" cy="120" r="{circleRadius}"
					stroke-dasharray="{tier.dash} {chartData().circumference}"
					transform="rotate({tier.rotation} 120 120)"
                    stroke={tier.color}
                    onmouseenter={(e) => handleMouseEnter(e, tier)}
                    onmousemove={handleMouseMove}
                    onmouseleave={handleMouseLeave}
                    role="graphics-symbol" 
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
					{formatCurrency(chartData().spend)}
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

			<!-- 범례 및 통계 테이블 -->
			<div class="table-container">
				<table class="data-table">
					<tbody>
						<tr class="row-earn">
							<td class="cell-label">
								<span class="cell-icon">💰</span>
								<span>수익</span>
								{#if chartData().usingDefault}
									<span class="cell-badge">기본값</span>
								{/if}
							</td>
							<td class="cell-amount text-right">{formatCurrency(chartData().income)}</td>
							<td class="text-center">
								<span class="cell-percent">100%</span>
							</td>
						</tr>
						
						<tr class="row-spend">
							<td class="cell-label">
								<span class="cell-icon">💸</span>
								<span>지출</span>
							</td>
							<td class="cell-amount text-right">{formatCurrency(chartData().spend)}</td>
							<td class="text-center">
								<span class="cell-percent spend">{chartData().spendPercent}%</span>
							</td>
						</tr>

						<tr class="row-save">
							<td class="cell-label">
								<span class="cell-icon">🏦</span>
								<span>저축</span>
							</td>
							<td class="cell-amount text-right">{formatCurrency(chartData().save)}</td>
							<td class="text-center">
								<span class="cell-percent save">{chartData().savePercent}%</span>
							</td>
						</tr>

						<tr class="{chartData().balance >= 0 ? 'row-positive' : 'row-negative'}">
							<td class="cell-label">
								<span class="cell-icon">{chartData().balance >= 0 ? '📈' : '📉'}</span>
								<span>잔액</span>
							</td>
							<td class="cell-amount text-right">{formatCurrency(Math.abs(chartData().balance))}</td>
							<td class="text-center">
								<span class="cell-percent balance">{chartData().balancePercent}%</span>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>
<style>
	.monthly-report {
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 12px;
		padding: 24px;
		margin-bottom: 32px;
	}

	.report-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 24px;
	}

	.report-header h2 {
		margin: 0;
		font-size: 1.4rem;
		color: var(--text-primary);
	}

	.refresh-btn {
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		padding: 8px;
		border-radius: 50%;
		transition: all 0.2s;
	}

	.refresh-btn:hover:not(:disabled) {
		background: var(--bg-secondary);
		color: var(--text-primary);
	}

	.refresh-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.spinning {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.loading, .error {
		text-align: center;
		padding: 40px 0;
		color: var(--text-secondary);
	}

	.spinner {
		width: 30px;
		height: 30px;
		border: 3px solid var(--bg-secondary);
		border-top-color: var(--primary-color);
		border-radius: 50%;
		margin: 0 auto 16px;
		animation: spin 1s linear infinite;
	}

	.retry-btn {
		margin-top: 12px;
		padding: 8px 16px;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 6px;
		cursor: pointer;
		color: var(--text-primary);
	}

	/* 동심원 차트 컨테이너 */
	.circular-chart-container {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 20px;
		align-items: center;
	}

	/* SVG 차트 */
	.circular-chart {
		max-width: 320px;
		width: 100%;
		margin: 0 auto;
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
        /* animation: drawCircle 1s ease-out backwards; */
        cursor: pointer;
	}

    .circle-outer:hover {
        stroke-width: 18;
        filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
    }

	@keyframes drawCircle {
		from {
			stroke-dasharray: 0 502;
		}
	}

	/* 중앙 텍스트 */
	.chart-center-label {
		font-size: 10px;
		fill: var(--text-secondary);
		text-anchor: middle;
		font-weight: 600;
	}

	.chart-center-value {
		font-size: 11px;
		fill: var(--text-primary);
		text-anchor: middle;
		font-weight: 700;
	}

    .chart-label {
        font-size: 11px;
        font-weight: 400;
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
        font-weight: 700;
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

    /* 테이블 스타일 */
    .table-container {
        width: 100%;
    }

    .data-table {
        width: 100%;
        border-collapse: collapse;
    }

    .data-table td {
        padding: 12px 8px;
        border-bottom: 1px solid var(--border-color);
        font-size: 0.95rem;
    }

    .data-table tr:last-child td {
        border-bottom: none;
    }

    .cell-label {
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--text-secondary);
    }

    .cell-icon {
        font-size: 1.2rem;
    }


    .cell-amount {
        font-weight: 600;
        color: var(--text-primary);
    }

    .cell-percent {
        font-size: 0.85rem;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 12px;
        background: var(--bg-secondary);
        color: var(--text-secondary);
    }

    .text-right { text-align: right; }
    .text-center { text-align: center; }

    /* 행별 강조 색상 - 전역 스타일 오버라이드 */
	.cell-percent.spend {
		background: rgba(244, 67, 54, 0.1);
		color: var(--text-danger);
	}

	.cell-percent.save {
		background: rgba(33, 150, 243, 0.1);
		color: var(--text-info);
	}

	.cell-percent.balance {
		background: var(--bg-tertiary);
		color: var(--text-secondary);
	}

	/* Tablet/Mobile (< 768px) */
	@media (max-width: 768px) {
		.monthly-report {
			padding: 16px;
		}

		.report-header {
			margin-bottom: 20px;
		}

		.report-header h2 {
			font-size: 1.2rem;
		}

		.circular-chart-container {
			grid-template-columns: 1fr;
			gap: 20px;
		}

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

	/* Mobile (< 320px) */
	@media (max-width: 320px) {
		.monthly-report {
			padding: 12px;
		}

		.report-header h2 {
			font-size: 1.1rem;
		}

		.circular-chart {
			max-width: 200px;
		}

		.chart-center-label {
			font-size: 8px;
		}

		.chart-center-value {
			font-size: 9px;
		}

		.refresh-btn {
			padding: 6px;
		}

		.refresh-btn svg {
			width: 16px;
			height: 16px;
		}
	}
</style>
