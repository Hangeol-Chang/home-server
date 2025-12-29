<script>
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';

	let { year = new Date().getFullYear(), month = new Date().getMonth() + 1 } = $props();

	let schedules = $state([]);
	let loading = $state(false);
	let error = $state(null);

	const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

	onMount(() => {
		loadData();
	});

	$effect(() => {
		loadData();
	});

	async function loadData() {
		loading = true;
		// TODO: Load actual schedule data
		// Mock data for now
		schedules = []; 
		loading = false;
	}

	function getCalendarDays() {
		const firstDay = new Date(year, month - 1, 1);
		const lastDay = new Date(year, month, 0).getDate();
		const startWeekday = firstDay.getDay();

		const days = [];
		const weeks = [];
		let currentWeek = [];

		// Empty slots for previous month
		for (let i = 0; i < startWeekday; i++) {
			currentWeek.push(null);
		}

		// Days of current month
		for (let day = 1; day <= lastDay; day++) {
			const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
			currentWeek.push({
				day,
				date: dateStr,
				schedules: schedules.filter(s => s.date === dateStr)
			});

			if (currentWeek.length === 7) {
				weeks.push(currentWeek);
				currentWeek = [];
			}
		}

		// Empty slots for next month
		if (currentWeek.length > 0) {
			while (currentWeek.length < 7) {
				currentWeek.push(null);
			}
			weeks.push(currentWeek);
		}

		return weeks;
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

	function isToday(dateStr) {
		const today = new Date();
		const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
		return dateStr === todayStr;
	}
</script>

<div class="calendar-view" class:mobile={$device.isMobile}>
	<div class="chart-header">
		<div class="month-nav">
			<button class="nav-btn" onclick={() => changeMonth(-1)} aria-label="이전 달">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="15 18 9 12 15 6"></polyline>
				</svg>
			</button>
			<h3>📅 {year}-{String(month).padStart(2, '0')}</h3>
			<button class="nav-btn" onclick={() => changeMonth(1)} aria-label="다음 달">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="9 18 15 12 9 6"></polyline>
				</svg>
			</button>
		</div>
	</div>

	<div class="calendar-container">
		<div class="calendar-grid">
			<!-- Weekday Headers -->
			{#each weekDays as day, index}
				<div class="calendar-weekday" class:sunday={index === 0} class:saturday={index === 6}>
					{day}
				</div>
			{/each}

			<!-- Calendar Days -->
			{#each getCalendarDays() as week}
				{#each week as dayInfo}
					{#if dayInfo === null}
						<div class="calendar-day empty"></div>
					{:else}
						<div
							class="calendar-day"
							class:today={isToday(dayInfo.date)}
						>
							<div class="day-number">{dayInfo.day}</div>
							<div class="day-content">
								<!-- Schedule items will go here -->
							</div>
						</div>
					{/if}
				{/each}
			{/each}
		</div>
	</div>
</div>

<style>
	.calendar-view {
		background: white;
		border-radius: 16px;
		padding: 24px;
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
		margin-bottom: 24px;
	}
    
	.calendar-grid {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 8px;
	}

	.calendar-weekday {
		text-align: center;
		font-weight: 600;
		padding: 8px;
		color: var(--text-secondary);
	}

	.calendar-weekday.sunday { color: #f44336; }
	.calendar-weekday.saturday { color: #2196f3; }

	.calendar-day {
		min-height: 100px;
		padding: 8px;
		border-radius: 8px;
		background: var(--bg-primary);
		border: 1px solid transparent;
	}

	.calendar-day.today {
		border-color: var(--accent);
		background: var(--bg-secondary);
	}

	.calendar-day.empty {
		background: transparent;
	}

	.day-number {
		font-weight: 600;
		margin-bottom: 4px;
	}

	/* Mobile styles */
	.calendar-view.mobile {
		padding: 12px;
	}

	.calendar-view.mobile .calendar-day {
		min-height: 60px;
		padding: 4px;
		font-size: 0.9rem;
	}
</style>
