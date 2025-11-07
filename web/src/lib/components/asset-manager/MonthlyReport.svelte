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
			<div class="stats-table-container">
				<table class="stats-table">
					<tbody>
						<tr class="stat-row income">
							<td class="stat-label">
								<span class="stat-icon">💰</span>
								<span>수익</span>
								{#if chartData().usingDefault}
									<span class="stat-badge default">기본값</span>
								{/if}
							</td>
							<td class="stat-amount text-right">{formatCurrency(chartData().income)}</td>
							<td class="text-center">
								<span class="stat-percent base">100%</span>
							</td>
						</tr>
						
						<tr class="stat-row spend">
							<td class="stat-label">
								<span class="stat-icon">💸</span>
								<span>지출</span>
							</td>
							<td class="stat-amount text-right">{formatCurrency(chartData().spend)}</td>
							<td class="text-center">
								<span class="stat-percent spend">{chartData().spendPercent}%</span>
							</td>
						</tr>

						<tr class="stat-row save">
							<td class="stat-label">
								<span class="stat-icon">🏦</span>
								<span>저축</span>
							</td>
							<td class="stat-amount text-right">{formatCurrency(chartData().save)}</td>
							<td class="text-center">
								<span class="stat-percent save">{chartData().savePercent}%</span>
							</td>
						</tr>

						<tr class="stat-row balance {chartData().balance >= 0 ? 'positive' : 'negative'}">
							<td class="stat-label">
								<span class="stat-icon">{chartData().balance >= 0 ? '📈' : '📉'}</span>
								<span>잔액</span>
							</td>
							<td class="stat-amount text-right">{formatCurrency(Math.abs(chartData().balance))}</td>
							<td class="text-center">
								<span class="stat-percent balance">{chartData().balancePercent}%</span>
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
		font-size: 1.5rem;
		color: var(--text-primary);
	}

	.refresh-btn {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 6px;
		padding: 8px;
		cursor: pointer;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		color: var(--text-secondary);
	}

	.refresh-btn:hover:not(:disabled) {
		background: var(--bg-tertiary);
		transform: scale(1.1);
	}

	.refresh-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.spinning {
		animation: spin 1s linear infinite;
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

	/* 통계 테이블 */
	.stats-table-container {
		background: var(--bg-primary);
		border-radius: 8px;
		overflow: hidden;
		box-shadow: var(--shadow-md);
	}

	.stats-table {
		width: 100%;
		border-collapse: collapse;
	}

	.stats-table tbody tr {
		transition: all 0.2s;
		border-bottom: 1px solid var(--border-color);
	}

	.stats-table tbody tr:last-child {
		border-bottom: none;
	}

	.stats-table tbody tr:hover {
		background: var(--bg-secondary);
		transform: scale(1.01);
	}

	.stats-table td {
		padding: 16px;
	}

	.stat-label {
		align-items: center;
		gap: 10px;
		font-weight: 600;
		color: var(--text-primary);
	}

	.stat-icon {
		font-size: 1.4rem;
		display: inline-flex;
		align-items: center;
	}

	.stat-badge {
		font-size: 0.75rem;
		padding: 3px 8px;
		border-radius: 10px;
		font-weight: 600;
		margin-left: 8px;
	}

	.stat-badge.default {
		background: rgba(255, 152, 0, 0.15);
		color: #ff9800;
	}

	.stat-amount {
		font-size: 1.3rem;
		font-weight: 700;
		color: var(--text-primary);
		font-variant-numeric: tabular-nums;
	}

	.stat-percent {
		padding: 6px 12px;
		border-radius: 16px;
		font-weight: 700;
		font-size: 0.9rem;
		display: inline-block;
		min-width: 60px;
		text-align: center;

		background-color: var(--bg-secondary);
		width: 80px;
	}

	.text-right {
		text-align: right;
	}

	.text-center {
		text-align: center;
	}

	/* 행별 강조 색상 */
	.stat-row.income {
		background: linear-gradient(to right, rgba(46, 125, 50, 0.03), transparent);
	}

	.stat-row.spend {
		background: linear-gradient(to right, rgba(244, 67, 54, 0.03), transparent);
	}

	.stat-row.save {
		background: linear-gradient(to right, rgba(33, 150, 243, 0.03), transparent);
	}

	.stat-row.balance.positive {
		background: linear-gradient(to right, rgba(76, 175, 80, 0.05), transparent);
	}

	.stat-row.balance.negative {
		background: linear-gradient(to right, rgba(244, 67, 54, 0.05), transparent);
	}

	@media (max-width: 1024px) {
		.circular-chart {
			max-width: 300px;
		}

		.stats-table td {
			padding: 8px 4px;
		}
		.stat-amount {
			font-size: 1.2rem;
		}
		.stat-icon {
			font-size: 1.1rem;
		}
	}

	@media (max-width: 768px) {
		.circular-chart-container {
			grid-template-columns: 1fr;
		}


		.circular-chart {
			max-width: 250px;
		}

		.stats-table {
			font-size: 0.85rem;
		}

		.stats-table td {
			padding: 12px 8px;
		}

		.stat-amount {
			font-size: 1.1rem;
		}

		.stat-icon {
			font-size: 1.2rem;
		}

		.stat-percent {
			font-size: 0.8rem;
			padding: 4px 8px;
			min-width: 50px;
		}

		.stat-badge {
			font-size: 0.7rem;
			padding: 2px 6px;
		}
	}
</style>
