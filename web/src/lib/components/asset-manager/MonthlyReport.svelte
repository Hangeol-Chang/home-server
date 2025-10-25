<script>
	import { getMonthlyStatistics } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	let { year = new Date().getFullYear(), month = new Date().getMonth() + 1 } = $props();

	let stats = $state(null);
	let loading = $state(true);
	let error = $state('');

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

	function getBalanceStatus(balance) {
		if (balance > 0) return { label: '흑자', color: '#4caf50', icon: '📈' };
		if (balance < 0) return { label: '적자', color: '#f44336', icon: '📉' };
		return { label: '수지균형', color: '#ff9800', icon: '⚖️' };
	}

	$effect(() => {
		loadStatistics();
	});
</script>

<div class="monthly-report">
	<div class="report-header">
		<h2>
			📊 {year}년 {month}월 재무 리포트
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
	{:else if stats}
		<div class="stats-grid">
			<!-- 수익 카드 -->
			<div class="stat-card income">
				<div class="stat-icon">💰</div>
				<div class="stat-content">
					<h3 class="stat-label">총 수익</h3>
					<p class="stat-value">{formatCurrency(stats.earn_total)}</p>
				</div>
			</div>

			<!-- 지출 카드 -->
			<div class="stat-card expense">
				<div class="stat-icon">💸</div>
				<div class="stat-content">
					<h3 class="stat-label">총 지출</h3>
					<p class="stat-value">{formatCurrency(stats.spend_total)}</p>
				</div>
			</div>

			<!-- 저축 카드 -->
			<div class="stat-card save">
				<div class="stat-icon">🏦</div>
				<div class="stat-content">
					<h3 class="stat-label">총 저축</h3>
					<p class="stat-value">{formatCurrency(stats.save_total)}</p>
				</div>
			</div>

			<!-- 잔액 카드 -->
			<div class="stat-card balance" style="--balance-color: {getBalanceStatus(stats.balance).color}">
				<div class="stat-icon">{getBalanceStatus(stats.balance).icon}</div>
				<div class="stat-content">
					<h3 class="stat-label">
						잔액 ({getBalanceStatus(stats.balance).label})
					</h3>
					<p class="stat-value">{formatCurrency(Math.abs(stats.balance))}</p>
				</div>
			</div>
		</div>

		<!-- 간단한 차트 (비율) -->
		<div class="budget-chart">
			<h3>지출 구성</h3>
			<div class="chart-bar">
				{#if stats.earn_total > 0}
					<div 
						class="bar-segment spend" 
						style="width: {(stats.spend_total / stats.earn_total * 100).toFixed(1)}%"
						title="지출: {(stats.spend_total / stats.earn_total * 100).toFixed(1)}%"
					>
						{#if (stats.spend_total / stats.earn_total * 100) > 10}
							<span class="bar-label">{(stats.spend_total / stats.earn_total * 100).toFixed(1)}%</span>
						{/if}
					</div>
					<div 
						class="bar-segment save" 
						style="width: {(stats.save_total / stats.earn_total * 100).toFixed(1)}%"
						title="저축: {(stats.save_total / stats.earn_total * 100).toFixed(1)}%"
					>
						{#if (stats.save_total / stats.earn_total * 100) > 10}
							<span class="bar-label">{(stats.save_total / stats.earn_total * 100).toFixed(1)}%</span>
						{/if}
					</div>
					<div 
						class="bar-segment balance" 
						style="width: {(stats.balance / stats.earn_total * 100).toFixed(1)}%"
						title="잔액: {(stats.balance / stats.earn_total * 100).toFixed(1)}%"
					>
						{#if (stats.balance / stats.earn_total * 100) > 10}
							<span class="bar-label">{(stats.balance / stats.earn_total * 100).toFixed(1)}%</span>
						{/if}
					</div>
				{:else}
					<p class="no-data">수익 데이터가 없습니다</p>
				{/if}
			</div>
			<div class="chart-legend">
				<div class="legend-item">
					<span class="legend-color spend"></span>
					<span>지출</span>
				</div>
				<div class="legend-item">
					<span class="legend-color save"></span>
					<span>저축</span>
				</div>
				<div class="legend-item">
					<span class="legend-color balance"></span>
					<span>잔액</span>
				</div>
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
		display: flex;
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

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.loading,
	.error {
		text-align: center;
		padding: 40px 20px;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid var(--border-color);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 16px;
	}

	.error p {
		color: #f44336;
		margin-bottom: 16px;
	}

	.retry-btn {
		padding: 10px 20px;
		background: var(--accent);
		color: white;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 600;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 16px;
		margin-bottom: 32px;
	}

	.stat-card {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 10px;
		padding: 20px;
		display: flex;
		align-items: center;
		gap: 16px;
		transition: all 0.2s;
	}

	.stat-card:hover {
		transform: translateY(-4px);
		box-shadow: var(--shadow-md);
	}

	.stat-card.income {
		border-left: 4px solid #4caf50;
	}

	.stat-card.expense {
		border-left: 4px solid #f44336;
	}

	.stat-card.save {
		border-left: 4px solid #2196f3;
	}

	.stat-card.balance {
		border-left: 4px solid var(--balance-color);
	}

	.stat-icon {
		font-size: 2.5rem;
		flex-shrink: 0;
	}

	.stat-content {
		flex: 1;
	}

	.stat-label {
		margin: 0 0 8px 0;
		font-size: 0.9rem;
		color: var(--text-secondary);
		font-weight: 600;
	}

	.stat-value {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--text-primary);
	}

	.budget-chart {
		background: var(--bg-secondary);
		border-radius: 10px;
		padding: 20px;
	}

	.budget-chart h3 {
		margin: 0 0 16px 0;
		font-size: 1.1rem;
		color: var(--text-primary);
	}

	.chart-bar {
		display: flex;
		height: 40px;
		border-radius: 8px;
		overflow: hidden;
		margin-bottom: 16px;
		background: var(--bg-primary);
	}

	.bar-segment {
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s;
		position: relative;
	}

	.bar-segment.spend {
		background: #f44336;
	}

	.bar-segment.save {
		background: #2196f3;
	}

	.bar-segment.balance {
		background: #4caf50;
	}

	.bar-label {
		color: white;
		font-weight: 600;
		font-size: 0.85rem;
	}

	.no-data {
		margin: 0;
		text-align: center;
		color: var(--text-tertiary);
		padding: 10px;
	}

	.chart-legend {
		display: flex;
		justify-content: center;
		gap: 24px;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.legend-color {
		width: 16px;
		height: 16px;
		border-radius: 4px;
	}

	.legend-color.spend {
		background: #f44336;
	}

	.legend-color.save {
		background: #2196f3;
	}

	.legend-color.balance {
		background: #4caf50;
	}

	@media (max-width: 768px) {
		.stats-grid {
			grid-template-columns: 1fr;
		}

		.stat-card {
			padding: 16px;
		}

		.stat-icon {
			font-size: 2rem;
		}

		.stat-value {
			font-size: 1.3rem;
		}

		.chart-legend {
			flex-wrap: wrap;
			gap: 12px;
		}
	}
</style>
