<script>
	import { getMonthlyStatistics } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	let { year = new Date().getFullYear(), month = new Date().getMonth() + 1 } = $props();

	// 기본 수익 가정값 (수익이 0일 때 사용)
	let defaultIncome = $state(3200000);
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
		const circumference = 2 * Math.PI * 80; // 외부 원의 둘레 (반지름 80)
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
	{:else if stats && chartData()}
		<!-- 기본 수익 설정 (수익이 없을 때만 표시) -->
		{#if chartData().usingDefault}
			<div class="default-income-notice">
				<p>
					ℹ️ 이번 달 수익이 등록되지 않아 기본값({formatCurrency(defaultIncome)})을 사용하고 있습니다.
				</p>
				<div class="income-input">
					<label>
						기본 수익 설정:
						<input
							type="number"
							bind:value={defaultIncome}
							step="100000"
							min="0"
						/>
					</label>
				</div>
			</div>
		{/if}

		<!-- 동심원 차트 -->
		<div class="circular-chart-container">
			<svg class="circular-chart" viewBox="0 0 200 200">
				<!-- 내부 원 (수익) - 배경 -->
				<circle
					class="circle-bg"
					cx="100"
					cy="100"
					r="50"
				/>
				<!-- 내부 원 (수익) - 채워진 부분 -->
				<circle
					class="circle-inner income"
					cx="100"
					cy="100"
					r="50"
				/>

				<!-- 외부 원 배경 -->
				<circle
					class="circle-bg-outer"
					cx="100"
					cy="100"
					r="80"
				/>

				<!-- 외부 원 - 지출 세그먼트 -->
				<circle
					class="circle-outer spend"
					cx="100"
					cy="100"
					r="80"
					stroke-dasharray="{chartData().spendDash} {chartData().circumference}"
					transform="rotate({chartData().spendRotation} 100 100)"
				/>

				<!-- 외부 원 - 저축 세그먼트 -->
				<circle
					class="circle-outer save"
					cx="100"
					cy="100"
					r="80"
					stroke-dasharray="{chartData().saveDash} {chartData().circumference}"
					transform="rotate({chartData().saveRotation} 100 100)"
				/>

				<!-- 중앙 텍스트 -->
				<text x="100" y="95" class="chart-center-label">총 수익</text>
				<text x="100" y="110" class="chart-center-value">
					{formatCurrency(chartData().income)}
				</text>
			</svg>

			<!-- 범례 및 통계 -->
			<div class="chart-stats">
				<div class="stat-item income">
					<div class="stat-header">
						<span class="stat-icon">💰</span>
						<span class="stat-name">수익</span>
					</div>
					<div class="stat-amount">{formatCurrency(chartData().income)}</div>
					{#if chartData().usingDefault}
						<div class="stat-note">(기본값)</div>
					{/if}
				</div>

				<div class="stat-item spend">
					<div class="stat-header">
						<span class="stat-icon">💸</span>
						<span class="stat-name">지출</span>
						<span class="stat-percent">{chartData().spendPercent}%</span>
					</div>
					<div class="stat-amount">{formatCurrency(chartData().spend)}</div>
				</div>

				<div class="stat-item save">
					<div class="stat-header">
						<span class="stat-icon">🏦</span>
						<span class="stat-name">저축</span>
						<span class="stat-percent">{chartData().savePercent}%</span>
					</div>
					<div class="stat-amount">{formatCurrency(chartData().save)}</div>
				</div>

				<div class="stat-item balance" style="--balance-color: {getBalanceStatus(chartData().balance).color}">
					<div class="stat-header">
						<span class="stat-icon">{getBalanceStatus(chartData().balance).icon}</span>
						<span class="stat-name">잔액 ({getBalanceStatus(chartData().balance).label})</span>
						<span class="stat-percent">{chartData().balancePercent}%</span>
					</div>
					<div class="stat-amount">{formatCurrency(Math.abs(chartData().balance))}</div>
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

	/* 기본 수익 설정 알림 */
	.default-income-notice {
		background: #fff3cd;
		border: 1px solid #ffeaa7;
		border-radius: 8px;
		padding: 16px;
		margin-bottom: 24px;
	}

	.default-income-notice p {
		margin: 0 0 12px 0;
		color: #856404;
		font-size: 0.95rem;
	}

	.income-input {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.income-input label {
		display: flex;
		align-items: center;
		gap: 8px;
		font-weight: 600;
		color: #856404;
		font-size: 0.9rem;
	}

	.income-input input {
		padding: 8px 12px;
		border: 1px solid #ffeaa7;
		border-radius: 6px;
		background: white;
		font-size: 1rem;
		width: 150px;
	}

	/* 동심원 차트 컨테이너 */
	.circular-chart-container {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 40px;
		align-items: center;
	}

	/* SVG 차트 */
	.circular-chart {
		max-width: 400px;
		width: 100%;
		height: auto;
		margin: 0 auto;
	}

	/* 원 배경 */
	.circle-bg {
		fill: none;
		stroke: #e0e0e0;
		stroke-width: 15;
	}

	.circle-bg-outer {
		fill: none;
		stroke: #e0e0e0;
		stroke-width: 25;
	}

	/* 내부 원 (수익) */
	.circle-inner {
		fill: #4caf50;
		stroke: #2e7d32;
		stroke-width: 2;
		animation: fillInner 1s ease-out;
	}

	@keyframes fillInner {
		from {
			r: 0;
		}
		to {
			r: 50;
		}
	}

	/* 외부 원 세그먼트 */
	.circle-outer {
		fill: none;
		stroke-width: 25;
		stroke-linecap: round;
		transition: all 0.3s ease;
	}

	.circle-outer.spend {
		stroke: #f44336;
		animation: drawSpend 1s ease-out 0.2s backwards;
	}

	.circle-outer.save {
		stroke: #2196f3;
		animation: drawSave 1s ease-out 0.4s backwards;
	}

	@keyframes drawSpend {
		from {
			stroke-dasharray: 0 502;
		}
	}

	@keyframes drawSave {
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

	/* 통계 리스트 */
	.chart-stats {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.stat-item {
		background: var(--bg-secondary);
		border-radius: 10px;
		padding: 16px;
		border-left: 4px solid;
		transition: all 0.2s;
	}

	.stat-item:hover {
		transform: translateX(4px);
		box-shadow: var(--shadow-md);
	}

	.stat-item.income {
		border-color: #4caf50;
	}

	.stat-item.spend {
		border-color: #f44336;
	}

	.stat-item.save {
		border-color: #2196f3;
	}

	.stat-item.balance {
		border-color: var(--balance-color);
	}

	.stat-header {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 8px;
	}

	.stat-icon {
		font-size: 1.3rem;
	}

	.stat-name {
		font-weight: 600;
		color: var(--text-primary);
		font-size: 0.95rem;
		flex: 1;
	}

	.stat-percent {
		background: rgba(99, 102, 241, 0.1);
		color: var(--accent);
		padding: 4px 10px;
		border-radius: 12px;
		font-size: 0.85rem;
		font-weight: 700;
	}

	.stat-amount {
		font-size: 1.4rem;
		font-weight: 700;
		color: var(--text-primary);
		margin: 0;
	}

	.stat-note {
		font-size: 0.8rem;
		color: var(--text-tertiary);
		margin-top: 4px;
		font-style: italic;
	}

	@media (max-width: 1024px) {
		.circular-chart-container {
			grid-template-columns: 1fr;
			gap: 32px;
		}

		.circular-chart {
			max-width: 300px;
		}
	}

	@media (max-width: 768px) {
		.report-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 16px;
		}

		.circular-chart {
			max-width: 250px;
		}

		.stat-amount {
			font-size: 1.2rem;
		}

		.income-input {
			flex-direction: column;
			align-items: flex-start;
		}

		.income-input input {
			width: 100%;
		}
	}
</style>
