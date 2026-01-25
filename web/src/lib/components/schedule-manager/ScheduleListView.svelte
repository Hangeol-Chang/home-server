<script>
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
    import { fade } from 'svelte/transition';

    let schedules = $state([]);
    let logs = $state([]);
    let currentDate = $state(new Date());
    let showAddModal = $state(false);
    let showLogModal = $state(false);
    let selectedLog = $state(null);
    
    // New Schedule Form
    let newSchedule = $state({
        title: '',
        description: '',
        cycle_weeks: 1,
        day_of_week: 1, // Monday
        start_date: new Date().toISOString().split('T')[0]
    });

    onMount(async () => {
        await fetchSchedules();
        await fetchLogs();
    });

    async function fetchSchedules() {
        try {
            const res = await fetch('/api/schedule-manager/recurring-schedules');
            if (res.ok) {
                schedules = await res.json();
            }
        } catch (e) {
            console.error(e);
        }
    }

    async function fetchLogs() {
        // Fetch logs for current week window
        // For simplicity, fetch all logs for now or last 3 months
        // Ideally, we should calculate the "current cycle" for each schedule and see if it's done.
        try {
            const res = await fetch('/api/schedule-manager/schedule-logs');
            if (res.ok) {
                logs = await res.json();
            }
        } catch (e) {
            console.error(e);
        }
    }

    async function saveLog() {
        if (!selectedLog) return;

        // Remove extra properties like scheduleTitle before sending
        const { scheduleTitle, ...logData } = selectedLog;

        try {
            const res = await fetch('/api/schedule-manager/schedule-logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(logData)
            });
            if (res.ok) {
                await fetchLogs();
                showLogModal = false;
            }
        } catch (e) {
            console.error(e);
        }
    }

    function openLogModal(schedule) {
        const cycleStart = getCycleStartDate(schedule, new Date());
        let log = logs.find(l => l.schedule_id === schedule.id && l.cycle_start_date === cycleStart);
        
        if (!log) {
            log = {
                schedule_id: schedule.id,
                cycle_start_date: cycleStart,
                is_completed: false,
                notes: ''
            };
        }
        
        selectedLog = { ...log, scheduleTitle: schedule.title };
        showLogModal = true;
    }

    async function toggleComplete(schedule, isCompleted) {
        // Calculate cycle_start_date for this schedule based on current date
        // This is tricky. We need to know which cycle we are checking off.
        // For now, let's assume we are checking off "this week's" instance.
        
        const cycleStartDate = getCycleStartDate(schedule, new Date());
        
        // Check if log exists to preserve notes
        let existingLog = logs.find(l => l.schedule_id === schedule.id && l.cycle_start_date === cycleStartDate);
        
        const log = {
            schedule_id: schedule.id,
            cycle_start_date: cycleStartDate,
            is_completed: isCompleted,
            notes: existingLog ? existingLog.notes : ''
        };

        try {
            const res = await fetch('/api/schedule-manager/schedule-logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(log)
            });
            if (res.ok) {
                await fetchLogs();
            }
        } catch (e) {
            console.error(e);
        }
    }

    function getCycleStartDate(schedule, targetDate) {
        // Simple logic: find the most recent start date cycle
        // This needs robust logic for N-weeks.
        // For 1 week, it's the start of the week.
        // For N weeks, it's start_date + K * N weeks.
        
        const start = new Date(schedule.start_date);
        const target = new Date(targetDate);
        
        // Normalize to start of day
        start.setHours(0,0,0,0);
        target.setHours(0,0,0,0);
        
        const diffTime = Math.abs(target - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
        const cycleDays = schedule.cycle_weeks * 7;
        
        const cyclesPassed = Math.floor(diffDays / cycleDays);
        const cycleStart = new Date(start);
        cycleStart.setDate(start.getDate() + (cyclesPassed * cycleDays));
        
        return cycleStart.toISOString().split('T')[0];
    }

    function getCycleEndDate(schedule, cycleStartDateStr) {
        const start = new Date(cycleStartDateStr);
        const cycleDays = schedule.cycle_weeks * 7;
        const end = new Date(start);
        end.setDate(start.getDate() + cycleDays - 1);
        return end.toISOString().split('T')[0];
    }

    function isCompleted(schedule) {
        const cycleStart = getCycleStartDate(schedule, new Date());
        return logs.some(l => l.schedule_id === schedule.id && l.cycle_start_date === cycleStart && l.is_completed);
    }

    async function addSchedule() {
        try {
            // Set start_date to nearest past Sunday automatically
            const d = new Date();
            const day = d.getDay();
            const diff = d.getDate() - day;
            d.setDate(diff);
            newSchedule.start_date = d.toISOString().split('T')[0];

            const res = await fetch('/api/schedule-manager/recurring-schedules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newSchedule)
            });
            if (res.ok) {
                showAddModal = false;
                await fetchSchedules();
                // Reset form
                newSchedule = {
                    title: '',
                    description: '',
                    cycle_weeks: 1,
                    day_of_week: 1,
                    start_date: new Date().toISOString().split('T')[0]
                };
            }
        } catch (e) {
            console.error(e);
        }
    }
</script>

<div class="module-container">
    <div class="header">
        <h3>✅ 반복 스케줄</h3>
        <button class="add-btn" onclick={() => showAddModal = true}>+ 일정 추가</button>
    </div>

    <div class="table-wrapper">
        <table class="data-table">
            <thead>
                <tr>
                    <th style="width: 50px; text-align: center;"> </th>
                    <th>Name</th>
                    <th style="width: 80px; text-align: center;">Cycle</th>
                    <th style="width: 120px; text-align: center;">Start</th>
                    <th style="width: 120px; text-align: center;">End</th>
                </tr>
            </thead>
            <tbody>
                {#each schedules as schedule}
                    {@const cycleStart = getCycleStartDate(schedule, currentDate)}
                    {@const cycleEnd = getCycleEndDate(schedule, cycleStart)}
                    {@const completed = isCompleted(schedule)}
                    
                    <tr class:completed={completed} onclick={() => openLogModal(schedule)}>
                        <td class="text-center" onclick={(e) => e.stopPropagation()}>
                            <button 
                                class="custom-checkbox"
                                class:checked={completed}
                                onclick={() => toggleComplete(schedule, !completed)}
                                aria-label={completed ? '완료 취소' : '완료 체크'}
                            >
                                {#if completed}
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                {/if}
                            </button>
                        </td>
                        <td>
                            <div class="title">{schedule.title}</div>
                            <!-- {#if schedule.description}
                                <div class="description">{schedule.description}</div>
                            {/if} -->
                        </td>
                        <td class="text-center">{schedule.cycle_weeks}주</td>
                        <td class="text-center">{cycleStart}</td>
                        <td class="text-center">{cycleEnd}</td>
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>

    {#if showAddModal}
        <div role="none" class="modal-overlay" class:mobile={$device.isMobile} class:tablet={$device.isTablet} onclick={() => showAddModal = false}>
            <div role="none" class="modal-container" onclick={(e) => e.stopPropagation()}>
				<div class="chart-header">
                    <h3>🎞️ 새 반복 스케줄</h3>
                </div>

                <div class="form-group">
                    <label for="title">제목</label>
                    <input id="title" type="text" bind:value={newSchedule.title} placeholder="예: 독서모임" />
                </div>
                <div class="form-group">
                    <label for="cycle_weeks">주기 (주)</label>
                    <input id="cycle_weeks" type="number" bind:value={newSchedule.cycle_weeks} min="1" />
                </div>
                <!-- start_date is automatically set to nearest past Sunday -->
                <div class="form-group">
                    <label for="description">설명</label>
                    <textarea 
                        id="description"
                        bind:value={newSchedule.description} 
                        placeholder="일정에 대한 설명을 입력하세요..."
                        rows="4"
                    ></textarea>
                </div>
                <div class="form-actions">
                    <button class="btn-cancel" onclick={() => showAddModal = false}>취소</button>
                    <button class="btn-submit" onclick={addSchedule}>저장</button>
                </div>
            </div>
        </div>
    {/if}

    {#if showLogModal && selectedLog}
        <div role="none" class="modal-overlay" class:mobile={$device.isMobile} class:tablet={$device.isTablet} onclick={() => showLogModal = false}>
            <div role="none" class="modal-container" onclick={(e) => e.stopPropagation()}>
                <div class="chart-header">
                    <h3>{selectedLog.scheduleTitle}</h3>
                </div>
                <div class="form-group">
                    <label for="is_completed">상태</label>
                    <div role="none" class="checkbox-label" onclick={() => selectedLog.is_completed = !selectedLog.is_completed}>
                        <button 
                            class="custom-checkbox"
                            class:checked={selectedLog.is_completed}
                            aria-label={selectedLog.is_completed ? '완료 취소' : '완료 체크'}
                        >
                            {#if selectedLog.is_completed}
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                            {/if}
                        </button>
                        <span>완료됨</span>
                    </div>
                </div>
                <div class="form-group">
                    <label for="notes">이번 주기 메모</label>
                    <textarea 
                        id="notes"
                        bind:value={selectedLog.notes} 
                        placeholder="이번 주기에 대한 메모를 입력하세요..."
                        rows="4"
                    ></textarea>
                </div>
                <div class="form-actions">
                    <button class="btn-cancel" onclick={() => showLogModal = false}>취소</button>
                    <button class="btn-submit" onclick={saveLog}>저장</button>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    /* Table specific styles */
    tr.completed {
        opacity: 0.6;
    }
    
    tr.completed .title {
        text-decoration: line-through;
    }

    tr {
        cursor: pointer;
    }

    .title {
        font-weight: 300;
        color: var(--text-primary);
    }
    
    .checkbox-label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
    }
    
    .checkbox-label span {
        user-select: none;
    }

    /* Custom Checkbox */
    .custom-checkbox {
        width: 24px;
        height: 24px;
        min-width: 24px;
        border: 1px solid var(--border-color, #ccc);
        border-radius: 4px;
        background: var(--bg-primary, #fff);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.15s ease;
        padding: 0;
    }

    .custom-checkbox:hover {
        border-color: var(--primary-color, #4a90d9);
        background: var(--bg-hover, #f5f5f5);
    }

    .custom-checkbox.checked {
        background: var(--primary-color, #4a90d9);
        border-color: var(--primary-color, #4a90d9);
    }

    .custom-checkbox svg {
        width: 18px;
        height: 18px;
        color: white;
    }
</style>
