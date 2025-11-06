<script>
	import { onMount } from 'svelte';
	import { Chart, registerables } from 'chart.js';
	import { getPeriodComparison } from '$lib/api/asset-manager.js';

	Chart.register(...registerables);

	let { unit = 'week', periods = 4 } = $props();

	let data = $state(null);
	let loading = $state(false);
	let error = $state(null);
	let selectedUnit = $state(unit);

	let spendChartCanvas = $state(null);
	let saveChartCanvas = $state(null);
	let spendChartInstance = null;
	let saveChartInstance = null;

	const units = [
		{ value: 'day', label: '일별', icon: '📅' },
		{ value: 'week', label: '주별', icon: '📆' },
		{ value: 'month', label: '월별', icon: '🗓️' },
		{ value: 'year', label: '연도별', icon: '📊' }
	];

	onMount(() => {
		loadData();
	});

	async function loadData() {
		loading = true;
		error = null;

		try {
			const response = await getPeriodComparison(selectedUnit, periods);
			data = response;

			// 차트 업데이트는 DOM이 준비된 후 실행
			setTimeout(() => {
				updateSpendChart();
				updateSaveChart();
			}, 100);
		} catch (err) {
			console.error('Failed to load period comparison:', err);
			error = '데이터를 불러오는데 실패했습니다.';
		} finally {
			loading = false;
		}
	}

	function handleUnitChange(newUnit) {
		selectedUnit = newUnit;
		loadData();
	}

	function formatCurrency(value) {
		if (value === null || value === undefined) return '0원';
		return new Intl.NumberFormat('ko-KR').format(Math.abs(value)) + '원';
	}

	function formatTrend(value) {
		if (value === null || value === undefined) return '-';
		const sign = value >= 0 ? '+' : '';
		return sign + value.toFixed(1) + '%';
	}

	function getTrendColor(value) {
		if (value === null || value === undefined) return '#666';
		return value >= 0 ? '#4caf50' : '#f44336';
	}

	function getTrendIcon(value) {
		if (value === null || value === undefined) return '━';
		return value >= 0 ? '▲' : '▼';
	}

	// 지출 카테고리별 차트 데이터 생성
	function getSpendChartData() {
		if (!data || !data.periods) return null;

		const categoryMap = new Map();

		// 모든 기간의 지출 카테고리 수집
		data.periods.forEach((period) => {
			period.by_category.forEach((cat) => {
				if (!categoryMap.has(cat.category_display_name)) {
					categoryMap.set(cat.category_display_name, []);
				}
			});
		});

		// 카테고리가 없으면 null 반환
		if (categoryMap.size === 0) return null;

		const labels = data.periods.map((p) => p.period_label).reverse();
		const datasets = [];

		let colorIndex = 0;
		categoryMap.forEach((_, categoryDisplayName) => {
			const categoryData = data.periods
				.map((period) => {
					const cat = period.by_category.find(
						(c) => c.category_display_name === categoryDisplayName
					);
					return cat ? Math.abs(cat.total_cost) : 0;
				})
				.reverse();

			const bgColor = getCategoryColor(colorIndex);
			datasets.push({
				label: categoryDisplayName,
				data: categoryData,
				backgroundColor: bgColor,
				borderColor: getBorderColor(bgColor),
				borderWidth: 2,
				borderRadius: 6
			});
			colorIndex++;
		});

		return { labels, datasets };
	}

	// 저축 추이 차트 데이터 생성
	function getSaveChartData() {
		if (!data || !data.periods) return null;

		const labels = data.periods.map((p) => p.period_label).reverse();
		const saveData = data.periods.map((p) => Math.abs(p.save_total)).reverse();

		return {
			labels,
			datasets: [
				{
					label: '저축',
					data: saveData,
					backgroundColor: 'rgba(33, 150, 243, 0.7)',
					borderColor: 'rgba(33, 150, 243, 1)',
					borderWidth: 2,
					borderRadius: 6
				}
			]
		};
	}

	function getCategoryColor(index) {
		const colors = [
			'rgba(244, 67, 54, 0.7)', // 빨강
			'rgba(156, 39, 176, 0.7)', // 보라
			'rgba(63, 81, 181, 0.7)', // 남색
			'rgba(33, 150, 243, 0.7)', // 파랑
			'rgba(0, 188, 212, 0.7)', // 청록
			'rgba(76, 175, 80, 0.7)', // 초록
			'rgba(255, 193, 7, 0.7)', // 노랑
			'rgba(255, 152, 0, 0.7)', // 주황
			'rgba(121, 85, 72, 0.7)', // 갈색
			'rgba(158, 158, 158, 0.7)' // 회색
		];
		return colors[index % colors.length];
	}

	function getBorderColor(bgColor) {
		return bgColor.replace('0.7', '1');
	}

	function updateSpendChart() {
		if (!spendChartCanvas) return;

		const chartData = getSpendChartData();
		if (!chartData) return;

		try {
			if (spendChartInstance) {
				spendChartInstance.destroy();
				spendChartInstance = null;
			}

			const ctx = spendChartCanvas.getContext('2d');
			spendChartInstance = new Chart(ctx, {
				type: 'bar',
				data: chartData,
				options: {
					responsive: true,
					maintainAspectRatio: false,
					interaction: {
						mode: 'index',
						intersect: false
					},
					plugins: {
						legend: {
							position: 'top',
							labels: {
								font: {
									size: 12,
									weight: '600'
								},
								padding: 12,
								usePointStyle: true,
								pointStyle: 'circle'
							}
						},
						tooltip: {
							backgroundColor: 'rgba(0, 0, 0, 0.8)',
							padding: 12,
							titleFont: {
								size: 13,
								weight: 'bold'
							},
							bodyFont: {
								size: 12
							},
							callbacks: {
								label: function (context) {
									let label = context.dataset.label || '';
									if (label) {
										label += ': ';
									}
									if (context.parsed.y !== null) {
										label += new Intl.NumberFormat('ko-KR').format(context.parsed.y) + '원';
									}
									return label;
								},
								footer: function (tooltipItems) {
									let total = 0;
									tooltipItems.forEach(function (tooltipItem) {
										total += tooltipItem.parsed.y;
									});
									return '합계: ' + new Intl.NumberFormat('ko-KR').format(total) + '원';
								}
							}
						}
					},
					scales: {
						x: {
							stacked: true,
							grid: {
								display: false
							},
							ticks: {
								font: {
									size: 11
								}
							}
						},
						y: {
							stacked: true,
							beginAtZero: true,
							grid: {
								color: 'rgba(0, 0, 0, 0.05)'
							},
							ticks: {
								font: {
									size: 11
								},
								callback: function (value) {
									if (value >= 1000000) {
										return (value / 1000000).toFixed(0) + 'M';
									} else if (value >= 1000) {
										return (value / 1000).toFixed(0) + 'K';
									}
									return value;
								}
							}
						}
					}
				}
			});
		} catch (err) {
			console.error('Spend chart update error:', err);
		}
	}

	function updateSaveChart() {
		if (!saveChartCanvas) return;

		const chartData = getSaveChartData();
		if (!chartData) return;

		try {
			if (saveChartInstance) {
				saveChartInstance.destroy();
				saveChartInstance = null;
			}

			const ctx = saveChartCanvas.getContext('2d');
			saveChartInstance = new Chart(ctx, {
				type: 'bar',
				data: chartData,
				options: {
					responsive: true,
					maintainAspectRatio: false,
					plugins: {
						legend: {
							display: false
						},
						tooltip: {
							backgroundColor: 'rgba(0, 0, 0, 0.8)',
							padding: 12,
							titleFont: {
								size: 13,
								weight: 'bold'
							},
							bodyFont: {
								size: 12
							},
							callbacks: {
								label: function (context) {
									if (context.parsed.y !== null) {
										return (
											'저축: ' +
											new Intl.NumberFormat('ko-KR').format(context.parsed.y) +
											'원'
										);
									}
									return '';
								}
							}
						}
					},
					scales: {
						x: {
							grid: {
								display: false
							},
							ticks: {
								font: {
									size: 11
								}
							}
						},
						y: {
							beginAtZero: true,
							grid: {
								color: 'rgba(0, 0, 0, 0.05)'
							},
							ticks: {
								font: {
									size: 11
								},
								callback: function (value) {
									if (value >= 1000000) {
										return (value / 1000000).toFixed(0) + 'M';
									} else if (value >= 1000) {
										return (value / 1000).toFixed(0) + 'K';
									}
									return value;
								}
							}
						}
					}
				}
			});
		} catch (err) {
			console.error('Save chart update error:', err);
		}
	}
</script>

<div class="period-comparison">
	<div class="comparison-header">
		<h2>📊 기간별 비교 분석</h2>
		<div class="controls">
			<div class="unit-selector">
				{#each units as unitOption}
					<button
						class="unit-btn"
						class:active={selectedUnit === unitOption.value}
						onclick={() => handleUnitChange(unitOption.value)}
					>
						<span class="unit-icon">{unitOption.icon}</span>
						<span>{unitOption.label}</span>
					</button>
				{/each}
			</div>
			<button class="refresh-btn" onclick={loadData} disabled={loading} aria-label="새로고침">
				<svg
					width="18"
					height="18"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
				>
					<path d="M23 4v6h-6M1 20v-6h6" />
					<path
						d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"
					/>
				</svg>
			</button>
		</div>
	</div>

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>데이터를 불러오는 중...</p>
		</div>
	{:else if error}
		<div class="error">
			<p>⚠️ {error}</p>
			<button class="retry-btn" onclick={loadData}>다시 시도</button>
		</div>
	{:else if data}
		<!-- 트렌드 요약 -->
		<div class="trend-summary">
			<div class="trend-card spend">
				<div class="trend-label">
					<span class="trend-icon">💸</span>
					<span>평균 지출</span>
				</div>
				<div class="trend-value">{formatCurrency(data.avg_spend)}</div>
				<div class="trend-change" style="color: {getTrendColor(data.spend_trend)}">
					<span>{getTrendIcon(data.spend_trend)}</span>
					<span>{formatTrend(data.spend_trend)}</span>
				</div>
			</div>

			<div class="trend-card earn">
				<div class="trend-label">
					<span class="trend-icon">💰</span>
					<span>평균 수익</span>
				</div>
				<div class="trend-value">{formatCurrency(data.avg_earn)}</div>
				<div class="trend-change" style="color: {getTrendColor(data.earn_trend)}">
					<span>{getTrendIcon(data.earn_trend)}</span>
					<span>{formatTrend(data.earn_trend)}</span>
				</div>
			</div>

			<div class="trend-card save">
				<div class="trend-label">
					<span class="trend-icon">🏦</span>
					<span>평균 저축</span>
				</div>
				<div class="trend-value">{formatCurrency(data.avg_save)}</div>
			</div>
		</div>

		<!-- 지출 카테고리별 차트 -->
		{#if getSpendChartData()}
			<div class="chart-section">
				<h3>💸 지출 카테고리별 비교</h3>
				<div class="chart-container">
					<canvas bind:this={spendChartCanvas}></canvas>
				</div>
			</div>
		{/if}

		<!-- 저축 추이 차트 -->
		<div class="chart-section">
			<h3>💰 저축 추이</h3>
			<div class="chart-container">
				<canvas bind:this={saveChartCanvas}></canvas>
			</div>
		</div>

		<!-- 기간별 상세 정보 -->
		<div class="periods-grid">
			{#each data.periods as period, index}
				<div class="period-card">
					<div class="period-header">
						<h3>{period.period_label}</h3>
						<span class="period-index">기간 {data.periods.length - index}</span>
					</div>

					<div class="period-stats">
						<div class="stat-item spend">
							<span class="stat-label">💸 지출</span>
							<span class="stat-value">{formatCurrency(period.spend_total)}</span>
						</div>
						<div class="stat-item earn">
							<span class="stat-label">💰 수익</span>
							<span class="stat-value">{formatCurrency(period.earn_total)}</span>
						</div>
						<div class="stat-item save">
							<span class="stat-label">🏦 저축</span>
							<span class="stat-value">{formatCurrency(period.save_total)}</span>
						</div>
					</div>

					<!-- 주요 카테고리 -->
					<div class="top-categories">
						<h4>주요 카테고리</h4>
						{#if period.by_category && period.by_category.length > 0}
							<div class="category-list">
								{#each period.by_category.slice(0, 3) as cat}
									<div class="category-item">
										<span class="category-name">{cat.category_display_name}</span>
										<span class="category-value">{formatCurrency(cat.total_cost)}</span>
									</div>
								{/each}
							</div>
						{:else}
							<p class="no-data">카테고리 데이터 없음</p>
						{/if}
					</div>

					<!-- 상위 거래 -->
					<div class="top-transactions">
						<h4>상위 거래</h4>
						{#if period.top_transactions && period.top_transactions.length > 0}
							<div class="transaction-list">
								{#each period.top_transactions.slice(0, 3) as trans}
									<div class="transaction-item">
										<div class="trans-info">
											<span class="trans-name">{trans.name}</span>
											<span class="trans-date"
												>{new Date(trans.date).toLocaleDateString('ko-KR')}</span
											>
										</div>
										<span class="trans-value">{formatCurrency(trans.cost)}</span>
									</div>
								{/each}
							</div>
						{:else}
							<p class="no-data">거래 내역 없음</p>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.period-comparison {
		background: white;
		border-radius: 16px;
		padding: 28px;
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
	}

	.comparison-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 28px;
		flex-wrap: wrap;
		gap: 16px;
	}

	.comparison-header h2 {
		font-size: 22px;
		font-weight: 700;
		color: #1a1a1a;
		margin: 0;
	}

	.controls {
		display: flex;
		gap: 16px;
		align-items: center;
	}

	.unit-selector {
		display: flex;
		gap: 8px;
		background: #f5f5f5;
		padding: 4px;
		border-radius: 10px;
	}

	.unit-btn {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 16px;
		background: transparent;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-size: 14px;
		font-weight: 500;
		color: #666;
		transition: all 0.2s ease;
	}

	.unit-btn:hover {
		background: rgba(33, 150, 243, 0.1);
		color: #2196f3;
	}

	.unit-btn.active {
		background: white;
		color: #2196f3;
		box-shadow: 0 2px 8px rgba(33, 150, 243, 0.15);
	}

	.unit-icon {
		font-size: 16px;
	}

	.refresh-btn {
		padding: 10px;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.refresh-btn:hover:not(:disabled) {
		background: #f5f5f5;
		border-color: #2196f3;
		color: #2196f3;
	}

	.refresh-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.loading,
	.error {
		text-align: center;
		padding: 60px 20px;
		color: #666;
	}

	.spinner {
		width: 40px;
		height: 40px;
		margin: 0 auto 16px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #2196f3;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	.error p {
		color: #f44336;
		font-size: 16px;
		margin-bottom: 16px;
	}

	.retry-btn {
		padding: 10px 24px;
		background: #2196f3;
		color: white;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-size: 14px;
		font-weight: 500;
		transition: background 0.2s ease;
	}

	.retry-btn:hover {
		background: #1976d2;
	}

	.chart-section {
		margin-bottom: 32px;
		background: #fafafa;
		padding: 24px;
		border-radius: 12px;
	}

	.chart-section h3 {
		font-size: 18px;
		font-weight: 600;
		color: #333;
		margin: 0 0 20px 0;
	}

	.chart-container {
		height: 320px;
		position: relative;
	}

	.trend-summary {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 16px;
		margin-bottom: 32px;
	}

	.trend-card {
		background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
		padding: 20px;
		border-radius: 12px;
		border: 2px solid transparent;
		transition: all 0.3s ease;
	}

	.trend-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.trend-card.spend {
		border-color: rgba(244, 67, 54, 0.2);
	}

	.trend-card.earn {
		border-color: rgba(76, 175, 80, 0.2);
	}

	.trend-card.save {
		border-color: rgba(33, 150, 243, 0.2);
	}

	.trend-label {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 14px;
		color: #666;
		margin-bottom: 10px;
	}

	.trend-icon {
		font-size: 20px;
	}

	.trend-value {
		font-size: 24px;
		font-weight: 700;
		color: #1a1a1a;
		margin-bottom: 8px;
	}

	.trend-change {
		display: flex;
		align-items: center;
		gap: 4px;
		font-size: 13px;
		font-weight: 600;
	}

	.periods-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: 20px;
		margin-top: 24px;
	}

	.period-card {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 12px;
		padding: 20px;
		transition: all 0.3s ease;
	}

	.period-card:hover {
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
		border-color: #2196f3;
	}

	.period-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;
		padding-bottom: 12px;
		border-bottom: 2px solid #f0f0f0;
	}

	.period-header h3 {
		font-size: 16px;
		font-weight: 600;
		color: #1a1a1a;
		margin: 0;
	}

	.period-index {
		font-size: 12px;
		color: #999;
		background: #f5f5f5;
		padding: 4px 10px;
		border-radius: 12px;
	}

	.period-stats {
		display: flex;
		flex-direction: column;
		gap: 10px;
		margin-bottom: 16px;
	}

	.stat-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px;
		background: #fafafa;
		border-radius: 8px;
	}

	.stat-label {
		font-size: 13px;
		color: #666;
		font-weight: 500;
	}

	.stat-value {
		font-size: 15px;
		font-weight: 600;
		color: #1a1a1a;
	}

	.top-categories,
	.top-transactions {
		margin-top: 16px;
	}

	.top-categories h4,
	.top-transactions h4 {
		font-size: 13px;
		font-weight: 600;
		color: #666;
		margin: 0 0 10px 0;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.category-list,
	.transaction-list {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.category-item,
	.transaction-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 8px;
		background: #f8f9fa;
		border-radius: 6px;
		font-size: 13px;
	}

	.category-name,
	.trans-info {
		color: #333;
		font-weight: 500;
	}

	.trans-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.trans-name {
		font-size: 13px;
		font-weight: 500;
		color: #333;
	}

	.trans-date {
		font-size: 11px;
		color: #999;
	}

	.category-value,
	.trans-value {
		color: #f44336;
		font-weight: 600;
	}

	.no-data {
		text-align: center;
		color: #999;
		font-size: 12px;
		padding: 12px;
		background: #f8f9fa;
		border-radius: 6px;
		margin: 0;
	}

	@media (max-width: 768px) {
		.period-comparison {
			padding: 20px;
		}

		.comparison-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.controls {
			width: 100%;
			flex-direction: column;
		}

		.unit-selector {
			width: 100%;
			justify-content: space-between;
		}

		.unit-btn {
			flex: 1;
			padding: 8px 12px;
		}

		.chart-container {
			height: 280px;
		}

		.periods-grid {
			grid-template-columns: 1fr;
		}

		.trend-summary {
			grid-template-columns: 1fr;
		}
	}
</style>
