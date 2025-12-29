<script>
	import TransactionForm from '$lib/components/asset-manager/TransactionForm.svelte';
	import { getMonthlyStatistics } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
	import MonthlyReport from '$lib/components/asset-manager/MonthlyReport.svelte';

	// 상태 관리
	let stats = $state(null);
	let loading = $state(true);
	let error = $state('');
	let isFormOpen = $state(false);

	// 현재 년월
	const now = new Date();
	const currentYear = now.getFullYear();
	const currentMonth = now.getMonth() + 1;

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		loading = true;
		error = '';
		try {
			// 월별 통계 가져오기
			stats = await getMonthlyStatistics(currentYear, currentMonth);
		} catch (err) {
			console.error('대시보드 데이터 로드 실패:', err);
			error = '데이터를 불러오는데 실패했습니다.';
		} finally {
			loading = false;
		}
	}

	function openForm() {
		isFormOpen = true;
	}

	async function handleFormSuccess() {
		await loadData();
	}
</script>

<div class="dashboard" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	{#if loading}
		<div class="loading">데이터 로딩 중...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else if stats}
		<div class="dashboard-header">
			<h2>💵 Asset Manager</h2>
			<div class="header-actions">
				<button class="add-transaction-btn" onclick={openForm} title="거래 등록">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path d="M12 5v14m-7-7h14" stroke-width="2" stroke-linecap="round" />
					</svg>
					<span>거래 등록</span>
				</button>
			</div>
		</div>
		<MonthlyReport {currentYear} {currentMonth} />
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

	.dashboard-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0 0 12px 0;
		margin-bottom: 12px;
		border-bottom: 1px solid var(--border-color);
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

	/* Tablet/Mobile (< 768px) */
	.dashboard {
		&.tablet,
		&.mobile {
			.dashboard-header {
				flex-wrap: wrap;
			}

			.header-actions {
				flex-direction: row-reverse;
			}
		}
	}
</style>