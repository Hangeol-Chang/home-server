<script>
	import { onMount } from 'svelte';
	import { getTransactions } from '$lib/api/asset-manager.js';
	import TransactionDropdown from './TransactionDropdown.svelte';

	let { year = new Date().getFullYear(), month = new Date().getMonth() + 1 } = $props();

	let transactions = $state([]);
	let loading = $state(false);
	let error = $state(null);

	// 날짜별 거래 집계 데이터
	let dailyData = $state({});

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
			calculateDailyData();
		} catch (err) {
			console.error('Failed to load calendar data:', err);
			error = '데이터를 불러오는데 실패했습니다.';
		} finally {
			loading = false;
		}
	}

	function calculateDailyData() {
		const daily = {};

		transactions.forEach((trans) => {
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

		dailyData = daily;
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
</script>

<div class="calendar-view">
	<div class="calendar-header">
		<button class="month-nav-btn" onclick={() => changeMonth(-1)} aria-label="이전 달">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="15 18 9 12 15 6"></polyline>
			</svg>
		</button>
		<h3>📅 {year}년 {month}월</h3>
		<button class="month-nav-btn" onclick={() => changeMonth(1)} aria-label="다음 달">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="9 18 15 12 9 6"></polyline>
			</svg>
		</button>
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
			<div class="calendar-grid">
				<!-- 요일 헤더 -->
				{#each weekDays as day, index}
					<div class="calendar-weekday" class:sunday={index === 0} class:saturday={index === 6}>
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
				<div class="week-stats-header">-</div>
				{#each getCalendarDays() as week, weekIndex}
					{@const weekStats = getWeekStats(week)}
					<div class="week-stats-cell">
						<div class="week-label">{weekIndex + 1}</div>
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
	/>
</div>

<style>
	.calendar-view {
		background: white;
		border-radius: 16px;
		padding: 28px;
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
		margin-bottom: 24px;
		container-type: inline-size;
	}

	.calendar-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
		gap: 16px;
	}

	.calendar-header h3 {
		font-size: 20px;
		font-weight: 700;
		color: var(--text-primary);
		margin: 0;
		flex: 1;
		text-align: center;
	}

	.month-nav-btn {
		background: var(--bg-secondary);
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

	.month-nav-btn:hover {
		background: var(--color-medium);
		color: white;
		transform: scale(1.1);
	}

	.calendar-container {
		display: flex;
		gap: 16px;
		align-items: flex-start;
	}

	.calendar-grid {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 8px;
		flex: 1;
	}

	.calendar-weekday {
		text-align: center;
		font-weight: 600;
		font-size: 14px;
		padding: 4px 6px;
		color: var(--text-primary);
		background: var(--bg-tertiary);
		border-radius: 4px;
	}

	.calendar-weekday.sunday {
		color: #f44336;
	}

	.calendar-weekday.saturday {
		color: #2196f3;
	}

	.week-stats-column {
		width: 100px;
		display: flex;
		flex-direction: column;
		gap: 8px;
		flex-shrink: 0;
	}

	.week-stats-header {
		text-align: center;
		font-size: 14px;
		padding: 4px 6px;
		background: var(--bg-primary-dark);
		color: white;
		border-radius: 4px;
	}

	.week-stats-cell {
		background: var(--bg-tertiary);
		border-radius: 4px;
		padding: 8px;
		display: flex;
		flex-direction: column;
		gap: 6px;
		min-height: 90px;
	}

	.week-label {
		font-size: 13px;
		font-weight: 700;
		color: var(--text-primary);
		text-align: center;
		border-bottom: 1px solid var(--border-color);
	}

	.calendar-day {
		min-height: 90px;
		padding: 8px;
		border-radius: 4px;
		background: var(--bg-primary);
		display: flex;
		flex-direction: column;
		transition: all 0.2s ease;
		justify-content: center;
		align-items: center;
		position: relative;
	}

	.calendar-day.clickable {
		cursor: pointer;
	}

	.calendar-day.clickable:hover {
		background: var(--bg-secondary);
		transform: scale(1.02);
	}

	.calendar-day.clickable:focus {
		outline: 2px solid var(--color-medium);
		outline-offset: 2px;
	}

	.calendar-day.empty {
		background: transparent;
		border: none;
		cursor: default;
	}

	.calendar-day.selected {
		border: 2px solid var(--color-dark);
		background: var(--color-light);
		box-shadow: 0 4px 12px rgba(201, 124, 93, 0.3);
	}

	.calendar-day.today {
		border: 2px solid var(--border-color);
        background: var(--bg-secondary);
		box-shadow: 0 2px 8px rgba(200, 159, 156, 0.2);
	}

	.calendar-day.has-data:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.day-number {
		font-size: 16px;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 4px;
	}

	.day-amounts {
		display: flex;
		flex-direction: column;
		gap: 2px;
		flex: 1;
        width: 100%;
	}

	.amount {
		font-size: 11px;
		width: 100%;
		text-align: center;
		font-weight: 600;
		padding: 2px 4px;
		border-radius: 4px;
		overflow: hidden;
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

	/* 태블릿 */
	@media (max-width: 1024px) {
		.calendar-view {
			padding: 20px;
		}
	}

	/* 모바일 */
	@media (max-width: 768px) {
		.calendar-view {
			padding: 16px;
		}

		.calendar-grid {
			gap: 4px;
		}

		.calendar-day {
			min-height: 80px;
			padding: 4px;
			font-size: 0.85rem;
		}

		.week-stats-column {
			width: 60px;
			gap: 4px;
		}

		.week-stats-cell {
			padding: 4px 2px;
			font-size: 0.7rem;
		}

		.amount-full {
			display: none;
		}

		.amount-compact {
			display: inline;
		}
	}

	/* 모바일 소형 */
	@media (max-width: 480px) {
		.calendar-view {
			padding: 12px;
		}

		.calendar-grid {
			gap: 2px;
		}

		.calendar-day {
			min-height: 70px;
			padding: 3px;
			font-size: 0.8rem;
		}

		.week-stats-column {
			width: 50px;
			gap: 2px;
		}

		.week-stats-cell {
			padding: 3px 1px;
			font-size: 0.65rem;
		}

		.amount-compact {
			font-size: 0.75rem;
		}
	}

	@media (max-width: 768px) {
		.amount-full {
			display: none;
		}

		.amount-compact {
			display: inline;
		}
	}

	@media (max-width: 768px) {
		.calendar-view {
			padding: 16px;
		}

		.calendar-grid {
			gap: 4px;
		}

		.calendar-day {
			min-height: 80px;
			padding: 4px;
		}

        .week-stats-column {
            width: 60px;
            gap: 4px;
        }

        .week-stats-cell {
            min-height: 80px;
            padding: 4px;
        }

		.day-number {
			font-size: 14px;
		}

		.amount {
			font-size: 10px;
		}

		/* 모바일에서는 항상 compact 버전 */
		.amount-full {
			display: none;
		}

		.amount-compact {
			display: inline;
		}
	}
</style>
