<script>
	import { onMount } from 'svelte';
	import { Chart, registerables } from 'chart.js';
	import { getTransactions, getCategories } from '$lib/api/asset-manager.js';
	import { device } from '$lib/stores/device';
	import { getChartColor } from '$lib/constants.js';

	Chart.register(...registerables);

	let { year = new Date().getFullYear() } = $props();

	let data = $state(null);
	let loading = $state(false);
	let error = $state(null);

	let chartCanvas = $state(null);
	let chartInstance = null;

	// 카테고리별 토글 상태
	let categoryVisibility = $state({});
	let categories = $state([]);

	onMount(() => {
		loadData();
	});

	async function loadData() {
		loading = true;
		error = null;

		try {
			// 수익(earn) 카테고리 로드 (class_id = 2)
			const earnCategories = await getCategories(2);
			categories = earnCategories;

			// 초기 visibility 설정 (모두 visible)
			categoryVisibility = {};
			earnCategories.forEach((cat) => {
				categoryVisibility[cat.display_name] = true;
			});

			// 올해 전체 트랜잭션 로드
			const startDate = `${year}-01-01`;
			const endDate = `${year}-12-31`;

			const transactions = await getTransactions({
				start_date: startDate,
				end_date: endDate,
				class_id: 2, // 수익만
				limit: 10000
			});

			// 월별, 카테고리별 데이터 집계
			const monthlyData = {};
			for (let m = 1; m <= 12; m++) {
				monthlyData[m] = {};
				earnCategories.forEach((cat) => {
					monthlyData[m][cat.display_name] = 0;
				});
			}

			transactions.forEach((tx) => {
				const txDate = new Date(tx.date);
				const txMonth = txDate.getMonth() + 1;
				const categoryName = tx.category_display_name || tx.category_name;

				if (monthlyData[txMonth] && categoryName) {
					if (monthlyData[txMonth][categoryName] === undefined) {
						monthlyData[txMonth][categoryName] = 0;
					}
					monthlyData[txMonth][categoryName] += Math.abs(tx.cost);
				}
			});

			// 올해 총 수익 계산
			let totalIncome = 0;
			transactions.forEach((tx) => {
				totalIncome += Math.abs(tx.cost);
			});

			// 월 평균 계산 (현재 월까지만)
			const currentMonth = new Date().getMonth() + 1;
			const monthsToConsider = year === new Date().getFullYear() ? currentMonth : 12;
			const monthlyAverage = monthsToConsider > 0 ? totalIncome / monthsToConsider : 0;

			data = {
				monthlyData,
				categories: earnCategories,
				totalIncome,
				monthlyAverage,
				currentMonth: monthsToConsider
			};

			// 차트 업데이트
			setTimeout(() => {
				updateChart();
			}, 100);
		} catch (err) {
			console.error('Failed to load yearly income data:', err);
			error = '데이터를 불러오는데 실패했습니다.';
		} finally {
			loading = false;
		}
	}

	function toggleCategory(categoryName) {
		categoryVisibility[categoryName] = !categoryVisibility[categoryName];
		updateChart();
	}

	function formatCurrency(value) {
		if (value === null || value === undefined) return '0원';
		return new Intl.NumberFormat('ko-KR').format(Math.abs(value)) + '원';
	}

	function getChartData() {
		if (!data || !data.monthlyData) return null;

		const labels = [];
		for (let m = 1; m <= 12; m++) {
			labels.push(`${m}월`);
		}

		const datasets = [];
		let colorIndex = 0;

		data.categories.forEach((cat) => {
			const categoryName = cat.display_name;
			if (!categoryVisibility[categoryName]) return;

			const monthlyValues = [];
			for (let m = 1; m <= 12; m++) {
				monthlyValues.push(data.monthlyData[m][categoryName] || 0);
			}

			datasets.push({
				label: categoryName,
				data: monthlyValues,
				backgroundColor: getChartColor(colorIndex),
				borderWidth: 0,
				borderRadius: 4
			});
			colorIndex++;
		});

		return { labels, datasets };
	}

	function updateChart() {
		if (!chartCanvas) return;

		const chartData = getChartData();
		if (!chartData) return;

		try {
			if (chartInstance) {
				chartInstance.destroy();
				chartInstance = null;
			}

			const ctx = chartCanvas.getContext('2d');
			chartInstance = new Chart(ctx, {
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
							display: false // 커스텀 범례 사용
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
									tooltipItems.forEach((item) => {
										total += item.parsed.y;
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
									size: 11,
									weight: '500'
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
			console.error('Chart update error:', err);
		}
	}

	$effect(() => {
		if (year) {
			loadData();
		}
	});
</script>

<div class="module-container" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<div class="chart-header">
		<h3>{year}년 월별 수익 비교</h3>
	</div>

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>데이터를 불러오는 중...</p>
		</div>
	{:else if error}
		<div class="error">
			<p>{error}</p>
			<button class="retry-btn" onclick={loadData}>다시 시도</button>
		</div>
	{:else if data}
		<!-- 요약 정보 -->
		<div class="summary-section">
			<div class="summary-item">
				<span class="summary-label">올해 총 수익:</span>
				<span class="summary-value total">{formatCurrency(data.totalIncome)}</span>
			</div>
			<div class="summary-item">
				<span class="summary-label">월 평균 ({data.currentMonth}개월):</span>
				<span class="summary-value average">{formatCurrency(data.monthlyAverage)}</span>
			</div>
		</div>

		<!-- 카테고리 토글 버튼 -->
		<div class="category-toggles">
			{#each categories as cat, index}
				<button
					class="category-toggle-btn"
					class:active={categoryVisibility[cat.display_name]}
					onclick={() => toggleCategory(cat.display_name)}
				>
					<span
						class="color-dot"
						style="background: {categoryVisibility[cat.display_name]
							? getChartColor(index)
							: '#ccc'}"
					></span>
					<span>{cat.display_name}</span>
				</button>
			{/each}
		</div>

		<!-- 차트 -->
		<div class="chart-container">
			<canvas bind:this={chartCanvas}></canvas>
		</div>
	{/if}
</div>

<style>
	/* 요약 섹션 */
	.summary-section {
		display: flex;
		gap: 24px;
		margin-bottom: 12px;
		color: var(--text-secondary);
		font-size: 0.9rem;
	}

	.summary-item {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.summary-label {
		color: var(--text-tertiary);
	}

	.summary-value {
		font-weight: 400;
		color: var(--text-primary);
	}

	.summary-value.total {
		color: #4caf50;
	}

	.summary-value.average {
		color: #2196f3;
	}

	/* 카테고리 토글 */
	.category-toggles {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-bottom: 12px;
	}

	.category-toggle-btn {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 2px 8px;
		border: none;
		border-radius: 4px;
		background: transparent;
		cursor: pointer;
		font-size: 0.8rem;
		color: var(--text-tertiary);
	}

	.category-toggle-btn.active {
		color: var(--text-primary);
	}

	.color-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	/* 차트 영역 */
	.chart-container {
		height: 300px;
		position: relative;
	}

	/* Tablet */
	.module-container.tablet {
		.summary-section {
			flex-direction: column;
			gap: 4px;
		}

		.chart-container {
			height: 250px;
		}
	}

	/* Mobile */
	.module-container.mobile {
		.summary-section {
			flex-direction: column;
			gap: 4px;
			font-size: 0.85rem;
		}

		.category-toggles {
			gap: 4px;
		}

		.category-toggle-btn {
			padding: 2px 6px;
			font-size: 0.75rem;
		}

		.chart-container {
			height: 220px;
		}
	}
</style>
