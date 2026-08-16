<script>
    import { onMount } from 'svelte';
    import { device } from '$lib/stores/device';
    import { getWeeklySchedules } from '$lib/api/schedule-manager.js';
    import WeeklyTimetableFormModal from './WeeklyTimetableFormModal.svelte';
    import '$lib/styles/module.css';

    let schedules = $state([]);
    let loading = $state(false);
    let error = $state(null);

    // Modal State
    let showFormModal = $state(false);
    let selectedSchedule = $state(null);
    let initialDayOfWeek = $state(0);
    let initialStartTime = $state('09:00');

    const weekDays = ['일', '월', '화', '수', '목', '금', '토'];
    
    // 시간 범위: 06:00 ~ 02:00 (다음날)
    // 06:00 ~ 23:00 (18시간) + 00:00 ~ 02:00 (2시간) = 20시간
    const timeSlots = generateTimeSlots();

    function generateTimeSlots() {
        const slots = [];
        // 06:00 ~ 23:00
        for (let h = 6; h < 24; h++) {
            slots.push(`${String(h).padStart(2, '0')}:00`);
        }
        // 00:00 ~ 02:00
        for (let h = 0; h <= 2; h++) {
            slots.push(`${String(h).padStart(2, '0')}:00`);
        }
        return slots;
    }

    // 시간을 분 단위로 변환 (06:00 기준)
    function timeToMinutes(time) {
        const [h, m] = time.split(':').map(Number);
        // 06:00 = 0분, 02:00(+1day) = 20*60 = 1200분
        if (h >= 6) {
            return (h - 6) * 60 + m;
        } else {
            // 0~2시는 다음날로 취급
            return (h + 18) * 60 + m;
        }
    }

    // 분을 시간으로 변환
    function minutesToTime(minutes) {
        const h = Math.floor(minutes / 60) + 6;
        const adjustedH = h >= 24 ? h - 24 : h;
        return `${String(adjustedH).padStart(2, '0')}:00`;
    }

    onMount(() => {
        loadData();
    });

    async function loadData() {
        loading = true;
        try {
            schedules = await getWeeklySchedules();
        } catch (err) {
            console.error("Failed to load weekly schedules:", err);
            error = '일정을 불러오는데 실패했습니다.';
            schedules = [];
        }
        loading = false;
    }

    // 특정 요일, 시간에 해당하는 일정들 찾기 (슬롯 시작점 기준 점유 여부)
    function getSchedulesForSlot(dayOfWeek, time) {
        return schedules.filter(s => {
            if (s.day_of_week !== dayOfWeek) return false;
            const slotMinutes = timeToMinutes(time);
            const startMinutes = timeToMinutes(s.start_time);
            const endMinutes = timeToMinutes(s.end_time);
            return slotMinutes >= startMinutes && slotMinutes < endMinutes;
        });
    }

    // 해당 슬롯 내에서 시작하는 일정들 찾기
    function getSchedulesStartingInSlot(dayOfWeek, time) {
        const slotStart = timeToMinutes(time);
        const slotEnd = slotStart + 60;
        return schedules.filter(s => {
            if (s.day_of_week !== dayOfWeek) return false;
            const start = timeToMinutes(s.start_time);
            return start >= slotStart && start < slotEnd;
        });
    }

    // 일정의 Top 위치 계산 (슬롯 시작 시간 기준 오프셋 %)
    function getScheduleTop(schedule, time) {
        const slotStart = timeToMinutes(time);
        const start = timeToMinutes(schedule.start_time);
        return (start - slotStart) / 60 * 100;
    }

    // 일정의 높이 계산 (시간 단위)
    function getScheduleHeight(schedule) {
        const startMinutes = timeToMinutes(schedule.start_time);
        const endMinutes = timeToMinutes(schedule.end_time);
        return (endMinutes - startMinutes) / 60;
    }

    // 셀 클릭 핸들러
    function handleCellClick(dayOfWeek, time) {
        const existingSchedules = getSchedulesForSlot(dayOfWeek, time);
        if (existingSchedules.length > 0) {
            // 기존 일정 편집
            selectedSchedule = existingSchedules[0];
        } else {
            // 새 일정 생성
            selectedSchedule = null;
            initialDayOfWeek = dayOfWeek;
            initialStartTime = time;
        }
        showFormModal = true;
    }

    // 일정 클릭 핸들러
    function handleScheduleClick(e, schedule) {
        e.stopPropagation();
        selectedSchedule = schedule;
        showFormModal = true;
    }

    async function handleFormSuccess() {
        await loadData();
    }

    async function handleDelete() {
        await loadData();
    }

    // 시간 포맷 (표시용)
    function formatTimeDisplay(time) {
        const [h] = time.split(':').map(Number);
        if (h === 0) return '12AM';
        if (h === 12) return '12PM';
        if (h < 12) return `${h}AM`;
        return `${h - 12}PM`;
    }
</script>

<div class="module-container" class:mobile={$device.isMobile}>
    <div class="chart-header">
        <h3>주간 타임테이블</h3>
    </div>

    {#if loading}
        <div class="loading-state">불러오는 중...</div>
    {:else if error}
        <div class="error-state">{error}</div>
    {:else}
        <div class="timetable-container">
            <div class="timetable-grid">
                <!-- 헤더 행: 빈 셀 + 요일들 -->
                <div class="timetable-header-corner"></div>
                {#each weekDays as day, index}
                    <div class="timetable-weekday" class:sunday={index === 0} class:saturday={index === 6}>
                        {day}
                    </div>
                {/each}

                <!-- 시간 행들 -->
                {#each timeSlots as time, timeIndex}
                    <!-- 시간 레이블 -->
                    <div class="timetable-time-label">
                        {formatTimeDisplay(time)}
                    </div>
                    
                    <!-- 각 요일의 셀 -->
                    {#each weekDays as _, dayIndex}
                        {@const cellSchedules = getSchedulesForSlot(dayIndex, time)}
                        {@const startingSchedules = getSchedulesStartingInSlot(dayIndex, time)}
                        <div 
                            class="timetable-cell"
                            class:has-schedule={cellSchedules.length > 0}
                            onclick={() => handleCellClick(dayIndex, time)}
                            role="button"
                            tabindex="0"
                            onkeydown={(e) => e.key === 'Enter' && handleCellClick(dayIndex, time)}
                        >
                            {#each startingSchedules as schedule}
                                <!-- svelte-ignore a11y_no_static_element_interactions -->
                                <div 
                                    class="timetable-schedule"
                                    style="
                                        background-color: {schedule.color || '#4285F4'};
                                        height: calc({getScheduleHeight(schedule)} * 100% - 2px);
                                        top: {getScheduleTop(schedule, time)}%;
                                    "
                                    onclick={(e) => handleScheduleClick(e, schedule)}
                                    onkeydown={(e) => e.key === 'Enter' && handleScheduleClick(e, schedule)}
                                >
                                    <span class="schedule-title">{schedule.title}</span>
                                    <span class="schedule-time">
                                        {schedule.start_time} - {schedule.end_time}
                                    </span>
                                </div>
                            {/each}
                        </div>
                    {/each}
                {/each}
            </div>
        </div>
    {/if}
</div>

<WeeklyTimetableFormModal
    bind:visible={showFormModal}
    schedule={selectedSchedule}
    initialDayOfWeek={initialDayOfWeek}
    initialStartTime={initialStartTime}
    onSuccess={handleFormSuccess}
    onDelete={handleDelete}
/>

<style>
    .timetable-container {
        overflow-x: auto;
    }

    .timetable-grid {
        display: grid;
        grid-template-columns: 60px repeat(7, minmax(80px, 1fr));
        border: 1px solid var(--border-color);
        border-radius: 4px;
        overflow: hidden;
        min-width: 600px;
    }

    /* 헤더 코너 (빈 셀) */
    .timetable-header-corner {
        background: var(--bg-primary-dark);
        border-bottom: 1px solid var(--border-color);
        border-right: 1px solid var(--border-color-light);
    }

    /* 요일 헤더 */
    .timetable-weekday {
        text-align: center;
        font-weight: 400;
        padding: 12px 8px;
        color: var(--text-secondary);
        background: var(--bg-primary-dark);
        border-bottom: 1px solid var(--border-color);
        border-right: 1px solid var(--border-color-light);
    }

    .timetable-weekday:last-child {
        border-right: none;
    }

    .timetable-weekday.sunday {
        color: var(--text-danger);
    }

    .timetable-weekday.saturday {
        color: var(--text-info);
    }

    /* 시간 레이블 */
    .timetable-time-label {
        padding: 4px 8px;
        font-size: 0.75rem;
        color: var(--text-tertiary);
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
        border-bottom: 1px solid var(--border-color-light);
        display: flex;
        align-items: flex-start;
        justify-content: flex-end;
        height: 48px;
    }

    /* 타임테이블 셀 */
    .timetable-cell {
        position: relative;
        height: 48px;
        background: var(--bg-primary);
        border-right: 1px solid var(--border-color-light);
        border-bottom: 1px solid var(--border-color-light);
        cursor: pointer;
        transition: background-color 0.15s;
    }

    .timetable-cell:nth-child(8n+1) {
        border-right: 1px solid var(--border-color);
    }

    .timetable-cell:hover {
        background: var(--bg-secondary);
    }

    .timetable-cell.has-schedule:hover {
        background: var(--bg-primary);
    }

    /* 일정 아이템 */
    .timetable-schedule {
        position: absolute;
        top: 1px;
        left: 2px;
        right: 2px;
        border-radius: 4px;
        padding: 4px 6px;
        color: white;
        font-size: 0.75rem;
        overflow: hidden;
        cursor: pointer;
        z-index: 10;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .timetable-schedule:hover {
        filter: brightness(0.9);
        z-index: 11;
    }

    .schedule-title {
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .schedule-time {
        font-size: 0.65rem;
        opacity: 0.9;
        white-space: nowrap;
    }

    /* 로딩/에러 상태 */
    .loading-state,
    .error-state {
        padding: 40px;
        text-align: center;
        color: var(--text-secondary);
    }

    .error-state {
        color: var(--text-danger);
    }

    /* 모바일 대응 */
    @media (max-width: 768px) {
        .timetable-grid {
            grid-template-columns: 50px repeat(7, minmax(60px, 1fr));
        }

        .timetable-time-label {
            font-size: 0.65rem;
            padding: 4px 4px;
            height: 40px;
        }

        .timetable-cell {
            height: 40px;
        }

        .timetable-weekday {
            padding: 8px 4px;
            font-size: 0.8rem;
        }

        .timetable-schedule {
            padding: 2px 4px;
        }

        .schedule-title {
            font-size: 0.65rem;
        }

        .schedule-time {
            display: none;
        }
    }
</style>
