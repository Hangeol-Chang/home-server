<script>
	import { Chart, registerables } from 'chart.js';
	import { getBudgets, getPeriodComparison, getCategories, getTransactions } from '$lib/api/asset-manager.js';
	import { device } from '$lib/stores/device';
	import TransactionDropdown from './TransactionDropdown.svelte';

	Chart.register(...registerables);

	let { year, month, period = 'month' } = $props();

	// 기간 단위별 [시작 월, 개월 수]
	function periodRange(p, m) {
		if (p === 'quarter') return [Math.floor((m - 1) / 3) * 3 + 1, 3];
		if (p === 'half') return [m <= 6 ? 1 : 7, 6];
		if (p === 'year') return [1, 12];
		return [m, 1];
	}

	let chartCanvas = $state(null);
	let chartInstance = null;
	let loading = $state(false);
	let error = $state(null);

	let categoryIds = [];
	let dropdownVisible = $state(false);
	let dropdownTitle = $state('');
	let dropdownList = $state([]);

	async function openCategory(index) {
		const [startMonth, n] = periodRange(period, month);
		const endMonth = startMonth + n - 1;
		const pad = (v) => String(v).padStart(2, '0');
		try {
			dropdownList = await getTransactions({
				category_id: categoryIds[index],
				start_date: `${year}-${pad(startMonth)}-01`,
				end_date: `${year}-${pad(endMonth)}-${new Date(year, endMonth, 0).getDate()}`,
				limit: 10000
			});
			dropdownTitle = `${chartInstance.data.labels[index]} 지출 내역`;
			dropdownVisible = true;
		} catch (err) {
			console.error('Failed to load category transactions:', err);
		}
	}

	$effect(() => {
		if (year && month && period) {
			loadData();
		}
	});

	async function loadData() {
		if (!year || !month) return;
		
		loading = true;
		error = null;

		try {
			const [startMonth, n] = periodRange(period, month);
			const endMonth = startMonth + n - 1;
			const lastDay = new Date(year, endMonth, 0).getDate();
			const endDate = `${year}-${String(endMonth).padStart(2, '0')}-${lastDay}`;

			// 예산은 월 단위로 저장되므로 기간 내 월별 예산을 합산 (period-comparison은 최대 8기간 → 연은 year 단위 사용)
			const [budgetLists, periodStats, categories] = await Promise.all([
				Promise.all(Array.from({ length: n }, (_, i) => getBudgets(year, startMonth + i))),
				period === 'year' ? getPeriodComparison('year', 1, endDate) : getPeriodComparison('month', n, endDate),
				getCategories() // 카테고리 이름 매핑용
			]);
			const budgets = budgetLists.flat();

			// 데이터 가공
			const categoryMap = new Map();
			
			// 1. 카테고리 기본 정보 설정
			categories.forEach(cat => {
				if (cat.class_id === 1) { // 지출 카테고리만
					categoryMap.set(cat.id, {
						name: cat.display_name || cat.name,
						budget: 0,
						spent: 0
					});
				}
			});

			// 2. 예산 정보 매핑
			budgets.forEach(b => {
				if (categoryMap.has(b.category_id)) {
					categoryMap.get(b.category_id).budget += b.budget_amount;
				}
			});

			// 3. 지출 정보 매핑
			(periodStats?.periods ?? []).forEach(p => {
				(p.by_category ?? []).forEach(cat => {
					if (categoryMap.has(cat.category_id)) {
						categoryMap.get(cat.category_id).spent += Math.abs(cat.total_cost);
					}
				});
			});

			// 차트 데이터 생성
			const labels = [];
			categoryIds = [];
			const budgetData = [];
			const spentData = [];

			// 예산이나 지출이 있는 카테고리만 필터링하거나 전체 표시
			// 여기서는 예산이 0보다 크거나 지출이 0보다 큰 경우만 표시
			for (const [id, data] of categoryMap.entries()) {
				if (data.budget > 0 || data.spent > 0) {
					labels.push(data.name);
					categoryIds.push(id);
					budgetData.push(data.budget);
					spentData.push(data.spent);
				}
			}

			updateChart(labels, budgetData, spentData);

		} catch (err) {
			console.error('Failed to load budget comparison data:', err);
			error = '데이터를 불러오는데 실패했습니다.';
		} finally {
			loading = false;
		}
	}

	function updateChart(labels, budgetData, spentData) {
		if (!chartCanvas) return;

		if (chartInstance) {
			chartInstance.destroy();
		}

		const ctx = chartCanvas.getContext('2d');
		
		// 지출이 예산을 초과했는지에 따라 색상 결정
		const spentColors = spentData.map((spent, index) => {
			const budget = budgetData[index];
			if (budget > 0 && spent > budget) {
				return '#f44336'; // 초과 시 빨간색
			}
			return '#4caf50'; // 정상 시 초록색
		});

		chartInstance = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: labels,
				datasets: [
					{
						label: '예산',
						data: budgetData,
						backgroundColor: '#e0e0e0',
						borderRadius: 4,
						barPercentage: 1.0,
						categoryPercentage: 0.7,
                        order: 1
					},
					{
						label: '지출',
						data: spentData,
						backgroundColor: spentColors,
						borderRadius: 4,
						barPercentage: 1.0,
						categoryPercentage: 0.7,
                        order: 2
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				onClick: (_, elements) => elements.length && openCategory(elements[0].index),
				onHover: (e, elements) => {
					e.native.target.style.cursor = elements.length ? 'pointer' : 'default';
				},
				interaction: {
					mode: 'index',
					intersect: false,
				},
				plugins: {
					legend: {
						position: 'top',
						align: 'end',
						labels: {
							usePointStyle: true,
							boxWidth: 8,
                            font: {
                                family: 'Pretendard'
                            }
						}
					},
					tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            family: 'Pretendard',
                            size: 13
                        },
                        bodyFont: {
                            family: 'Pretendard',
                            size: 12
                        },
						callbacks: {
							label: function(context) {
								let label = context.dataset.label || '';
								if (label) {
									label += ': ';
								}
								if (context.parsed.y !== null) {
									label += new Intl.NumberFormat('ko-KR').format(context.parsed.y) + '원';
								}
								return label;
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
                                family: 'Pretendard',
								size: 11
							}
						}
					},
					y: {
						beginAtZero: true,
						grid: {
							color: '#f0f0f0'
						},
						ticks: {
							callback: function(value) {
								if (value >= 1000000) return (value/1000000).toFixed(1) + 'M';
								if (value >= 1000) return (value/1000).toFixed(0) + 'K';
								return value;
							},
							font: {
                                family: 'Pretendard',
								size: 10
							}
						}
					}
				}
			}
		});
	}
</script>

<div class="module-container" class:mobile={$device.isMobile}>
	<h3>예산 대비 지출 현황</h3>
	
	<div class="content-wrapper">
		{#if loading}
			<div class="loading-overlay">데이터 로딩 중...</div>
		{/if}

		{#if error}
			<div class="error">{error}</div>
		{:else}
			<div class="chart-container">
				<canvas bind:this={chartCanvas}></canvas>
			</div>
		{/if}
	</div>
</div>

<TransactionDropdown
	bind:visible={dropdownVisible}
	mode="list"
	title={dropdownTitle}
	transactions={dropdownList}
/>

<style>
	.module-container {
		padding: 12px 0;
	}

	h3 {
		margin-bottom: 20px;
		font-size: 1.1rem;
		color: var(--text-primary);
	}

	.content-wrapper {
		position: relative;
		min-height: 300px;
	}

	.chart-container {
		height: 300px;
		width: 100%;
		position: relative;
	}

	.loading-overlay {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(255, 255, 255, 0.8);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-secondary);
		font-size: 0.9rem;
		z-index: 10;
	}

	.error {
		height: 200px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-danger);
		font-size: 0.9rem;
	}
</style>
