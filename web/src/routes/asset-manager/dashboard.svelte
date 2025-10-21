<script>
	// Dashboard props
	let { compact = false } = $props();

	// 더미 데이터 (나중에 API로 교체)
	const stats = {
		thisMonthIncome: 3500000,
		thisMonthExpense: 2100000,
		balance: 1400000,
		categories: [
			{ name: '식비', count: 24, amount: 450000, type: 'expense' },
			{ name: '교통비', count: 18, amount: 120000, type: 'expense' },
			{ name: '월급', count: 1, amount: 3000000, type: 'income' },
			{ name: '쇼핑', count: 8, amount: 380000, type: 'expense' }
		]
	};

	function formatCurrency(value) {
		return new Intl.NumberFormat('ko-KR', {
			style: 'currency',
			currency: 'KRW'
		}).format(value);
	}

	const totalExpense = $derived(
		stats.categories.filter((c) => c.type === 'expense').reduce((sum, c) => sum + c.amount, 0)
	);
	const totalIncome = $derived(
		stats.categories.filter((c) => c.type === 'income').reduce((sum, c) => sum + c.amount, 0)
	);
</script>

<div class="dashboard" class:compact>
	<div class="dashboard-header">
		<h2>이번 달 가계부</h2>
		{#if compact}
			<a href="/asset-manager" class="view-more">전체보기 →</a>
		{/if}
	</div>

	<div class="stats-grid">
		<div class="stat-card income">
			<div class="stat-label">수입</div>
			<div class="stat-value">{formatCurrency(stats.thisMonthIncome)}</div>
		</div>
		<div class="stat-card expense">
			<div class="stat-label">지출</div>
			<div class="stat-value">{formatCurrency(stats.thisMonthExpense)}</div>
		</div>
		<div class="stat-card highlight">
			<div class="stat-label">잔액</div>
			<div class="stat-value">{formatCurrency(stats.balance)}</div>
		</div>
	</div>

	<div class="category-section">
		<h3>카테고리별 내역</h3>
		<div class="category-list">
			{#each stats.categories as category}
				<div class="category-item" class:income={category.type === 'income'}>
					<div class="category-info">
						<span class="category-name">
							{category.type === 'income' ? '💰' : '💸'} {category.name}
						</span>
						<span class="category-count">{category.count}건</span>
					</div>
					<div class="category-value" class:income={category.type === 'income'}>
						{category.type === 'income' ? '+' : '-'}{formatCurrency(category.amount)}
					</div>
				</div>
			{/each}
		</div>
	</div>

	{#if !compact}
		<div class="recent-section">
			<h3>최근 거래</h3>
			<div class="recent-list">
				<div class="recent-item">
					<span class="recent-name">💸 스타벅스</span>
					<span class="recent-amount expense">-5,800원</span>
					<span class="recent-date">2시간 전</span>
				</div>
				<div class="recent-item">
					<span class="recent-name">💸 GS25 편의점</span>
					<span class="recent-amount expense">-12,000원</span>
					<span class="recent-date">5시간 전</span>
				</div>
				<div class="recent-item">
					<span class="recent-name">💰 월급</span>
					<span class="recent-amount income">+3,000,000원</span>
					<span class="recent-date">1일 전</span>
				</div>
			</div>
		</div>
	{/if}
</div>

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
		padding: 20px;
		border-radius: 8px;
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
		margin-bottom: 8px;
	}

	.stat-value {
		font-size: 1.8rem;
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

	.category-list,
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

	.category-item.income {
		background: #f1f8f4;
		border-left: 3px solid #4caf50;
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

	.category-value.income {
		color: #4caf50;
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

	@media (max-width: 768px) {
		.stats-grid {
			grid-template-columns: 1fr;
		}
	}
</style>