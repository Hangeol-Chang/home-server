<script>
	import { deleteTransaction } from '$lib/api/asset-manager.js';
	import { device } from '$lib/stores/device';

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

<section class="transactions-section" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
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
		<div class="table-scroll-wrapper">
			<table class="data-table">
				<thead>
					<tr>
						<th class="col-icon"></th>
						<th class="col-name">항목명</th>
						<th class="col-category">분류</th>
						<th class="col-date">날짜</th>
						<th class="col-tags">태그</th>
						<th class="text-right col-amount">금액</th>
						<th class="text-center col-actions">작업</th>
					</tr>
				</thead>
				<tbody>
					{#each transactions as transaction (transaction.id)}
						<tr
							class:row-earn={transaction.class_name === 'earn'}
							class:row-spend={transaction.class_name === 'spend'}
							class:row-save={transaction.class_name === 'save'}
						>
							<td class="cell-icon">
								{#if transaction.class_name === 'earn'}
									💰
								{:else if transaction.class_name === 'spend'}
									💸
								{:else}
									🏦
								{/if}
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
							<td class="cell-tags">
								{#if transaction.tags && transaction.tags.length > 0}
									<div class="tags-wrapper">
										{#each transaction.tags as tag}
											<span class="tag">{tag}</span>
										{/each}
									</div>
								{/if}
							</td>
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

	/* 테이블 스크롤 래퍼 */
	.table-scroll-wrapper {
		max-height: 600px;
		overflow-y: auto;
		overflow-x: auto;
		border: 1px solid var(--border-color);
		border-radius: 8px;
		background: var(--bg-white);
	}

	/* 테이블 헤더 고정 */
	.table-scroll-wrapper .data-table thead {
		position: sticky;
		top: 0;
		z-index: 10;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
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

	.col-tags {
		min-width: 150px;
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
		font-weight: 600;
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

	.badge {
		padding: 3px 10px;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 500;
		display: inline-block;
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

	.cell-tags .tags-wrapper {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
	}

	.cell-tags .tag {
		padding: 4px 8px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-radius: 10px;
		font-size: 0.7rem;
		font-weight: 500;
	}

	.cell-amount {
		font-size: 1.2rem;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
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

	.icon-btn {
		padding: 6px;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 6px;
		cursor: pointer;
		display: inline-flex;
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



	/* Tablet/Mobile (< 768px) */
	.transactions-section {
		&.tablet {
			margin-top: 20px;

			.section-header {
				flex-direction: column;
				align-items: flex-start;
				gap: 10px;

				h2 {
					font-size: 1.2rem;
				}
			}

			.transaction-count {
				padding: 4px 12px;
				font-size: 0.85rem;
			}

			.table-scroll-wrapper {
				max-height: 450px;
				font-size: 0.85rem;
			}

			/* 테이블 컬럼 조정 */
			.col-icon {
				width: 40px;
			}

			.col-name {
				min-width: 140px;
			}

			.col-category {
				min-width: 180px;
			}

			.col-date {
				width: 120px;
				font-size: 0.8rem;
			}

			.col-tags {
				min-width: 100px;
			}

			.col-amount {
				width: 120px;
			}

			.col-actions {
				width: 60px;
			}

			.cell-icon {
				font-size: 1.2rem;
			}

			.cell-name {
				.name {
					font-size: 0.9rem;
				}

				.description {
					font-size: 0.75rem;
				}
			}

			.badge {
				padding: 2px 8px;
				font-size: 0.7rem;
			}

			.cell-tags .tag {
				padding: 3px 6px;
				font-size: 0.65rem;
			}

			.cell-amount {
				font-size: 1rem;
			}

			.icon-btn {
				padding: 5px;

				svg {
					width: 14px;
					height: 14px;
				}
			}

			.empty-state {
				padding: 40px 16px;

				svg {
					width: 48px;
					height: 48px;
				}

				p {
					font-size: 0.95rem;
				}
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			margin-top: 16px;

			.section-header h2 {
				font-size: 1.1rem;
			}

			.transaction-count {
				padding: 3px 10px;
				font-size: 0.8rem;
			}

			/* 작은 화면에서는 스크롤 가능하도록 */
			.table-scroll-wrapper {
				overflow-x: auto;
				-webkit-overflow-scrolling: touch;
				border: none;
				border-radius: 0;
				max-height: none;
			}

			.data-table {
				display: table; /* 테이블 유지 */
				min-width: 600px; /* 최소 너비 설정 */

				th {
					padding: 8px 4px;
					font-size: 0.7rem;
				}

				td {
					padding: 10px 4px;
				}
			}

			.col-icon {
				width: 35px;
			}

			.col-name {
				min-width: 120px;
			}

			.col-category {
				min-width: 150px;
			}

			.col-date {
				width: 100px;
			}

			.col-tags {
				min-width: 80px;
			}

			.col-amount {
				width: 100px;
			}

			.col-actions {
				width: 50px;
			}

			.cell-icon {
				font-size: 1.1rem;
			}

			.cell-name {
				.name {
					font-size: 0.85rem;
				}

				.description {
					font-size: 0.7rem;
				}
			}

			.badge {
				padding: 2px 6px;
				font-size: 0.65rem;
			}

			.cell-amount {
				font-size: 0.9rem;
			}

			.empty-state {
				padding: 30px 12px;

				svg {
					width: 40px;
					height: 40px;
				}
			}
		}
	}
</style>
