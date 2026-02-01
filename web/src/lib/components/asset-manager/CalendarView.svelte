<script>
	import { onMount } from 'svelte';
	import { getTransactions } from '$lib/api/asset-manager.js';
	import TransactionDropdown from './TransactionDropdown.svelte';
	import TransactionForm from './TransactionForm.svelte';
	import { device } from '$lib/stores/device';
	import '$lib/styles/module.css';

	let { year = new Date().getFullYear(), month = new Date().getMonth() + 1 } = $props();

	let transactions = $state([]);
	let loading = $state(false);
	let error = $state(null);

	// 거래 등록 폼 상태
	let isFormOpen = $state(false);
	let formDate = $state(null);

	// 티어 필터 상태 (name -> boolean, true=visible)
	let tierFilters = $state({});

	// 현재 데이터에 존재하는 티어 목록
	let availableTiers = $derived.by(() => {
		const tiers = new Map();
		transactions.forEach((t) => {
			if (t.tier_display_name && !tiers.has(t.tier_display_name)) {
				tiers.set(t.tier_display_name, {
					name: t.tier_display_name,
					level: t.tier_level
				});
			}
		});
		return Array.from(tiers.values()).sort((a, b) => a.level - b.level);
	});

	// 날짜별 거래 집계 데이터
	let dailyData = $derived.by(() => {
		const daily = {};

		transactions.forEach((trans) => {
			// 티어 필터링 (undefined면 true로 취급)
			if (tierFilters[trans.tier_display_name] === false) return;

			const date = trans.date;
			if (!daily[date]) {
				daily[date] = {
					earn: 0, // 수익
					spend: 0, // 지출
					save: 0 // 저축
				};
			}

			if (trans.class_name === 'earn') {
				daily[date].earn += Math.abs(trans.cost);
			} else if (trans.class_name === 'spend') {
				daily[date].spend += Math.abs(trans.cost);
			} else if (trans.class_name === 'save') {
				daily[date].save += Math.abs(trans.cost);
			}
		});

		return daily;
	});

	function toggleTierFilter(name) {
		// 현재 상태가 false이면 true로, undefined나 true이면 false로
		const current = tierFilters[name] !== false;
		tierFilters = { ...tierFilters, [name]: !current };
	}

	let monthlyStats = $derived.by(() => {
		let earn = 0;
		let spend = 0;
		let save = 0;

		Object.values(dailyData).forEach((day) => {
			earn += day.earn;
			spend += day.spend;
			save += day.save;
		});

		return { earn, spend, save };
	});

	// 선택된 날짜 및 드롭다운 상태
	let selectedDate = $state(null);
	let dropdownVisible = $state(false);

	const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

	onMount(() => {
		loadData();
	});

	$effect(() => {
		// year, month가 변경되면 데이터 재로드
		loadData();
	});

	async function loadData() {
		loading = true;
		error = null;

		try {
			const startDate = `${year}-${String(month).padStart(2, '0')}-01`;
			const lastDay = new Date(year, month, 0).getDate();
			const endDate = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;

			const data = await getTransactions({
				start_date: startDate,
				end_date: endDate,
				limit: 1000
			});

			transactions = data;
		} catch (err) {
			console.error('Failed to load calendar data:', err);
			error = '데이터를 불러오는데 실패했습니다.';
		} finally {
			loading = false;
		}
	}

	function getCalendarDays() {
		const firstDay = new Date(year, month - 1, 1);
		const lastDay = new Date(year, month, 0).getDate();
		const startWeekday = firstDay.getDay(); // 0=일요일, 6=토요일

		const days = [];
		const weeks = [];
		let currentWeek = [];

		// 이전 달 빈 칸
		for (let i = 0; i < startWeekday; i++) {
			currentWeek.push(null);
		}

		// 현재 달 날짜
		for (let day = 1; day <= lastDay; day++) {
			const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
			currentWeek.push({
				day,
				date: dateStr,
				data: dailyData[dateStr] || { earn: 0, spend: 0, save: 0 }
			});

			// 토요일이면 주 완성
			if (currentWeek.length === 7) {
				weeks.push(currentWeek);
				currentWeek = [];
			}
		}

		// 마지막 주 처리
		if (currentWeek.length > 0) {
			// 남은 빈 칸 채우기
			while (currentWeek.length < 7) {
				currentWeek.push(null);
			}
			weeks.push(currentWeek);
		}

		return weeks;
	}

	function getWeekStats(week) {
		let earn = 0;
		let spend = 0;
		let save = 0;

		week.forEach((dayInfo) => {
			if (dayInfo && dayInfo.data) {
				earn += dayInfo.data.earn;
				spend += dayInfo.data.spend;
				save += dayInfo.data.save;
			}
		});

		return { earn, spend, save, net: earn - spend - save };
	}

	function formatCurrency(value) {
		if (value === 0) return '';
		return new Intl.NumberFormat('ko-KR').format(value);
	}

	function formatCurrencyCompact(value) {
		if (value === 0) return '';
		// 만원 단위로 변환하고 소수점 1자리까지 표시
		const inManwon = value / 10000;
		if (Math.abs(inManwon) >= 1) {
			return inManwon.toFixed(1);
		}
		// 1만원 미만이면 그냥 천원 단위로 표시
		return (value / 1000).toFixed(0);
	}

	function changeMonth(delta) {
		const newMonth = month + delta;
		if (newMonth > 12) {
			month = 1;
			year = year + 1;
		} else if (newMonth < 1) {
			month = 12;
			year = year - 1;
		} else {
			month = newMonth;
		}
	}

	function getNetIncome(data) {
		// 순수익 = 수익 - (지출 + 저축)
		return data.earn - data.spend - data.save;
	}

	function isToday(dateStr) {
		const today = new Date();
		const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
		return dateStr === todayStr;
	}

	function handleDayClick(dateStr) {
		if (selectedDate === dateStr && dropdownVisible) {
			// 같은 날짜를 다시 클릭하면 닫기
			dropdownVisible = false;
			selectedDate = null;
		} else {
			// 새로운 날짜 선택
			selectedDate = dateStr;
			dropdownVisible = true;
		}
	}

	function handleAddTransaction(date) {
		formDate = date;
		isFormOpen = true;
		// 드롭다운은 닫기
		dropdownVisible = false;
	}

	async function handleFormSuccess() {
		await loadData();
	}
</script>

<div class="module-container" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<div class="chart-header">
		<div class="month-nav">
			<button class="nav-btn" onclick={() => changeMonth(-1)} aria-label="이전 달">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="15 18 9 12 15 6"></polyline>
				</svg>
			</button>
			<h3>📅 {year}-{month}</h3>
			<button class="nav-btn" onclick={() => changeMonth(1)} aria-label="다음 달">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="9 18 15 12 9 6"></polyline>
				</svg>
			</button>
		</div>
		<div class="filters">
			{#each availableTiers as tier}
				<button 
					class="filter-chip" 
					class:active={tierFilters[tier.name] !== false}
					onclick={() => toggleTierFilter(tier.name)}
					aria-pressed={tierFilters[tier.name] !== false}
				>
					<span class="check-icon">
						{#if tierFilters[tier.name] !== false}
							<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
								<polyline points="20 6 9 17 4 12"></polyline>
							</svg>
						{/if}
					</span>
					{tier.name}
				</button>
			{/each}
		</div>
	</div>

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>데이터를 불러오는 중...</p>
		</div>
	{:else if error}
		<div class="error">
			<p>⚠️ {error}</p>
		</div>
	{:else}
		<div class="calendar-container">
			<div class="calendar-grid" style="flex-grow: 1;">
				<!-- 요일 헤더 -->
				{#each weekDays as day, index}
					<div class="calendar-weekday" style="height: 60px;" class:sunday={index === 0} class:saturday={index === 6}>
						{day}
					</div>
				{/each}

				<!-- 주별 날짜 셀 -->
				{#each getCalendarDays() as week, weekIndex}
					{#each week as dayInfo}
						{#if dayInfo === null}
							<div class="calendar-day empty"></div>
						{:else}
							<div
								class="calendar-day clickable"
								class:today={isToday(dayInfo.date)}
								class:has-data={dayInfo.data.earn > 0 || dayInfo.data.spend > 0 || dayInfo.data.save > 0}
								class:selected={selectedDate === dayInfo.date}
								onclick={() => handleDayClick(dayInfo.date)}
								onkeydown={(e) => e.key === 'Enter' && handleDayClick(dayInfo.date)}
								role="button"
								tabindex="0"
							>
								<div class="day-number">{dayInfo.day}</div>
								<div class="day-amounts">
									{#if dayInfo.data.spend > 0 || dayInfo.data.save > 0}
										<div class="amount spend">
											<span class="amount-full">-{formatCurrency(dayInfo.data.spend + dayInfo.data.save)}</span>
											<span class="amount-compact">-{formatCurrencyCompact(dayInfo.data.spend + dayInfo.data.save)}</span>
										</div>
									{/if}
									{#if dayInfo.data.earn > 0}
										<div class="amount earn">
											<span class="amount-full">+{formatCurrency(dayInfo.data.earn)}</span>
											<span class="amount-compact">+{formatCurrencyCompact(dayInfo.data.earn)}</span>
										</div>
									{/if}
								</div>
							</div>
						{/if}
					{/each}
				{/each}
			</div>

			<!-- 주간 통계 -->
			<div class="week-stats-column">
				<div class="calendar-weekday" style="height: 60px; padding: 0px;">
					{#if monthlyStats.spend > 0 || monthlyStats.save > 0}
						<div class="amount spend">
							<span class="amount-full">-{formatCurrency(monthlyStats.spend + monthlyStats.save)}</span>
							<span class="amount-compact">-{formatCurrencyCompact(monthlyStats.spend + monthlyStats.save)}</span>
						</div>
					{/if}
					{#if monthlyStats.earn > 0}
						<div class="amount earn">
							<span class="amount-full">+{formatCurrency(monthlyStats.earn)}</span>
							<span class="amount-compact">+{formatCurrencyCompact(monthlyStats.earn)}</span>
						</div>
					{/if}
					{#if monthlyStats.earn === 0 && monthlyStats.spend === 0 && monthlyStats.save === 0}
						-
					{/if}
				</div>
				{#each getCalendarDays() as week, weekIndex}
					{@const weekStats = getWeekStats(week)}
					<div class="calendar-day" style="border-bottom: 1px solid var(--border-color);">
						<div class="day-number">{weekIndex + 1}</div>
						<div class="day-amounts">
							{#if weekStats.spend > 0 || weekStats.save > 0}
								<div class="amount spend">
									<span class="amount-full">-{formatCurrency(weekStats.spend + weekStats.save)}</span>
									<span class="amount-compact">-{formatCurrencyCompact(weekStats.spend + weekStats.save)}</span>
								</div>
								{/if}
							{#if weekStats.earn > 0}
								<div class="amount earn">
									<span class="amount-full">+{formatCurrency(weekStats.earn)}</span>
									<span class="amount-compact">+{formatCurrencyCompact(weekStats.earn)}</span>
								</div>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- 거래 내역 드롭다운 -->
	<TransactionDropdown
		bind:selectedDate
		bind:visible={dropdownVisible}
		{transactions}
		{dailyData}
		onAddTransaction={handleAddTransaction}
	/>
</div>

{#if isFormOpen}
	<TransactionForm 
		bind:isOpen={isFormOpen} 
		initialDate={formDate}
		onSuccess={handleFormSuccess} 
	/>
{/if}

<style>
	/* 1. 월간 캘린더 네비게이션 (Schedule Manager와 동일) */
	.month-nav {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.month-nav h3 {
		margin: 0;
		min-width: 140px;
		text-align: center;
	}

	.month-nav .nav-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border: 1px solid var(--border-color);
		border-radius: 4px;
		background: var(--bg-secondary);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all 0.2s;
	}

	.month-nav .nav-btn:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
	}

    /* 2. Asset Manager 전용 필터 스타일 */
	.filters {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}

	.filter-chip {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 4px 12px;
		border-radius: 8px;
		border: transparent 1px solid;
		background: var(--bg-primary);
		color: var(--text-primary);
		font-size: 0.8rem;
		font-weight: 300;
		cursor: pointer;
		transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
		user-select: none;
	}

	.filter-chip:hover {
		background: var(--bg-primary);
		transform: translateY(-1px);
	}

	.filter-chip.active {
		background: var(--bg-primary);
		color: var(--text-primary);
		border-color: var(--color-main-4);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		padding-left: 12px;
	}

	.check-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 14px;
		height: 14px;
	}

	.calendar-container {
		display: flex;
		gap: 12px;
		align-items: flex-start;
	}

	.week-stats-column {
		width: 100px;
		display: flex;
		flex-direction: column;
		gap: 0; 
		flex-shrink: 0;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        overflow: hidden;
        background: var(--bg-secondary);
	}

	.calendar-day.clickable {
		cursor: pointer;
	}
    
    .calendar-day.clickable:hover {
        background: var(--bg-secondary);
    }
    
    .calendar-day.selected {
        border: 2px solid var(--color-dark); /* Keep explicit border for selection */
    }

    /* 4. 데이터 표시 (Amounts) */
	.day-amounts {
		display: flex;
		flex-direction: column;
		gap: 2px;
		flex: 1;
        width: 100%;
        justify-content: flex-start;
	}

	.amount {
		font-size: 11px;
		width: calc(100% - 8px);
		text-align: center;
		font-weight: 400;
		padding: 2px 4px;
		border-radius: 4px;
		overflow: hidden;
		margin: 2px 4px;
	}

	.amount-full {
		display: inline;
	}

	.amount-compact {
		display: none;
	}

	.amount.earn {
		color: #4caf50;
		background: rgba(76, 175, 80, 0.1);
	}

	.amount.spend {
		color: #f44336;
		background: rgba(244, 67, 54, 0.1);
	}

    /* Media Queries matching module-calendar.css breakpoints */
    @media (max-width: 768px) {
        .week-stats-column {
            width: 60px;
        }

        .amount-full {
            display: none;
        }

        .amount-compact {
            display: inline;
        }
        
        .amount {
            font-size: 10px;
        }
    }
</style>
