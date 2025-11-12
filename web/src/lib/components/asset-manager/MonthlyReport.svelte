<script>
	import { getMonthlyStatistics } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	let { year = new Date().getFullYear(), month = new Date().getMonth() + 1 } = $props();

	// 기본 수익 가정값 (수익이 0일 때 사용)
	let defaultIncome = $state(3200000);
	let stats = $state(null);
	let loading = $state(true);
	let error = $state('');

	const circleRadius = 80; // 외부 원의 반지름

	onMount(async () => {
		await loadStatistics();
	});

	async function loadStatistics() {
		loading = true;
		error = '';
		try {
			stats = await getMonthlyStatistics(year, month);
		} catch (err) {
			error = '통계를 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	function formatCurrency(value) {
		return new Intl.NumberFormat('ko-KR').format(value) + '원';
	}

	// 차트 데이터 계산
	const chartData = $derived(() => {
		if (!stats) return null;

		const income = stats.earn_total > 0 ? stats.earn_total : defaultIncome;
		const spend = stats.spend_total;
		const save = stats.save_total;
		const balance = stats.balance;

		const spendPercent = (spend / income) * 100;
		const savePercent = (save / income) * 100;
		const balancePercent = (balance / income) * 100;

		// SVG 원형 차트를 위한 각도 계산 (시작점은 -90도, 즉 12시 방향)
		const circumference = 2 * Math.PI * circleRadius; // 외부 원의 둘레 (반지름 80)
		const spendDash = (spendPercent / 100) * circumference;
		const saveDash = (savePercent / 100) * circumference;

		// 각 세그먼트의 시작 각도 (rotate 값)
		const spendRotation = -90;
		const saveRotation = -90 + (spendPercent * 360) / 100;

		return {
			income,
			spend,
			save,
			balance,
			spendPercent: spendPercent.toFixed(1),
			savePercent: savePercent.toFixed(1),
			balancePercent: balancePercent.toFixed(1),
			spendDash,
			saveDash,
			circumference,
			spendRotation,
			saveRotation,
			usingDefault: stats.earn_total === 0
		};
	});

	$effect(() => {
		loadStatistics();
	});
</script>

<div class="monthly-report">
	<div class="report-header">
		<h2>
			📊 {year}년 {month}월
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
	{:else if stats && chartData()}
		<!-- 동심원 차트 -->
		<div class="circular-chart-container">
			<svg class="circular-chart" viewBox="0 0 200 200">
				<!-- 배경 -->
				<circle class="circle-bg" cx="100" cy="100" r="{circleRadius}"/>
				<!-- 내부 원 (수익) - 채워진 부분 -->
				<circle class="circle-inner income" cx="100" cy="100" r="{circleRadius - 14}" 
					stroke-dasharray="{360} {0}"
				/>

				<!-- 외부 원 - 세그먼트 -->
				<circle class="circle-outer spend" cx="100" cy="100" r="{circleRadius}"
					stroke-dasharray="{chartData().spendDash} {chartData().circumference}"
					transform="rotate({chartData().spendRotation} 100 100)"
				/>
				<circle class="circle-outer save" cx="100" cy="100" r="{circleRadius}"
					stroke-dasharray="{chartData().saveDash} {chartData().circumference}"
					transform="rotate({chartData().saveRotation} 100 100)"
				/>

				<!-- 중앙 텍스트 -->
				<text x="100" y="95" class="chart-center-label">총 수익</text>
				<text x="100" y="110" class="chart-center-value">
					{formatCurrency(chartData().income)}
				</text>
			</svg>

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

	/* 동심원 차트 컨테이너 */
	.circular-chart-container {
		display: grid;
		grid-template-columns: 2fr 3fr;
		gap: 10px;
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

	/* 내부 원 (수익) */
	.circle-inner {
		fill: none;
		stroke: #9cffa6;
		/* shadow */
		filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
		stroke-width: 30;
		animation: drawCircle 1s ease-out 0.2s backwards;
	}

	/* 외부 원 세그먼트 */
	.circle-outer {
		fill: none;
		stroke-width: 14;
		stroke-linecap: round;
		transition: all 0.3s ease;
		filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
	}

	.circle-outer.spend {
		stroke: #fa746b;
		animation: drawCircle 1s ease-out 0.2s backwards;
	}

	.circle-outer.save {
		stroke: #54b2fe;
		animation: drawCircle 1s ease-out 0.4s backwards;
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

	/* 태블릿 */
	@media (max-width: 1024px) {
		.circular-chart {
			max-width: 280px;
		}

		.report-header h2 {
			font-size: 1.3rem;
		}
	}

	/* 모바일 */
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
			max-width: 240px;
		}

		.chart-center-label {
			font-size: 9px;
		}

		.chart-center-value {
			font-size: 10px;
		}
	}

	/* 모바일 소형 */
	@media (max-width: 480px) {
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
