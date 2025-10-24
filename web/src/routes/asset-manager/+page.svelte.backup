<script>
	import Dashboard from './dashboard.svelte';

	// 더미 거래 데이터
	const transactions = [
		{
			id: 1,
			name: '스타벅스 아메리카노',
			category: '식비',
			amount: 4500,
			type: 'expense',
			date: '2025-10-21',
			time: '14:30',
			memo: '점심 후 커피'
		},
		{
			id: 2,
			name: 'GS25 편의점',
			category: '식비',
			amount: 12000,
			type: 'expense',
			date: '2025-10-21',
			time: '09:15',
			memo: '아침식사'
		},
		{
			id: 3,
			name: '월급',
			category: '급여',
			amount: 3000000,
			type: 'income',
			date: '2025-10-20',
			time: '09:00',
			memo: '10월 급여'
		},
		{
			id: 4,
			name: '쿠팡 쇼핑',
			category: '쇼핑',
			amount: 89000,
			type: 'expense',
			date: '2025-10-19',
			time: '22:30',
			memo: '생필품 구매'
		},
		{
			id: 5,
			name: '카카오 T 택시',
			category: '교통',
			amount: 8500,
			type: 'expense',
			date: '2025-10-19',
			time: '18:20',
			memo: '퇴근 택시'
		},
		{
			id: 6,
			name: '프리랜서 수입',
			category: '부수입',
			amount: 500000,
			type: 'income',
			date: '2025-10-18',
			time: '15:00',
			memo: '사이드 프로젝트'
		}
	];

	let selectedType = $state('전체');
	let selectedCategory = $state('전체');
	
	const types = ['전체', '지출', '수입'];
	const categories = ['전체', '식비', '교통', '쇼핑', '급여', '부수입', '기타'];

	function formatCurrency(value) {
		return new Intl.NumberFormat('ko-KR').format(value) + '원';
	}

	function formatDate(dateStr) {
		const date = new Date(dateStr);
		return date.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' });
	}

	const filteredTransactions = $derived(
		transactions.filter((t) => {
			const typeMatch = selectedType === '전체' || 
				(selectedType === '지출' && t.type === 'expense') ||
				(selectedType === '수입' && t.type === 'income');
			const categoryMatch = selectedCategory === '전체' || t.category === selectedCategory;
			return typeMatch && categoryMatch;
		})
	);
</script>

<svelte:head>
	<title>가계부 - Home Server</title>
</svelte:head>

<div class="asset-manager-page">
	<header class="page-header">
		<h1>💰 가계부</h1>
		<div class="header-actions">
			<button class="add-btn income">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="12" y1="5" x2="12" y2="19" />
					<line x1="5" y1="12" x2="19" y2="12" />
				</svg>
				수입 추가
			</button>
			<button class="add-btn expense">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="12" y1="5" x2="12" y2="19" />
					<line x1="5" y1="12" x2="19" y2="12" />
				</svg>
				지출 추가
			</button>
		</div>
	</header>

	<!-- Dashboard 컴포넌트 삽입 -->
	<section class="dashboard-section">
		<Dashboard />
	</section>

	<!-- 거래 내역 -->
	<section class="transactions-section">
		<div class="section-header">
			<h2>거래 내역</h2>
			<div class="filters">
				<div class="type-filter">
					{#each types as type}
						<button
							class="filter-btn"
							class:active={selectedType === type}
							onclick={() => (selectedType = type)}
						>
							{type}
						</button>
					{/each}
				</div>
				<div class="category-filter">
					{#each categories as category}
						<button
							class="filter-btn"
							class:active={selectedCategory === category}
							onclick={() => (selectedCategory = category)}
						>
							{category}
						</button>
					{/each}
				</div>
			</div>
		</div>

		<div class="transactions-list">
			{#each filteredTransactions as transaction (transaction.id)}
				<div class="transaction-card" class:income={transaction.type === 'income'}>
					<div class="transaction-main">
						<div class="transaction-icon">
							{transaction.type === 'income' ? '💰' : '💸'}
						</div>
						<div class="transaction-info">
							<h3 class="transaction-name">{transaction.name}</h3>
							<div class="transaction-meta">
								<span class="transaction-category">{transaction.category}</span>
								<span class="transaction-date">{formatDate(transaction.date)} {transaction.time}</span>
							</div>
							{#if transaction.memo}
								<p class="transaction-memo">{transaction.memo}</p>
							{/if}
						</div>
						<div class="transaction-amount" class:income={transaction.type === 'income'}>
							{transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
						</div>
					</div>
					<div class="transaction-actions">
						<button class="icon-btn" title="수정">
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
								<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
							</svg>
						</button>
						<button class="icon-btn danger" title="삭제">
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<polyline points="3 6 5 6 21 6" />
								<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
							</svg>
						</button>
					</div>
				</div>
			{/each}
		</div>

		{#if filteredTransactions.length === 0}
			<div class="empty-state">
				<svg
					width="64"
					height="64"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
				>
					<rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
					<line x1="9" y1="9" x2="15" y2="15" />
					<line x1="15" y1="9" x2="9" y2="15" />
				</svg>
				<p>해당 카테고리에 자산이 없습니다.</p>
			</div>
		{/if}
	</section>
</div>

<style>
	.asset-manager-page {
		max-width: 1400px;
		margin: 0 auto;
		padding: 20px;
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 32px;
	}

	.page-header h1 {
		margin: 0;
		font-size: 2rem;
		color: var(--text-primary);
	}

	.header-actions {
		display: flex;
		gap: 12px;
	}

	.add-btn {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 12px 20px;
		border: none;
		border-radius: 8px;
		font-size: 0.95rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.add-btn.income {
		background: #4caf50;
		color: white;
	}

	.add-btn.income:hover {
		background: #45a049;
		transform: translateY(-2px);
		box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
	}

	.add-btn.expense {
		background: #f44336;
		color: white;
	}

	.add-btn.expense:hover {
		background: #e53935;
		transform: translateY(-2px);
		box-shadow: 0 4px 8px rgba(244, 67, 54, 0.3);
	}

	.dashboard-section {
		margin-bottom: 40px;
	}

	.transactions-section {
		margin-top: 32px;
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 24px;
		flex-wrap: wrap;
		gap: 16px;
	}

	.section-header h2 {
		margin: 0;
		font-size: 1.5rem;
		color: var(--text-primary);
	}

	.category-filter {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}

	.filter-btn {
		padding: 8px 16px;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 6px;
		color: var(--text-secondary);
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.filter-btn:hover {
		background: var(--bg-tertiary);
	}

	.filter-btn.active {
		background: var(--accent);
		color: white;
		border-color: var(--accent);
	}

	.transactions-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.transaction-card {
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-left: 4px solid #f44336;
		border-radius: 8px;
		padding: 16px 20px;
		transition: all 0.2s;
	}

	.transaction-card.income {
		border-left-color: #4caf50;
	}

	.transaction-card:hover {
		box-shadow: var(--shadow-md);
		transform: translateX(4px);
	}

	.transaction-main {
		display: flex;
		align-items: start;
		gap: 16px;
		margin-bottom: 12px;
	}

	.transaction-icon {
		font-size: 2rem;
		min-width: 40px;
		text-align: center;
	}

	.transaction-info {
		flex: 1;
	}

	.transaction-name {
		margin: 0 0 8px 0;
		font-size: 1.1rem;
		color: var(--text-primary);
	}

	.transaction-meta {
		display: flex;
		gap: 12px;
		align-items: center;
		margin-bottom: 4px;
	}

	.transaction-category {
		padding: 2px 10px;
		background: var(--bg-tertiary);
		border-radius: 12px;
		font-size: 0.8rem;
		font-weight: 500;
		color: var(--text-secondary);
	}

	.transaction-date {
		font-size: 0.85rem;
		color: var(--text-tertiary);
	}

	.transaction-memo {
		margin: 8px 0 0 0;
		font-size: 0.9rem;
		color: var(--text-tertiary);
		font-style: italic;
	}

	.transaction-amount {
		font-size: 1.5rem;
		font-weight: 700;
		color: #f44336;
		white-space: nowrap;
	}

	.transaction-amount.income {
		color: #4caf50;
	}

	.transaction-actions {
		display: flex;
		justify-content: flex-end;
		gap: 8px;
	}

	.icon-btn {
		padding: 6px;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 6px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		color: var(--text-secondary);
	}

	.icon-btn:hover {
		background: var(--bg-tertiary);
		transform: scale(1.1);
	}

	.icon-btn.danger:hover {
		background: #fee;
		border-color: #fcc;
		color: #c33;
	}

	.empty-state {
		text-align: center;
		padding: 60px 20px;
		color: var(--text-tertiary);
	}

	.empty-state svg {
		margin-bottom: 16px;
		opacity: 0.3;
	}

	.empty-state p {
		margin: 0;
		font-size: 1rem;
	}

	@media (max-width: 768px) {
		.page-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 16px;
		}

		.section-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.transactions-list {
			gap: 8px;
		}

		.transaction-card {
			padding: 12px 16px;
		}

		.transaction-main {
			gap: 12px;
		}

		.transaction-amount {
			font-size: 1.3rem;
		}
	}
</style>
