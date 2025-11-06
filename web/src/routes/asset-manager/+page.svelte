<script>
	import TransactionForm from '$lib/components/asset-manager/TransactionForm.svelte';
	import MonthlyReport from '$lib/components/asset-manager/MonthlyReport.svelte';
	import StatisticsChart from '$lib/components/asset-manager/StatisticsChart.svelte';
	import TransactionList from '$lib/components/asset-manager/TransactionList.svelte';
	import PeriodComparison from '$lib/components/asset-manager/PeriodComparison.svelte';
	import { getTransactions } from '$lib/api/asset-manager.js';
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

	async function handleTransactionSuccess() {
		await loadTransactions();
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

	<hr>
	<button class="part-btn">
		🗓️기간별 통계
	</button>
	<hr>

	<!-- 기간별 비교 분석 -->
	<PeriodComparison unit="week" periods={4} />

	<hr>
	<button class="part-btn">
		📊 항목별 통계
	</button>
	<hr>
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
	<TransactionList
		{transactions}
		{loading}
		{error}
		onReload={loadTransactions}
		onOpenForm={() => (isFormOpen = true)}
	/>
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
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
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
	}

	.part-btn {
		text-decoration: none;
		width: 100%;
		background-color: var(--bg-primary);
		border: transparent;
		border-radius: 4px;
		padding: 8px;
		margin: 8px 0;
		text-align: left;
		font-size: 1.3rem;
		font-weight: 600;
		color: var(--text-primary);
		cursor: pointer;
		transition: all 0.3s;

		background: linear-gradient(to right, 
			var(--bg-secondary) 0%, var(--bg-secondary) 49%, 
			var(--bg-primary) 50%, var(--bg-primary) 100%
		);
		background-size: 200% 100%;
		background-position: right center;

		&:hover {
			background-position: left center;
			transform: translateY(-2px);
		}
	}
</style>
