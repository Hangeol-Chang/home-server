<script>
	import TransactionForm from '$lib/components/asset-manager/TransactionForm.svelte';
	import MonthlyReport from '$lib/components/asset-manager/MonthlyReport.svelte';
	import StatisticsChart from '$lib/components/asset-manager/StatisticsChart.svelte';
	import TransactionList from '$lib/components/asset-manager/TransactionList.svelte';
	import CalendarView from '$lib/components/asset-manager/CalendarView.svelte';
	import PeriodComparison from '$lib/components/asset-manager/PeriodComparison.svelte';
	import { getTransactions } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
	import BudgetManager from '$lib/components/asset-manager/BudgetManager.svelte';
	import BudgetComparisonChart from '$lib/components/asset-manager/BudgetComparisonChart.svelte';
	import BudgetEditor from '$lib/components/asset-manager/BudgetEditor.svelte';
	import '$lib/styles/module.css';
	import '$lib/styles/module-header.css';

	// 상태 관리
	let isFormOpen = $state(false);
	let transactions = $state([]);
	let loading = $state(true);
	let error = $state('');

	// 필터
	let selectedClass = $state(null); // null=전체, 1=지출, 2=수익, 3=저축
	let currentYear = $state(new Date().getFullYear());
	let currentMonth = $state(new Date().getMonth() + 1);

	// 예산 관리용 날짜 상태
	let budgetYear = $state(new Date().getFullYear());
	let budgetMonth = $state(new Date().getMonth() + 1);

	function changeBudgetMonth(delta) {
		const newMonth = budgetMonth + delta;
		if (newMonth > 12) {
			budgetMonth = 1;
			budgetYear += 1;
		} else if (newMonth < 1) {
			budgetMonth = 12;
			budgetYear -= 1;
		} else {
			budgetMonth = newMonth;
		}
	}

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

	// 필터 변경 시 자동 로드
	$effect(() => {
		loadTransactions();
	});
</script>

<svelte:head>
	<title>가계부 - Home Server</title>
</svelte:head>

<div class="asset-manager-page" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
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
				onclick={() => (isFormOpen = true)}
			>
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="12" y1="5" x2="12" y2="19" />
					<line x1="5" y1="12" x2="19" y2="12" />
				</svg>
				거래 등록
			</button>
		</div>
	</header>

	<!-- 거래 등록 폼 -->
	<TransactionForm bind:isOpen={isFormOpen} onSuccess={handleTransactionSuccess} />

	<!-- 월간 리포트 -->
	<MonthlyReport style="border: 1px solid var(--border-color); margin-bottom: 32px; padding: 24px;" />

	<hr>
	<button class="part-btn">
		🗓️ 월간 캘린더
	</button>
	<hr>

	<!-- 월간 캘린더 뷰 -->
	<CalendarView />

	<hr>
	<div class="part-header">
		<button class="part-btn">
			💰 예산 관리
		</button>
	</div>
	<hr>

	
	<div class="month-nav">
		<button class="nav-btn" onclick={() => changeBudgetMonth(-1)} aria-label="이전 달">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="15 18 9 12 15 6"></polyline>
			</svg>
		</button>
		<h3>📅 {budgetYear}-{String(budgetMonth).padStart(2, '0')}</h3>
		<button class="nav-btn" onclick={() => changeBudgetMonth(1)} aria-label="다음 달">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="9 18 15 12 9 6"></polyline>
			</svg>
		</button>
	</div>

	<!-- 예산 대비 지출 차트 -->
	<BudgetComparisonChart year={budgetYear} month={budgetMonth} />

	<BudgetEditor year={budgetYear} month={budgetMonth} />

	<hr>
	<button class="part-btn">
		🗓️ 기간별 통계
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
	<div class="unit-selector" style="margin: 12px;">
		{#each classTypes as classType}
			<button
				class="unit-btn"
				class:active={selectedClass === classType.id}
				style="--class-color: {classType.color}"
				onclick={() => (selectedClass = classType.id)}
			>
				<span class="class-icon">{classType.icon}</span>
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

	.class-icon {
		font-size: 16px;
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

	/* Tablet/Mobile (< 768px) */
	.asset-manager-page {
		&.tablet {
			padding: 16px;

			.part-btn {
				font-size: 1.1rem;
				padding: 6px;
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			padding: 8px;

			.part-btn {
				font-size: 1rem;
				padding: 6px;
			}
		}
	}
</style>
