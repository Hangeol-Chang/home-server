<script>
	let {
		selectedDate = $bindable(null),
		visible = $bindable(false),
		transactions = [],
		dailyData = {},
		onAddTransaction = () => {},
		onEditTransaction = () => {},
		mode = 'date', // 'date' | 'list'
		title = '' // Used in 'list' mode
	} = $props();

	function formatCurrency(value) {
		if (value === 0) return '';
		return new Intl.NumberFormat('ko-KR').format(value);
	}

	function getNetIncome(data) {
		// 순수익 = 수익 - (지출 + 저축)
		return data.earn - data.spend - data.save;
	}

	function close() {
		visible = false;
		if (mode === 'date') {
			selectedDate = null;
		}
	}

	function getTransactionsForDate() {
		if (mode === 'list') return transactions;
		if (!selectedDate) return [];
		return transactions.filter((t) => t.date === selectedDate);
	}

	function getDayData() {
		if (mode === 'list') {
			return transactions.reduce((acc, t) => {
				if (t.class_name === 'earn') acc.earn += t.cost;
				else if (t.class_name === 'spend') acc.spend += t.cost;
				else if (t.class_name === 'save') acc.save += t.cost;
				return acc;
			}, { earn: 0, spend: 0, save: 0 });
		}
		return dailyData[selectedDate] || { earn: 0, spend: 0, save: 0 };
	}
</script>

{#if visible && (selectedDate || mode === 'list')}
	{@const dayTransactions = getTransactionsForDate()}
	{@const dayData = getDayData()}
	<div class="dropdown-overlay" onclick={close} role="presentation"></div>
	<div class="transaction-dropdown">
		<div class="dropdown-header">
			<h4>{mode === 'list' ? title : selectedDate}</h4>
			<div class="header-actions">
				{#if mode === 'date'}
				<button class="add-btn" onclick={() => onAddTransaction(selectedDate)} aria-label="거래 추가" title="거래 추가">
					<svg style="position: relative;" width="28" height="28" viewBox="0 0 24 24" fill="none">
						<line x1="12" y1="5" x2="12" y2="19" stroke="white" stroke-width="2" stroke-linecap="round"/>
						<line x1="5" y1="12" x2="19" y2="12" stroke="white" stroke-width="2" stroke-linecap="round"/>
					</svg>
				</button>
				{/if}
				<button class="close-btn" onclick={close} aria-label="닫기">✕</button>
			</div>
		</div>
		<div class="dropdown-content">
			{#if dayTransactions.length === 0}
				<p class="no-transactions">거래 내역이 없습니다.</p>
			{:else}
				<div class="table-wrapper">
					<table class="data-table compact">
						<thead>
							<tr>
								<th class="col-date">날짜</th>
								<th class="col-name">항목</th>
								<th class="col-category">분류</th>
								<th class="text-right">금액</th>
							</tr>
						</thead>
						<tbody>
							{#each dayTransactions as trans}
								<tr
									class:row-spend={trans.class_name === 'spend'}
									class:row-earn={trans.class_name === 'earn'}
									class:row-save={trans.class_name === 'save'}
									class="clickable-row"
									onclick={() => onEditTransaction(trans)}
									onkeydown={(e) => e.key === 'Enter' && onEditTransaction(trans)}
									tabindex="0"
								>
									<td class="trans-date">{trans.date.slice(5)}</td>
									<td class="trans-name">{trans.name}</td>
									<td class="trans-category">{trans.category_display_name}</td>
									<td class="text-right">
										<span
											class:amount-spend={trans.class_name === 'spend' || trans.class_name === 'save'}
											class:amount-earn={trans.class_name === 'earn'}
										>
											{trans.class_name === 'earn' ? '+' : '-'}{formatCurrency(Math.abs(trans.cost))}원
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				<div class="dropdown-summary">
					<table class="data-table compact">
						<tbody>
							<tr class="row-spend">
								<td class="cell-label">
									<span class="cell-icon">💸</span>
									<span>지출</span>
								</td>
								<td class="cell-amount amount-spend text-right">-{formatCurrency(dayData.spend)}원</td>
							</tr>
							<tr class="row-earn">
								<td class="cell-label">
									<span class="cell-icon">💰</span>
									<span>수익</span>
								</td>
								<td class="cell-amount amount-earn text-right">+{formatCurrency(dayData.earn)}원</td>
							</tr>
							<tr class="row-save">
								<td class="cell-label">
									<span class="cell-icon">🏦</span>
									<span>저축</span>
								</td>
								<td class="cell-amount amount-spend text-right">-{formatCurrency(dayData.save)}원</td>
							</tr>
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	/* 드롭다운 스타일 */
	.dropdown-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.3);
		z-index: 998;
		animation: fadeIn 0.2s ease;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.transaction-dropdown {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		background: white;
		border-radius: 8px;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
		z-index: 999;
		width: 90%;
		max-width: 700px;
		max-height: 80vh;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		animation: slideUp 0.3s ease;
	}

	@keyframes slideUp {
		from {
			opacity: 0;
			transform: translate(-50%, -40%);
		}
		to {
			opacity: 1;
			transform: translate(-50%, -50%);
		}
	}

	.dropdown-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px 20px;
		border-bottom: 2px solid var(--border-color);
		background: var(--bg-secondary);
        color: var(--text-primary);
	}

	.dropdown-header h4 {
		margin: 0;
		font-size: 18px;
		font-weight: 400;
		color: var(--text-primary);
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.add-btn {
		background: var(--bg-primary-dark);
		border: none;
		border-radius: 4px;
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		color: white;
		font-size: 2rem;
		text-align: center;
		transition: all 0.2s;
		padding: 0;
	}

	.add-btn:hover {
		background: var(--accent-hover);
		transform: scale(1.1);
	}

	.close-btn {
		background: transparent;
		border: none;
		font-size: 24px;
		cursor: pointer;
		color: var(--text-secondary);
		padding: 4px 8px;
		transition: all 0.2s;
		border-radius: 4px;
		line-height: 1;
	}

	.close-btn:hover {
		background: var(--color-medium);
		color: white;
	}

	.dropdown-content {
		padding: 20px 24px;
		overflow-y: auto;
		flex: 1;
	}

	.clickable-row {
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.clickable-row:hover {
		background-color: var(--bg-tertiary) !important;
	}

	.no-transactions {
		text-align: center;
		color: var(--text-secondary);
		padding: 40px 20px;
		font-size: 14px;
	}

	/* 컴포넌트별 커스텀 스타일 */
	.trans-date {
		font-size: 13px;
		color: var(--text-secondary);
		white-space: nowrap;
	}

	.trans-name {
		font-size: 15px;
		font-weight: 400;
		color: var(--text-primary);
	}

	.trans-category {
		font-size: 13px;
		color: var(--text-secondary);
	}

	.dropdown-summary {
		border-top: 2px solid var(--border-color);
		padding-top: 16px;
	}

	.cell-icon {
		font-size: 1.1rem;
	}

	.cell-amount {
		font-size: 1.1rem;
	}
</style>
