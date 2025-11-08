<script>
	let {
		selectedDate = $bindable(null),
		visible = $bindable(false),
		transactions = [],
		dailyData = {}
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
		selectedDate = null;
	}

	function getTransactionsForDate() {
		if (!selectedDate) return [];
		return transactions.filter((t) => t.date === selectedDate);
	}

	function getDayData() {
		return dailyData[selectedDate] || { earn: 0, spend: 0, save: 0 };
	}
</script>

{#if visible && selectedDate}
	{@const dayTransactions = getTransactionsForDate()}
	{@const dayData = getDayData()}
	<div class="dropdown-overlay" onclick={close} role="presentation"></div>
	<div class="transaction-dropdown">
		<div class="dropdown-header">
			<h4>{selectedDate}</h4>
			<button class="close-btn" onclick={close} aria-label="닫기">✕</button>
		</div>
		<div class="dropdown-content">
			{#if dayTransactions.length === 0}
				<p class="no-transactions">거래 내역이 없습니다.</p>
			{:else}
				<div class="table-wrapper">
					<table class="data-table compact">
						<thead>
							<tr>
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
								>
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
		border-radius: 16px;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
		z-index: 999;
		width: 90%;
		max-width: 500px;
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
		font-weight: 700;
		color: var(--text-primary);
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

	.no-transactions {
		text-align: center;
		color: var(--text-secondary);
		padding: 40px 20px;
		font-size: 14px;
	}

	/* 컴포넌트별 커스텀 스타일 */
	.trans-name {
		font-size: 15px;
		font-weight: 600;
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
