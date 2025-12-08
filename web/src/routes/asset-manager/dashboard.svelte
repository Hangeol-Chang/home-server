<script>
	import TransactionForm from '$lib/components/asset-manager/TransactionForm.svelte';
	import { getMonthlyStatistics, getTransactions, getPeriodStatistics } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	// Dashboard props
	let { compact = false } = $props();

	// 상태 관리
	let stats = $state(null);
	let recentTransactions = $state([]);
	let categoryStats = $state([]);
	let loading = $state(true);
	let error = $state('');
	let isFormOpen = $state(false);

	// 현재 년월
	const now = new Date();
	const currentYear = now.getFullYear();
	const currentMonth = now.getMonth() + 1;

	// 이번 달의 시작일과 종료일
	const startDate = `${currentYear}-${String(currentMonth).padStart(2, '0')}-01`;
	const endDate = new Date(currentYear, currentMonth, 0).toISOString().split('T')[0]; // 이번 달 마지막 날

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		loading = true;
		error = '';
		try {
			// 월별 통계와 최근 거래 내역, 지출 카테고리별 통계 가져오기
			const [monthlyStats, transactions, spendStats] = await Promise.all([
				getMonthlyStatistics(currentYear, currentMonth),
				getTransactions({
					start_date: startDate,
					end_date: endDate,
					limit: compact ? 5 : 10
				}),
				getPeriodStatistics(1, startDate, endDate) // class_id=1은 지출(spend)
			]);

			stats = monthlyStats;
			recentTransactions = transactions;
			// 지출 카테고리 통계 추출
			categoryStats = spendStats?.by_category || [];
		} catch (err) {
			console.error('대시보드 데이터 로드 실패:', err);
			error = '데이터를 불러오는데 실패했습니다.';
		} finally {
			loading = false;
		}
	}

	function formatCurrency(value) {
		return new Intl.NumberFormat('ko-KR', {
			style: 'currency',
			currency: 'KRW'
		}).format(value);
	}

	function formatDate(dateStr) {
		const date = new Date(dateStr);
		const diff = now - date;
		const hours = Math.floor(diff / (1000 * 60 * 60));
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));

		if (hours < 1) return '방금 전';
		if (hours < 24) return `${hours}시간 전`;
		if (days === 1) return '1일 전';
		if (days < 7) return `${days}일 전`;
		return date.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' });
	}

	function openForm() {
		isFormOpen = true;
	}

	async function handleFormSuccess() {
		await loadData();
	}
</script>

<div class="dashboard" class:compact>
	{#if loading}
		<div class="loading">데이터 로딩 중...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else if stats}
		<div class="dashboard-header">
			<h2>이번 달 가계부</h2>
			<div class="header-actions">
				<button class="add-transaction-btn" onclick={openForm} title="거래 등록">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path d="M12 5v14m-7-7h14" stroke-width="2" stroke-linecap="round" />
					</svg>
					{#if !compact}
						<span>거래 등록</span>
					{/if}
				</button>
				{#if compact}
					<a href="/asset-manager" class="view-more">전체보기 →</a>
				{/if}
			</div>
		</div>

		<div class="stats-grid">
			<div class="stat-card income">
				<div class="stat-label">수입</div>
				<div class="stat-value">{formatCurrency(stats.earn_total || 0)}</div>
			</div>
			<div class="stat-card expense">
				<div class="stat-label">지출</div>
				<div class="stat-value">{formatCurrency(stats.spend_total || 0)}</div>
			</div>
			<div class="stat-card highlight">
				<div class="stat-label">잔액</div>
				<div class="stat-value">{formatCurrency(stats.balance || 0)}</div>
			</div>
		</div>

		<div class="category-section">
			<h3>카테고리별 지출</h3>
			{#if categoryStats && categoryStats.length > 0}
				<div class="category-list">
					{#each categoryStats.slice(0, compact ? 3 : 5) as category}
						<div class="category-item">
							<div class="category-info">
								<span class="category-name">
									💸 {category.category_display_name}
								</span>
								<span class="category-count">{category.count}건</span>
							</div>
							<div class="category-value">
								{formatCurrency(category.total_cost)}
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<p class="no-data">카테고리 데이터가 없습니다.</p>
			{/if}
		</div>

		{#if !compact}
			<div class="recent-section">
				<h3>최근 거래</h3>
				{#if recentTransactions.length > 0}
					<div class="recent-list">
						{#each recentTransactions as transaction}
							<div class="recent-item">
								<span class="recent-name">
									{transaction.class_name === 'earn' ? '💰' : '💸'} {transaction.name || transaction.category_display_name}
								</span>
								<span class="recent-amount" class:income={transaction.class_name === 'earn'} class:expense={transaction.class_name === 'spend'}>
									{transaction.class_name === 'earn' ? '+' : '-'}{formatCurrency(transaction.cost)}
								</span>
								<span class="recent-date">{formatDate(transaction.date)}</span>
							</div>
						{/each}
					</div>
				{:else}
					<p class="no-data">최근 거래가 없습니다.</p>
				{/if}
			</div>
		{/if}
	{/if}
</div>

{#if isFormOpen}
	<TransactionForm bind:isOpen={isFormOpen} onSuccess={handleFormSuccess} />
{/if}

<style>
	.dashboard {
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 12px;
		padding: 24px;
		box-shadow: var(--shadow-md);
	}

	.dashboard.compact {
		padding: 20px;
	}

	.dashboard-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
	}

	.dashboard-header h2 {
		margin: 0;
		font-size: 1.5rem;
		color: var(--text-primary);
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.add-transaction-btn {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 16px;
		background: var(--accent);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 0.9rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}

	.add-transaction-btn:hover {
		background: var(--accent-hover);
		transform: translateY(-1px);
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
	}

	.add-transaction-btn svg {
		flex-shrink: 0;
	}

	.dashboard.compact .add-transaction-btn {
		padding: 8px;
	}

	.dashboard.compact .add-transaction-btn span {
		display: none;
	}

	.view-more {
		color: var(--accent);
		text-decoration: none;
		font-size: 0.9rem;
		font-weight: 500;
		transition: color 0.2s;
	}

	.view-more:hover {
		color: var(--accent-hover);
		text-decoration: underline;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 16px;
		margin-bottom: 24px;
	}

	.stat-card {
		background: var(--bg-secondary);
		border-radius: 8px;
		padding: 8px 12px;
		border: 1px solid var(--border-color);
		transition: transform 0.2s, box-shadow 0.2s;
	}

	.stat-card:hover {
		transform: translateY(-2px);
		box-shadow: var(--shadow-md);
	}

	.stat-card.income {
		background: #e8f5e9;
		border-color: #4caf50;
	}

	.stat-card.expense {
		background: #ffebee;
		border-color: #f44336;
	}

	.stat-card.highlight {
		background: var(--accent);
		color: white;
		border-color: var(--accent);
	}

	.stat-label {
		font-size: 0.85rem;
		opacity: 0.8;
	}

	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
	}

	.category-section,
	.recent-section {
		margin-top: 24px;
	}

	.category-section h3,
	.recent-section h3 {
		font-size: 1.1rem;
		margin-bottom: 12px;
		color: var(--text-primary);
	}

	.category-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
		max-height: 300px;
		overflow-y: auto;
		padding-right: 4px;
	}

	.category-list::-webkit-scrollbar {
		width: 6px;
	}

	.category-list::-webkit-scrollbar-track {
		background: var(--bg-secondary);
		border-radius: 3px;
	}

	.category-list::-webkit-scrollbar-thumb {
		background: var(--border-color);
		border-radius: 3px;
	}

	.category-list::-webkit-scrollbar-thumb:hover {
		background: var(--text-tertiary);
	}

	.recent-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.category-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 12px 16px;
		background: var(--bg-secondary);
		border-radius: 8px;
		border: 1px solid var(--border-color);
		transition: background 0.2s;
	}

	.category-item:hover {
		background: var(--bg-tertiary);
	}

	.category-info {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.category-name {
		font-weight: 600;
		color: var(--text-primary);
	}

	.category-count {
		font-size: 0.85rem;
		color: var(--text-tertiary);
	}

	.category-value {
		font-weight: 600;
		color: #f44336;
	}

	.recent-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px 12px;
		background: var(--bg-secondary);
		border-radius: 6px;
		font-size: 0.9rem;
		gap: 12px;
	}

	.recent-name {
		color: var(--text-primary);
		flex: 1;
	}

	.recent-amount {
		font-weight: 600;
		font-size: 0.95rem;
	}

	.recent-amount.income {
		color: #4caf50;
	}

	.recent-amount.expense {
		color: #f44336;
	}

	.recent-date {
		color: var(--text-tertiary);
		font-size: 0.85rem;
		min-width: 60px;
		text-align: right;
	}

	.no-data {
		text-align: center;
		color: var(--text-tertiary);
		padding: 20px;
		font-size: 0.9rem;
	}

	@media (max-width: 768px) {
		.stats-grid {
			grid-template-columns: 1fr;
		}

		.dashboard-header {
			flex-wrap: wrap;
		}

		.header-actions {
			flex-direction: row-reverse;
		}
	}
</style>