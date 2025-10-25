<script>
	import TransactionForm from '$lib/components/asset-manager/TransactionForm.svelte';
	import MonthlyReport from '$lib/components/asset-manager/MonthlyReport.svelte';
	import StatisticsChart from '$lib/components/asset-manager/StatisticsChart.svelte';
	import { getTransactions, deleteTransaction } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	// 상태 관리
	let isFormOpen = $state(false);
	let transactions = $state([]);
	let loading = $state(true);
	let error = $state('');

	// 필터
	let selectedClass = $state(null); // null=전체, 1=지출, 2=수익, 3=저축
	let currentYear = $state(new Date().getFullYear());
	let currentMonth = $state(new Date().getMonth() + 1);

	// 날짜 범위 계산
	const startDate = $derived(`${currentYear}-${String(currentMonth).padStart(2, '0')}-01`);
	const endDate = $derived(() => {
		const lastDay = new Date(currentYear, currentMonth, 0).getDate();
		return `${currentYear}-${String(currentMonth).padStart(2, '0')}-${lastDay}`;
	});

	const classTypes = [
		{ id: null, name: 'all', label: '전체', color: '#6366f1', icon: '📊' },
		{ id: 1, name: 'spend', label: '지출', color: '#f44336', icon: '💸' },
		{ id: 2, name: 'earn', label: '수익', color: '#4caf50', icon: '💰' },
		{ id: 3, name: 'save', label: '저축', color: '#2196f3', icon: '🏦' }
	];

	onMount(async () => {
		await loadTransactions();
	});

	async function loadTransactions() {
		loading = true;
		error = '';
		try {
			const filters = {
				start_date: startDate,
				end_date: endDate(),
				limit: 100
			};
			if (selectedClass) {
				filters.class_id = selectedClass;
			}
			transactions = await getTransactions(filters);
		} catch (err) {
			error = '거래 내역을 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	async function handleDeleteTransaction(transactionId) {
		if (!confirm('이 거래를 삭제하시겠습니까?')) return;

		try {
			await deleteTransaction(transactionId);
			await loadTransactions();
		} catch (err) {
			alert('삭제 실패: ' + err.message);
		}
	}

	async function handleTransactionSuccess() {
		await loadTransactions();
	}

	function formatCurrency(value) {
		return new Intl.NumberFormat('ko-KR').format(value) + '원';
	}

	function formatDate(dateStr) {
		const date = new Date(dateStr);
		return date.toLocaleDateString('ko-KR', {
			month: 'long',
			day: 'numeric',
			weekday: 'short'
		});
	}

	function changeMonth(delta) {
		currentMonth += delta;
		if (currentMonth > 12) {
			currentMonth = 1;
			currentYear += 1;
		} else if (currentMonth < 1) {
			currentMonth = 12;
			currentYear -= 1;
		}
	}

	// 필터 변경 시 자동 로드
	$effect(() => {
		loadTransactions();
	});
</script>

<svelte:head>
	<title>가계부 - Home Server</title>
</svelte:head>

<div class="asset-manager-page">
	<!-- 헤더 -->
	<header class="page-header">
		<h1>💰 가계부</h1>
		<div class="header-actions">
			<a href="/asset-manager/admin" class="admin-link">
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="12" cy="12" r="3"></circle>
					<path d="M12 1v6m0 6v6"></path>
					<path d="M1 12h6m6 0h6"></path>
				</svg>
				관리
			</a>
			<button
				class="add-btn"
				onclick={() => (isFormOpen = !isFormOpen)}
			>
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="12" y1="5" x2="12" y2="19" />
					<line x1="5" y1="12" x2="19" y2="12" />
				</svg>
				{isFormOpen ? '닫기' : '거래 등록'}
			</button>
		</div>
	</header>

	<!-- 거래 등록 폼 -->
	<TransactionForm bind:isOpen={isFormOpen} onSuccess={handleTransactionSuccess} />

	<!-- 월 선택 -->
	<div class="month-selector">
		<button class="month-btn" onclick={() => changeMonth(-1)} aria-label="이전 달">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="15 18 9 12 15 6"></polyline>
			</svg>
		</button>
		<h2 class="current-month">{currentYear}년 {currentMonth}월</h2>
		<button class="month-btn" onclick={() => changeMonth(1)} aria-label="다음 달">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="9 18 15 12 9 6"></polyline>
			</svg>
		</button>
	</div>

	<!-- 월간 리포트 -->
	<MonthlyReport year={currentYear} month={currentMonth} />

	<!-- 거래 분류 필터 -->
	<div class="class-filter">
		{#each classTypes as classType}
			<button
				class="filter-btn"
				class:active={selectedClass === classType.id}
				style="--class-color: {classType.color}"
				onclick={() => (selectedClass = classType.id)}
			>
				<span class="filter-icon">{classType.icon}</span>
				<span>{classType.label}</span>
			</button>
		{/each}
	</div>

	<!-- 통계 차트 (지출만) -->
	{#if selectedClass === 1}
		<StatisticsChart
			classId={1}
			startDate={startDate}
			endDate={endDate()}
		/>
	{:else if selectedClass === 2}
		<StatisticsChart
			classId={2}
			startDate={startDate}
			endDate={endDate()}
		/>
	{:else if selectedClass === 3}
		<StatisticsChart
			classId={3}
			startDate={startDate}
			endDate={endDate()}
		/>
	{/if}

	<!-- 거래 내역 리스트 -->
	<section class="transactions-section">
		<div class="section-header">
			<h2>거래 내역</h2>
			<span class="transaction-count">{transactions.length}건</span>
		</div>

		{#if loading}
			<div class="loading">
				<div class="spinner"></div>
				<p>거래 내역을 불러오는 중...</p>
			</div>
		{:else if error}
			<div class="error">
				<p>⚠️ {error}</p>
				<button class="retry-btn" onclick={loadTransactions}>다시 시도</button>
			</div>
		{:else if transactions.length > 0}
			<div class="transactions-list">
				{#each transactions as transaction (transaction.id)}
					<div
						class="transaction-card"
						class:income={transaction.class_name === 'earn'}
						class:expense={transaction.class_name === 'spend'}
						class:save={transaction.class_name === 'save'}
					>
						<div class="transaction-main">
							<div class="transaction-icon">
								{#if transaction.class_name === 'earn'}
									💰
								{:else if transaction.class_name === 'spend'}
									💸
								{:else}
									🏦
								{/if}
							</div>
							<div class="transaction-info">
								<h3 class="transaction-name">{transaction.name}</h3>
								<div class="transaction-meta">
									<span class="transaction-class">{transaction.class_display_name}</span>
									<span class="transaction-category">{transaction.category_display_name}</span>
									<span class="transaction-tier">{transaction.tier_display_name}</span>
								</div>
								<div class="transaction-date">{formatDate(transaction.date)}</div>
								{#if transaction.description}
									<p class="transaction-memo">{transaction.description}</p>
								{/if}
							</div>
							<div
								class="transaction-amount"
								class:income={transaction.class_name === 'earn'}
								class:expense={transaction.class_name === 'spend'}
								class:save={transaction.class_name === 'save'}
							>
								{transaction.class_name === 'earn' ? '+' : '-'}{formatCurrency(transaction.cost)}
							</div>
						</div>
						<div class="transaction-actions">
							<button
								class="icon-btn danger"
								onclick={() => handleDeleteTransaction(transaction.id)}
								title="삭제"
								aria-label="거래 삭제"
							>
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<polyline points="3 6 5 6 21 6" />
									<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
								</svg>
							</button>
						</div>
					</div>
				{/each}
			</div>
		{:else}
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
					<line x1="3" y1="9" x2="21" y2="9" />
				</svg>
				<p>이 기간에 거래 내역이 없습니다</p>
				<button class="cta-btn" onclick={() => (isFormOpen = true)}>
					첫 거래 등록하기
				</button>
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

	/* 페이지 특화 스타일 */
	.header-actions {
		display: flex;
		gap: 12px;
	}

	.admin-link {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 20px;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		color: var(--text-primary);
		text-decoration: none;
		font-weight: 600;
		transition: all 0.2s;
	}

	.admin-link:hover {
		background: var(--bg-tertiary);
		transform: translateY(-2px);
	}

	.month-selector {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 24px;
		margin-bottom: 32px;
		padding: 16px;
		background: var(--bg-secondary);
		border-radius: 12px;
	}

	.month-btn {
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		padding: 8px 12px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
		color: var(--text-primary);
	}

	.month-btn:hover {
		background: var(--bg-tertiary);
		transform: scale(1.1);
	}

	.current-month {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--text-primary);
		min-width: 180px;
		text-align: center;
	}

	.class-filter {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 12px;
		margin-bottom: 32px;
	}

	/* 필터 버튼 오버라이드 */
	.filter-btn {
		padding: 16px;
		font-size: 1rem;
	}

	.filter-btn.active {
		background: var(--class-color);
		color: white;
		border-color: var(--class-color);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	.filter-icon {
		font-size: 1.5rem;
	}

	.transactions-section {
		margin-top: 32px;
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
	}

	.section-header h2 {
		margin: 0;
		font-size: 1.5rem;
		color: var(--text-primary);
	}

	.transaction-count {
		padding: 6px 16px;
		background: var(--bg-secondary);
		border-radius: 20px;
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--text-secondary);
	}

	/* 거래 리스트 */
	.transactions-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.transaction-card {
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-left: 4px solid #6366f1;
		border-radius: 8px;
		padding: 16px 20px;
		transition: all 0.2s;
	}

	.transaction-card.expense {
		border-left-color: #f44336;
	}

	.transaction-card.income {
		border-left-color: #4caf50;
	}

	.transaction-card.save {
		border-left-color: #2196f3;
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
		font-weight: 600;
		color: var(--text-primary);
	}

	.transaction-meta {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
		margin-bottom: 6px;
	}

	.transaction-class,
	.transaction-category,
	.transaction-tier {
		padding: 3px 10px;
		background: var(--bg-tertiary);
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 500;
		color: var(--text-secondary);
	}

	.transaction-date {
		font-size: 0.85rem;
		color: var(--text-tertiary);
		margin-top: 4px;
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
		white-space: nowrap;
	}

	.transaction-amount.expense {
		color: #f44336;
	}

	.transaction-amount.income {
		color: #4caf50;
	}

	.transaction-amount.save {
		color: #2196f3;
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
		padding: 80px 20px;
		color: var(--text-tertiary);
	}

	.empty-state svg {
		margin-bottom: 24px;
		opacity: 0.3;
	}

	.empty-state p {
		margin: 0 0 24px 0;
		font-size: 1.1rem;
	}

	@media (max-width: 768px) {
		.header-actions {
			width: 100%;
			flex-direction: column;
		}

		.admin-link,
		.add-btn {
			width: 100%;
			justify-content: center;
		}

		.class-filter {
			grid-template-columns: 1fr 1fr;
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
			font-size: 1.2rem;
		}
	}
</style>
