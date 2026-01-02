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

<div class="section" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	{#if loading}
		<div class="loading">데이터 로딩 중...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else if stats}
		<div class="chart-header">
			<h3><a href="/asset-manager" style="text-decoration: none; color: inherit;">💵 Asset Manager</a></h3>
			<div class="header-actions">
				<button class="add-btn" onclick={openForm} title="거래 등록">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path d="M12 5v14m-7-7h14" stroke-width="2" stroke-linecap="round" />
					</svg>
					<span>거래 등록</span>
				</button>
			</div>
		</div>
		<MonthlyReport {currentYear} {currentMonth} style="border: transparent; padding: 0px;" />
	{/if}
</div>

{#if isFormOpen}
	<TransactionForm bind:isOpen={isFormOpen} onSuccess={handleFormSuccess} />
{/if}