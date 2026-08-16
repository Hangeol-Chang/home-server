<script>
	import { Chart, registerables } from 'chart.js';
	import { getPeriodStatistics } from '$lib/api/asset-manager.js';

	Chart.register(...registerables);

	let {
		classId = 1,
		startDate = null,
		endDate = null
	} = $props();

	let stats = $state(null);
	let loading = $state(true);
	let error = $state('');
	let viewType = $state('category'); // 'category' 또는 'tier'

	let canvasEl = $state(null);
	let chartInstance = null;

	async function loadStatistics() {
		loading = true;
		error = '';
		try {
			stats = await getPeriodStatistics(classId, startDate, endDate);
		} catch (err) {
			error = '통계를 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	function formatCurrency(value) {
		return new Intl.NumberFormat('ko-KR').format(value) + '원';
	}

	function getPercentage(value) {
		if (!stats || stats.total_cost === 0) return 0;
		return ((value / stats.total_cost) * 100).toFixed(1);
	}

	// 차트 색상
	const categoryColors = [
		'#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5',
		'#2196f3', '#03a9f4', '#00bcd4', '#009688', '#4caf50',
		'#8bc34a', '#cddc39', '#ffeb3b', '#ffc107', '#ff9800',
		'#ff5722', '#795548', '#9e9e9e', '#607d8b'
	];

	function getColor(index) {
		return categoryColors[index % categoryColors.length];
	}

	function currentItems() {
		if (!stats) return [];
		if (viewType === 'category') {
			return stats.by_category.map((item) => ({
				name: item.category_display_name,
				value: item.total_cost,
				count: item.count
			}));
		}
		return stats.by_tier.map((item) => ({
			name: item.tier_display_name,
			value: item.total_cost,
			count: item.count
		}));
	}

	function updateChart() {
		if (!canvasEl) return;

		if (chartInstance) {
			chartInstance.destroy();
			chartInstance = null;
		}

		const items = currentItems();
		if (items.length === 0) return;

		chartInstance = new Chart(canvasEl.getContext('2d'), {
			type: 'bar',
			data: {
				labels: items.map((it) => it.name),
				datasets: [
					{
						data: items.map((it) => it.value),
						backgroundColor: items.map((_, i) => getColor(i)),
						borderRadius: 4,
						barPercentage: 0.7
					}
				]
			},
			options: {
				indexAxis: 'y',
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: { display: false },
					tooltip: {
						backgroundColor: 'rgba(0, 0, 0, 0.8)',
						padding: 12,
						callbacks: {
							label: (context) => {
								const item = items[context.dataIndex];
								return `${formatCurrency(item.value)} (${getPercentage(item.value)}%) · ${item.count}건`;
							}
						}
					}
				},
				scales: {
					x: {
						beginAtZero: true,
						grid: { color: 'rgba(0, 0, 0, 0.05)' },
						ticks: {
							font: { size: 11 },
							callback: (value) => {
								if (value >= 1000000) return (value / 1000000).toFixed(0) + 'M';
								if (value >= 1000) return (value / 1000).toFixed(0) + 'K';
								return value;
							}
						}
					},
					y: {
						grid: { display: false },
						ticks: { font: { size: 11 } }
					}
				}
			}
		});
	}

	$effect(() => {
		loadStatistics();
	});

	$effect(() => {
		stats;
		viewType;
		updateChart();
	});

	$effect(() => {
		return () => {
			if (chartInstance) chartInstance.destroy();
		};
	});
</script>

<div class="module-container">
	<div class="chart-header">
		<h3>
			{stats?.class_display_name || '거래'} 통계
			{#if startDate || endDate}
				<span class="date-range">
					({startDate || '시작'} ~ {endDate || '끝'})
				</span>
			{/if}
		</h3>
		<div class="view-toggle">
			<button
				class="toggle-btn"
				class:active={viewType === 'category'}
				onclick={() => (viewType = 'category')}
			>
				카테고리별
			</button>
			<button
				class="toggle-btn"
				class:active={viewType === 'tier'}
				onclick={() => (viewType = 'tier')}
			>
				분류별
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
			<p>{error}</p>
			<button class="retry-btn" onclick={loadStatistics}>다시 시도</button>
		</div>
	{:else if stats}
		<div class="chart-content">
			<div class="total-summary">
				<div class="total-info">
					<span class="total-value">{formatCurrency(stats.total_cost)}</span>
				</div>
				<div class="total-count">
					{stats.total_count}건
				</div>
			</div>

			{#if currentItems().length > 0}
				<div class="chart-container" style="height: {Math.max(currentItems().length * 40, 120)}px">
					<canvas bind:this={canvasEl}></canvas>
				</div>

				<div class="item-list">
					{#each currentItems() as item, index (item.name)}
						<div class="item-row">
							<span class="item-dot" style="background: {getColor(index)}"></span>
							<span class="item-name">{item.name}</span>
							<span class="item-count">{item.count}건</span>
							<span class="item-percent">{getPercentage(item.value)}%</span>
							<span class="item-value">{formatCurrency(item.value)}</span>
						</div>
					{/each}
				</div>
			{:else}
				<p class="no-data">
					{viewType === 'category' ? '카테고리별' : '분류별'} 데이터가 없습니다
				</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	.chart-container {
		position: relative;
		width: 100%;
	}

	.item-list {
		display: flex;
		flex-direction: column;
		gap: 6px;
		margin-top: 16px;
	}

	.item-row {
		display: grid;
		grid-template-columns: 8px 1fr auto auto auto;
		align-items: center;
		gap: 10px;
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.item-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.item-name {
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.item-count {
		white-space: nowrap;
	}

	.item-percent {
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}

	.item-value {
		white-space: nowrap;
		color: var(--text-primary);
		font-variant-numeric: tabular-nums;
	}
</style>
