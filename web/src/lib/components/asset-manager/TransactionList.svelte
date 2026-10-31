<script>
	import { deleteTransaction } from '$lib/api/asset-manager.js';
	import { device } from '$lib/stores/device';
	import TransactionTypeIcon from '$lib/components/ui/TransactionTypeIcon.svelte';

	let {
		transactions = [],
		loading = false,
		error = '',
		onReload = () => {},
		onOpenForm = () => {},
		onEditTransaction = () => {}
	} = $props();

	let hidden = $state([]);
	let categories = $derived([...new Set(transactions.map((t) => t.category_display_name))]);
	let visible = $derived(transactions.filter((t) => !hidden.includes(t.category_display_name)));
	let allChecked = $derived(categories.every((c) => !hidden.includes(c)));

	function toggleAll() {
		hidden = allChecked ? [...categories] : [];
	}

	function toggleCategory(c) {
		hidden = hidden.includes(c) ? hidden.filter((h) => h !== c) : [...hidden, c];
	}

	async function handleDelete(e, transactionId) {
		e.stopPropagation();
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

<section class="asset-manager-card transactions-section" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<div class="section-header">
		<h2>거래 내역</h2>
		<span class="transaction-count">{visible.length}건</span>
	</div>

	{#if categories.length > 0}
		<div class="category-filter">
			<label class="filter-item"><input type="checkbox" checked={allChecked} onchange={toggleAll} />전체</label>
			{#each categories as c (c)}
				<label class="filter-item">
					<input type="checkbox" checked={!hidden.includes(c)} onchange={() => toggleCategory(c)} />{c}
				</label>
			{/each}
		</div>
	{/if}

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>거래 내역을 불러오는 중...</p>
		</div>
	{:else if error}
		<div class="error">
			<p>{error}</p>
			<button class="retry-btn" onclick={onReload}>다시 시도</button>
		</div>
	{:else if transactions.length > 0}
		<div class="table-scroll-wrapper">
			<table class="data-table">
				<thead>
					<tr>
						<th class="col-icon"></th>
						<th class="col-name">항목명</th>
						<th class="col-category">분류</th>
						<th class="col-date">날짜</th>
						<th class="text-right col-amount">금액</th>
						<th class="text-center col-actions">작업</th>
					</tr>
				</thead>
				<tbody>
					{#each visible as transaction (transaction.id)}
						<tr
							class:row-earn={transaction.class_name === 'earn'}
							class:row-spend={transaction.class_name === 'spend'}
							class:row-save={transaction.class_name === 'save'}
							class="clickable-row"
							onclick={() => onEditTransaction(transaction)}
							onkeydown={(e) => e.key === 'Enter' && onEditTransaction(transaction)}
							tabindex="0"
						>
							<td class="cell-icon">
								<TransactionTypeIcon
									type={transaction.class_name === 'earn' ? 'earn' : transaction.class_name === 'spend' ? 'spend' : 'save'}
								/>
							</td>
							<td class="cell-name">
								<div class="name-wrapper">
									<span class="name">{transaction.name}</span>
									{#if transaction.description}
										<span class="description">{transaction.description}</span>
									{/if}
								</div>
							</td>
							<td class="cell-category">
								<div class="meta-wrapper">
									<span class="badge badge-class">{transaction.class_display_name}</span>
									<span class="badge badge-category">{transaction.category_display_name}</span>
									<span class="badge badge-tier">{transaction.tier_display_name}</span>
								</div>
							</td>
							<td class="cell-date">{formatDate(transaction.date)}</td>
							<td class="text-right">
								<span
									class="cell-amount"
									class:amount-earn={transaction.class_name === 'earn'}
									class:amount-spend={transaction.class_name === 'spend'}
									class:amount-save={transaction.class_name === 'save'}
								>
									{transaction.class_name === 'earn' ? '+' : '-'}{formatCurrency(transaction.cost)}
								</span>
							</td>
							<td class="text-center">
								<button
									class="icon-btn danger"
									onclick={(e) => handleDelete(e, transaction.id)}
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
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
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
		border-radius: var(--radius-md);
		font-size: 0.9rem;
		font-weight: 400;
		color: var(--text-secondary);
	}

	.category-filter {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-bottom: 16px;
	}

	.filter-item {
		position: relative;
		padding: 6px 14px;
		border-top: 1px solid var(--line);
		border-bottom: 1px solid var(--line);
		background: var(--bg-white);
		font-size: 0.85rem;
		color: var(--text-tertiary);
		cursor: pointer;
		user-select: none;
		transition:
			background-color 0.15s,
			color 0.15s,
			border-color 0.15s;
	}

	.filter-item:hover {
		border-color: var(--text-secondary);
	}

	.filter-item:has(input:checked) {
		background: var(--text-primary);
		border-color: var(--text-primary);
		color: var(--bg-white);
	}

	.filter-item:has(input:focus-visible) {
		outline: 2px solid var(--text-info);
		outline-offset: 2px;
	}

	.filter-item input {
		position: absolute;
		opacity: 0;
		pointer-events: none;
	}

	/* 테이블 스크롤 래퍼 */
	.table-scroll-wrapper {
		max-height: 600px;
		overflow-y: auto;
		overflow-x: auto;
		border: 1px solid var(--border-color);
		border-radius: var(--radius-md);
		background: var(--bg-white);
	}

	/* 테이블 헤더 고정 */
	.table-scroll-wrapper .data-table thead {
		position: sticky;
		top: 0;
		z-index: 10;
	}

	/* 컬럼 너비 조정 */
	.col-icon {
		width: 50px;
		text-align: center;
	}

	.col-name {
		min-width: 200px;
	}

	.col-category {
		min-width: 280px;
	}

	.col-date {
		width: 140px;
	}

	.col-amount {
		width: 150px;
	}

	.col-actions {
		width: 80px;
	}

	/* 셀 스타일 */
	.cell-icon {
		font-size: 1.5rem;
		text-align: center;
	}

	.cell-name .name-wrapper {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.cell-name .name {
		font-size: 1rem;
		font-weight: 400;
		color: var(--text-primary);
	}

	.cell-name .description {
		font-size: 0.85rem;
		color: var(--text-tertiary);
		font-style: italic;
	}

	.cell-category .meta-wrapper {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}

	.badge-class {
		background: var(--bg-tertiary);
		color: var(--text-secondary);
	}

	.badge-category {
		background: var(--bg-secondary);
		color: var(--text-secondary);
	}

	.badge-tier {
		background: var(--bg-primary);
		color: var(--text-secondary);
		border: 1px solid var(--border-color);
	}

	.cell-date {
		font-size: 0.9rem;
		color: var(--text-secondary);
		white-space: nowrap;
	}

	.clickable-row {
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.clickable-row:hover {
		background-color: var(--bg-tertiary) !important;
	}

	.amount-earn {
		color: var(--text-success);
	}

	.amount-spend {
		color: var(--text-danger);
	}

	.amount-save {
		color: var(--text-info);
	}
</style>
