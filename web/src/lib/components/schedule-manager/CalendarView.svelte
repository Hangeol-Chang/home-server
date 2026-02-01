<script>
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
    import { getGoogleEvents } from '$lib/api/schedule-manager.js';
    import ScheduleDetailModal from './ScheduleDetailModal.svelte';
    import '$lib/styles/module.css';

	let { year = new Date().getFullYear(), month = new Date().getMonth() + 1 } = $props();

	let schedules = $state([]);
	let loading = $state(false);
	let error = $state(null);
    
    // Modal State
    let showModal = $state(false);
    let selectedSchedule = $state(null);

	const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

	onMount(() => {
		loadData();
	});

	$effect(() => {
		loadData();
	});

	async function loadData() {
		loading = true;
        try {
            schedules = await getGoogleEvents(year, month);
        } catch (err) {
            console.error("Failed to load schedules:", err);
            schedules = [];
        }
		loading = false;
	}

    function openModal(schedule) {
        selectedSchedule = schedule;
        showModal = true;
    }
	let weeks = $derived(getCalendarWeeks());
	function getCalendarWeeks() {
		const firstDay = new Date(year, month - 1, 1);
		const lastDay = new Date(year, month, 0).getDate();
		const startWeekday = firstDay.getDay();

		const weeks = [];
		let currentWeekDays = [];

		// 1. 날짜 그리드 생성
		// Empty slots for previous month
		for (let i = 0; i < startWeekday; i++) {
			currentWeekDays.push(null);
		}

		// Days of current month
		for (let day = 1; day <= lastDay; day++) {
			const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
			currentWeekDays.push({
				day,
				date: dateStr,
                slots: [] // 일정이 들어갈 슬롯들
			});

			if (currentWeekDays.length === 7) {
				weeks.push({ days: currentWeekDays, slots: [] });
				currentWeekDays = [];
			}
		}

		// Empty slots for next month
		if (currentWeekDays.length > 0) {
			while (currentWeekDays.length < 7) {
				currentWeekDays.push(null);
			}
			weeks.push({ days: currentWeekDays, slots: [] });
		}

        // 2. 일정 배치 로직
        weeks.forEach(week => {
            // 이번 주에 해당하는 날짜 범위 구하기
            const weekStart = week.days.find(d => d !== null)?.date;
            const weekEnd = week.days.slice().reverse().find(d => d !== null)?.date;
            
            if (!weekStart) return;

            // 이번 주에 표시해야 할 일정 필터링
            const weekSchedules = schedules.filter(s => {
                return s.end_date >= weekStart && s.start_date <= weekEnd;
            });

            // 일정 정렬 (시작일 빠르고, 기간 긴 순서)
            weekSchedules.sort((a, b) => {
                if (a.start_date !== b.start_date) return a.start_date.localeCompare(b.start_date);
                const durationA = new Date(a.end_date) - new Date(a.start_date);
                const durationB = new Date(b.end_date) - new Date(b.start_date);
                return durationB - durationA;
            });

            // 슬롯 할당 상태 (각 날짜별로 사용 중인 슬롯 인덱스 추적)
            // week.days는 7개 요소. null인 날짜도 인덱스는 차지함.
            const slotUsage = Array(7).fill().map(() => []); // 각 요일별 사용된 슬롯 인덱스들

            weekSchedules.forEach(schedule => {
                // 이 일정이 이번 주에서 차지하는 요일 인덱스 범위(0~6) 구하기
                let startIndex = 0;
                let endIndex = 6;

                // 시작일이 이번 주보다 늦으면 그 요일부터 시작
                if (schedule.start_date > weekStart) {
                    const startDay = new Date(schedule.start_date).getDate();
                    // 이번 달의 날짜와 매칭되는 인덱스 찾기
                    const idx = week.days.findIndex(d => d && d.date === schedule.start_date);
                    if (idx !== -1) startIndex = idx;
                } else {
                    // 지난 주부터 이어지는 경우, 첫 번째 유효한 날짜부터 시작
                    startIndex = week.days.findIndex(d => d !== null);
                }

                // 종료일이 이번 주보다 빠르면 그 요일까지
                if (schedule.end_date < weekEnd) {
                    const idx = week.days.findIndex(d => d && d.date === schedule.end_date);
                    if (idx !== -1) endIndex = idx;
                } else {
                    // 다음 주까지 이어지는 경우, 마지막 유효한 날짜까지
                    // (null인 날짜 전까지)
                    for (let i = 6; i >= 0; i--) {
                        if (week.days[i] !== null) {
                            endIndex = i;
                            break;
                        }
                    }
                }

                // 유효하지 않은 범위면 패스
                if (startIndex > endIndex) return;

                // 해당 범위(startIndex ~ endIndex)에서 비어있는 가장 낮은 슬롯 인덱스 찾기
                let slotIndex = 0;
                while (true) {
                    let isAvailable = true;
                    for (let i = startIndex; i <= endIndex; i++) {
                        if (week.days[i] === null) continue; // 빈 날짜는 체크 안함
                        if (slotUsage[i].includes(slotIndex)) {
                            isAvailable = false;
                            break;
                        }
                    }
                    if (isAvailable) break;
                    slotIndex++;
                }

                // 슬롯 점유 표시
                for (let i = startIndex; i <= endIndex; i++) {
                    if (week.days[i] !== null) {
                        slotUsage[i].push(slotIndex);
                    }
                }

                // 일정 객체에 배치 정보 추가하여 날짜별 슬롯에 저장
                for (let i = startIndex; i <= endIndex; i++) {
                    if (week.days[i] === null) continue;
                    
                    // 해당 날짜의 slots 배열 확장
                    while (week.days[i].slots.length <= slotIndex) {
                        week.days[i].slots.push(null);
                    }
                    
                    week.days[i].slots[slotIndex] = {
                        ...schedule,
                        isStart: i === startIndex || schedule.start_date === week.days[i].date,
                        isEnd: i === endIndex || schedule.end_date === week.days[i].date,
                        isContinuedFromPrev: i > startIndex,
                        isContinuedToNext: i < endIndex
                    };
                }
            });
        });

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

<div class="module-container" class:mobile={$device.isMobile}>
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
			{#each weeks as week}
				{#each week.days as dayInfo}
					{#if dayInfo === null}
						<div class="calendar-day empty"></div>
					{:else}
						<div
							class="calendar-day"
							class:today={isToday(dayInfo.date)}
						>
							<div class="day-number">{dayInfo.day}</div>
							<div class="day-content">
								{#each dayInfo.slots as slot}
                                    {#if slot}
                                        <div 
                                            class="schedule-item" 
                                            class:start={slot.isStart}
                                            class:end={slot.isEnd}
                                            class:continued={slot.isContinuedFromPrev}
                                            style="background-color: {slot.color || '#4285F4'};"
                                            title={slot.title}
                                            onclick={() => openModal(slot)}
                                            role="button"
                                            tabindex="0"
                                            onkeydown={(e) => e.key === 'Enter' && openModal(slot)}
                                        >
                                            {#if slot.isStart || !slot.isContinuedFromPrev}
                                                {slot.title}
                                            {:else}
                                                &nbsp;
                                            {/if}
                                        </div>
                                    {:else}
                                        <div class="schedule-placeholder"></div>
                                    {/if}
                                {/each}
							</div>
						</div>
					{/if}
				{/each}
			{/each}
		</div>
	</div>
</div>

<ScheduleDetailModal bind:visible={showModal} schedule={selectedSchedule} />

<style>
	/* 월간 캘린더용 추가 스타일 */
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
</style>
