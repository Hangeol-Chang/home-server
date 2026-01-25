<script>
	import { onMount } from 'svelte';
	import { Chart, registerables } from 'chart.js';
	import { getPeriodComparison } from '$lib/api/asset-manager.js';
	import { device } from '$lib/stores/device';
	import { getChartColor } from '$lib/constants.js';

	Chart.register(...registerables);

	let { unit = 'week', periods = 4 } = $props();

	let data = $state(null);
	let loading = $state(false);
	let error = $state(null);
	let selectedUnit = $state(unit);

	let spendChartCanvas = $state(null);
	let saveChartCanvas = $state(null);
	let spendChartInstance = null;
	let saveChartInstance = null;0

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
		if (value === null || value === undefined) return '0';
		return new Intl.NumberFormat('ko-KR').format(Math.abs(value)) + '';
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

			const bgColor = getChartColor(colorIndex);
			datasets.push({
				label: categoryDisplayName,
				data: categoryData,
				backgroundColor: bgColor,
				borderWidth: 0,
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
					backgroundColor: '#c89f9c',
					borderWidth: 0,
					borderRadius: 6
				}
			]
		};
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

<div class="module-container" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<div class="chart-header">
		<div class="tab-buttons">
			{#each units as unitOption}
				<button
					class="tab-btn"
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
		<!-- 지출 카테고리별 차트 -->
		{#if getSpendChartData()}
            <h3>💸 SPEND</h3>
			<div class="chart-section">
                <table class="data-table compact">
                    <thead>
                        <tr>
                            <th>period</th>
                            <th class="text-right">sum</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each data.periods as period, index}
                            <tr>
                                <td class="period-label">
                                    {period.period_label}
                                </td>
                                <td class="period-value text-right">
                                    {formatCurrency(period.spend_total)}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
				<div class="chart-container">
					<canvas bind:this={spendChartCanvas}></canvas>
				</div>
			</div>
		{/if}

		<!-- 저축 추이 차트 -->
        <!-- <h3>💰 SAVE</h3>
		<div class="chart-section">
            <table class="data-table compact">
                <thead>
                    <tr>
                        <th>period</th>
                        <th class="text-right">sum</th>
                    </tr>
                </thead>
                <tbody>
                    {#each data.periods as period, index}
                        <tr>
                            <td class="period-label">
                                {period.period_label}
                            </td>
                            <td class="period-value text-right">
                                {formatCurrency(period.save_total)}
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
			<div class="chart-container">
				<canvas bind:this={saveChartCanvas}></canvas>
			</div>
		</div> -->

		<!-- 기간별 상세 정보 -->
		<!-- <div class="periods-grid">
			{#each data.periods as period, index}
				<div class="period-card">
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
		</div> -->
	{/if}
</div>

<style>
	.chart-section {
		display: flex;
		gap: 16px;
		margin: 16px 0px;
		background: var(--bg-primary);
		box-shadow: var(--shadow-md);
		padding: 24px;
		border-radius: 8px;
	}

	.chart-container {
		width: 100%;
		height: 320px;
		position: relative;
		flex-grow: 1;
	}

	.data-table.compact {
		max-width: 300px;
		flex-grow: 1;
		box-shadow: var(--shadow-md);
	}

	.period-label {
		font-weight: 300;
		font-size: 12px;
		color: var(--text-secondary);
    }

    .period-value {
        font-weight: 400;
        color: var(--text-primary);
    }



	/* Tablet/Mobile (< 768px) */
	.module-container {
		&.tablet {
			padding: 16px;

			.chart-section {
				flex-direction: column;
				align-items: center;
				gap: 20px;
			}

			.chart-container {
				height: 260px;
			}

			.data-table.compact {
				max-width: 100%;
				font-size: 0.85rem;

				th,
				td {
					padding: 6px 4px;
				}
			}

			.period-value {
				font-size: 0.9rem;
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			padding: 12px;

			.chart-container {
				height: 220px;
			}

			.data-table.compact {
				font-size: 0.8rem;

				th,
				td {
					padding: 5px 3px;
					font-size: 0.75rem;
				}
			}

			.period-label {
				font-size: 0.7rem;
			}

			.period-value {
				font-size: 0.85rem;
			}
		}
	}
</style>
