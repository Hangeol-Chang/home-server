<script>
	import { deleteTransaction } from '$lib/api/asset-manager.js';

	let {
		transactions = [],
		loading = false,
		error = '',
		onReload = () => {},
		onOpenForm = () => {}
	} = $props();

	async function handleDelete(transactionId) {
		if (!confirm('이 거래를 삭제하시겠습니까?')) return;

		try {
			await deleteTransaction(transactionId);
			onReload();
		} catch (err) {
			alert('삭제 실패: ' + err.message);
		}
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
</script>

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
			<button class="retry-btn" onclick={onReload}>다시 시도</button>
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
							onclick={() => handleDelete(transaction.id)}
							title="삭제"
							aria-label="거래 삭제"
						>
							<svg
								width="16"
								height="16"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
							>
								<polyline points="3 6 5 6 21 6" />
								<path
									d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
								/>
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
			<button class="btn-primary" onclick={onOpenForm}>첫 거래 등록하기</button>
		</div>
	{/if}
</section>

<style>
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

	@media (max-width: 768px) {
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
