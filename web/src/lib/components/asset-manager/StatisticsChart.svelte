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
			<p>⚠️ {error}</p>
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
	/* 추가적인 커스텀 스타일이 필요한 경우 여기에 작성 */
</style>
