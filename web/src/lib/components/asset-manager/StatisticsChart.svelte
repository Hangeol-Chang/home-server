<script>
	import { getPeriodStatistics } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	let {
		classId = 1,
		startDate = null,
		endDate = null
	} = $props();

	let stats = $state(null);
	let loading = $state(true);
	let error = $state('');
	let viewType = $state('category'); // 'category' 또는 'tier'

	onMount(async () => {
		await loadStatistics();
	});

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

	$effect(() => {
		loadStatistics();
	});
</script>

<div class="statistics-chart">
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
			<p>⚠️ {error}</p>
			<button class="retry-btn" onclick={loadStatistics}>다시 시도</button>
		</div>
	{:else if stats}
		<div class="chart-content">
			<!-- 총 합계 -->
			<div class="total-summary">
				<div class="total-info">
					<span class="total-label">총 {stats.class_display_name}</span>
					<span class="total-value">{formatCurrency(stats.total_cost)}</span>
				</div>
				<div class="total-count">
					{stats.total_count}건
				</div>
			</div>

			{#if viewType === 'category'}
				<!-- 카테고리별 차트 -->
				{#if stats.by_category.length > 0}
					<div class="bar-chart">
						{#each stats.by_category as item, index}
							<div class="bar-item">
								<div class="bar-info">
									<span class="bar-name">{item.category_display_name}</span>
									<span class="bar-value">{formatCurrency(item.total_cost)}</span>
								</div>
								<div class="bar-wrapper">
									<div
										class="bar-fill"
										style="width: {getPercentage(item.total_cost)}%; background: {getColor(index)}"
									>
										<span class="bar-percentage">{getPercentage(item.total_cost)}%</span>
									</div>
								</div>
								<div class="bar-count">{item.count}건</div>
							</div>
						{/each}
					</div>
				{:else}
					<p class="no-data">카테고리별 데이터가 없습니다</p>
				{/if}
			{:else}
				<!-- 티어별 차트 -->
				{#if stats.by_tier.length > 0}
					<div class="bar-chart">
						{#each stats.by_tier as item, index}
							<div class="bar-item">
								<div class="bar-info">
									<span class="bar-name">{item.tier_display_name}</span>
									<span class="bar-value">{formatCurrency(item.total_cost)}</span>
								</div>
								<div class="bar-wrapper">
									<div
										class="bar-fill"
										style="width: {getPercentage(item.total_cost)}%; background: {getColor(index)}"
									>
										<span class="bar-percentage">{getPercentage(item.total_cost)}%</span>
									</div>
								</div>
								<div class="bar-count">{item.count}건</div>
							</div>
						{/each}
					</div>
				{:else}
					<p class="no-data">분류별 데이터가 없습니다</p>
				{/if}
			{/if}
		</div>
	{/if}
</div>

<style>
	.statistics-chart {
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 12px;
		padding: 24px;
		margin-bottom: 32px;
	}

	.chart-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 24px;
		flex-wrap: wrap;
		gap: 16px;
	}

	.chart-header h3 {
		margin: 0;
		font-size: 1.3rem;
		color: var(--text-primary);
	}

	.date-range {
		font-size: 0.85rem;
		color: var(--text-tertiary);
		font-weight: normal;
	}

	.view-toggle {
		display: flex;
		gap: 8px;
		background: var(--bg-secondary);
		padding: 4px;
		border-radius: 8px;
	}

	.toggle-btn {
		padding: 8px 16px;
		background: transparent;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--text-secondary);
		transition: all 0.2s;
	}

	.toggle-btn:hover {
		background: var(--bg-tertiary);
	}

	.toggle-btn.active {
		background: var(--accent);
		color: white;
	}

	/* 차트 레이아웃 */
	.chart-content {
		margin-top: 20px;
	}

	.total-summary {
		display: flex;
		justify-content: space-between;
		align-items: center;
		background: var(--bg-secondary);
		padding: 20px;
		border-radius: 10px;
		margin-bottom: 24px;
		border: 2px solid var(--accent);
	}

	.total-info {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.total-label {
		font-size: 0.95rem;
		color: var(--text-secondary);
		font-weight: 600;
	}

	.total-value {
		font-size: 2rem;
		font-weight: 700;
		color: var(--accent);
	}

	.total-count {
		font-size: 1.1rem;
		color: var(--text-secondary);
		padding: 8px 16px;
		background: var(--bg-primary);
		border-radius: 8px;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.bar-item {
		display: grid;
		grid-template-columns: 1fr 3fr auto;
		gap: 16px;
		align-items: center;
	}

	.bar-info {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.bar-name {
		font-size: 0.95rem;
		font-weight: 600;
		color: var(--text-primary);
	}

	.bar-value {
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.bar-wrapper {
		background: var(--bg-secondary);
		border-radius: 8px;
		height: 36px;
		overflow: hidden;
		position: relative;
	}

	.bar-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding-right: 12px;
		transition: width 0.5s ease-out;
		min-width: 60px;
	}

	.bar-percentage {
		color: white;
		font-weight: 600;
		font-size: 0.85rem;
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
	}

	.bar-count {
		font-size: 0.9rem;
		color: var(--text-tertiary);
		white-space: nowrap;
	}

	.no-data {
		text-align: center;
		padding: 40px;
		color: var(--text-tertiary);
	}

	@media (max-width: 768px) {
		.chart-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.bar-item {
			grid-template-columns: 1fr;
			gap: 8px;
		}

		.bar-info {
			flex-direction: row;
			justify-content: space-between;
		}

		.bar-count {
			text-align: right;
			margin-top: 4px;
		}

		.total-summary {
			flex-direction: column;
			gap: 16px;
			align-items: flex-start;
		}

		.total-value {
			font-size: 1.5rem;
		}
	}
</style>
