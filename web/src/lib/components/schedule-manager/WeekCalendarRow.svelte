<script>
	import { device } from '$lib/stores/device';
	import { getGoogleEventsForWeek } from '$lib/api/schedule-manager.js';
	import ScheduleDetailModal from './ScheduleDetailModal.svelte';
	let { style = '' } = $props();

	let loading = $state(false);

	// Modal State
	let showModal = $state(false);
	let selectedSchedule = $state(null);

	// 현재 표시 중인 주의 기준 날짜 (해당 주의 일요일)
	let weekOffset = $state(0);

	const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

	// 특정 주의 날짜 계산 (일요일 시작)
	function getWeekDates(offset = 0) {
		const today = new Date();
		const dayOfWeek = today.getDay();
		const sunday = new Date(today);
		sunday.setDate(today.getDate() - dayOfWeek + offset * 7);

		const weekDates = [];
		for (let i = 0; i < 7; i++) {
			const d = new Date(sunday);
			d.setDate(sunday.getDate() + i);
			weekDates.push({
				day: d.getDate(),
				date: d.toISOString().split('T')[0],
				dayOfWeek: i,
				month: d.getMonth() + 1,
				year: d.getFullYear(),
				slots: []
			});
		}
		return weekDates;
	}

	let weekDates = $state(getWeekDates(0));

	// 주가 변경될 때마다 날짜와 데이터 갱신
	$effect(() => {
		const offset = weekOffset; // weekOffset만 추적
		const newDates = getWeekDates(offset);
		loadDataForWeek(newDates);
	});

	async function loadDataForWeek(dates) {
		loading = true;
		try {
			const startDate = dates[0].date;
			const endDate = dates[6].date;
			const fetchedSchedules = await getGoogleEventsForWeek(startDate, endDate);
			weekDates = assignSchedulesToSlots(dates, fetchedSchedules);
		} catch (err) {
			console.error('Failed to load schedules:', err);
			weekDates = dates;
		}
		loading = false;
	}

	function assignSchedulesToSlots(dates, scheduleList) {
		// 슬롯 초기화 - 새 배열로 복사해서 작업
		const updatedDates = dates.map((d) => ({ ...d, slots: [] }));

		const weekStart = updatedDates[0].date;
		const weekEnd = updatedDates[6].date;

		// 이번 주에 표시해야 할 일정 필터링
		const weekSchedules = scheduleList.filter((s) => {
			return s.end_date >= weekStart && s.start_date <= weekEnd;
		});

		// 일정 정렬 (시작일 빠르고, 기간 긴 순서)
		weekSchedules.sort((a, b) => {
			if (a.start_date !== b.start_date) return a.start_date.localeCompare(b.start_date);
			const durationA = new Date(a.end_date) - new Date(a.start_date);
			const durationB = new Date(b.end_date) - new Date(b.start_date);
			return durationB - durationA;
		});

		// 슬롯 사용 추적
		const slotUsage = Array(7)
			.fill()
			.map(() => []);

		weekSchedules.forEach((schedule) => {
			// 시작/끝 인덱스 찾기
			let startIndex = updatedDates.findIndex((d) => d.date === schedule.start_date);
			let endIndex = updatedDates.findIndex((d) => d.date === schedule.end_date);

			// 이번 주 범위 밖이면 조정
			if (startIndex === -1) startIndex = schedule.start_date < weekStart ? 0 : -1;
			if (endIndex === -1) endIndex = schedule.end_date > weekEnd ? 6 : -1;

			if (startIndex === -1 || endIndex === -1 || startIndex > endIndex) return;

			// 비어있는 가장 낮은 슬롯 찾기
			let slotIndex = 0;
			while (true) {
				let isAvailable = true;
				for (let i = startIndex; i <= endIndex; i++) {
					if (slotUsage[i].includes(slotIndex)) {
						isAvailable = false;
						break;
					}
				}
				if (isAvailable) break;
				slotIndex++;
			}

			// 슬롯 점유
			for (let i = startIndex; i <= endIndex; i++) {
				slotUsage[i].push(slotIndex);
			}

			// 날짜별 슬롯에 저장
			for (let i = startIndex; i <= endIndex; i++) {
				while (updatedDates[i].slots.length <= slotIndex) {
					updatedDates[i].slots.push(null);
				}

				updatedDates[i].slots[slotIndex] = {
					...schedule,
					isStart: i === startIndex || schedule.start_date === updatedDates[i].date,
					isEnd: i === endIndex || schedule.end_date === updatedDates[i].date,
					isContinuedFromPrev: i > startIndex,
					isContinuedToNext: i < endIndex
				};
			}
		});

		return updatedDates;
	}

	function openModal(schedule) {
		selectedSchedule = schedule;
		showModal = true;
	}

	function isToday(dateStr) {
		const today = new Date();
		const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
		return dateStr === todayStr;
	}

	function goToPrevWeek() {
		weekOffset -= 1;
	}

	function goToNextWeek() {
		weekOffset += 1;
	}

	function goToThisWeek() {
		weekOffset = 0;
	}
</script>

<div class="module-container" style={style} class:mobile={$device.isMobile}>
	<div>
		<h2 class="module-title">🚐 주간 일정</h2>
	</div>

	<div class="week-calendar">
		<div class="calendar-wrapper">
			<div class="calendar-grid week-row">
				{#each weekDates as dayInfo, index}
					<div
						class="calendar-day"
						class:today={isToday(dayInfo.date)}
						class:sunday={index === 0}
						class:saturday={index === 6}
					>
						<div class="day-number">
							<span class="weekday-label">{weekDays[index]}</span>
							<span>{dayInfo.day}</span>
						</div>
						<div class="day-content">
							{#each dayInfo.slots as slot}
								{#if slot}
									<button
										class="schedule-item"
										class:start={slot.isStart}
										class:end={slot.isEnd}
										class:continued={slot.isContinuedFromPrev}
										style="background-color: {slot.color || '#4285F4'};"
										title={slot.title}
										onclick={() => openModal(slot)}
									>
										{#if slot.isStart || !slot.isContinuedFromPrev}
											{slot.title}
										{:else}
											&nbsp;
										{/if}
									</button>
								{:else}
									<div class="schedule-placeholder"></div>
								{/if}
							{/each}
						</div>
					</div>
				{/each}
			</div>
			<div class="week-spinner">
				<button class="spin-btn" onclick={goToPrevWeek} aria-label="이전 주">
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<polyline points="18 15 12 9 6 15"></polyline>
					</svg>
				</button>
				<button 
					class="spin-btn today-spin-btn" 
					class:disabled={weekOffset === 0} 
					onclick={goToThisWeek} 
					aria-label="오늘"
					title="이번 주로 이동"
				>
					<span>Today</span>
				</button>
				<button class="spin-btn" onclick={goToNextWeek} aria-label="다음 주">
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<polyline points="6 9 12 15 18 9"></polyline>
					</svg>
				</button>
			</div>
		</div>
	</div>
</div>

<ScheduleDetailModal bind:visible={showModal} schedule={selectedSchedule} />

<style>
	.week-calendar {
		margin-top: 0.5rem;
	}

	.calendar-wrapper {
		display: flex;
		gap: 0;
	}

	.calendar-wrapper .calendar-grid {
		flex: 1;
		border-top-right-radius: 0;
		border-bottom-right-radius: 0;
	}

	/* 스핀 버튼 컨테이너 */
	.week-spinner {
		display: grid;
        grid-template-rows: 2fr 1fr 2fr;
		border: 1px solid var(--border-color);
		border-left: none;
		border-radius: 0 8px 8px 0;
		overflow: hidden;
	}

	.spin-btn {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		background: var(--bg-secondary);
		color: var(--text-secondary);
		border: none;
		cursor: pointer;
		transition: all 0.2s;
		border-bottom: 1px solid var(--border-color);
	}

	.spin-btn:last-child {
		border-bottom: none;
	}

	.spin-btn:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
	}

    .today-spin-btn {
        font-size: 0.7rem;
        font-weight: 400;
        letter-spacing: -0.5px;
    }
    
    .today-spin-btn.disabled {
        opacity: 0.3;
        cursor: default;
    }
    
    .today-spin-btn.disabled:hover {
        background: var(--bg-secondary);
        color: var(--text-secondary);
    }

	/* 주간 캘린더용 추가 스타일 */
	.week-row .calendar-day {
		min-height: 140px;
	}

	.week-row .day-number {
		display: flex;
		align-items: center;
		gap: 6px;
		border-bottom: 1px solid var(--border-color);
	}

	.week-row .weekday-label {
		font-size: 0.75rem;
		color: var(--text-secondary);
		font-weight: 300;
	}

	.week-row .calendar-day.sunday .weekday-label {
		color: var(--text-danger);
	}

	.week-row .calendar-day.saturday .weekday-label {
		color: var(--text-info);
	}

	/* Mobile */
	.mobile .week-row .calendar-day {
		min-height: 100px;
	}

	.mobile .week-row .day-number {
		flex-direction: column;
		align-items: flex-start;
		gap: 0;
	}

	.mobile .week-row .weekday-label {
		font-size: 0.65rem;
	}

	.mobile .spin-btn {
		width: 24px;
	}
</style>
