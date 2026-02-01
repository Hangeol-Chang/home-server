<script>
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
    import { getGoogleEvents, getTodos, moveTodo, toggleTodoCompletion } from '$lib/api/schedule-manager.js';
    import ScheduleDetailModal from './ScheduleDetailModal.svelte';
    import DayDetailModal from './DayDetailModal.svelte';
    import TodoFormModal from './TodoFormModal.svelte';
    import '$lib/styles/module.css';

	let { year = new Date().getFullYear(), month = new Date().getMonth() + 1 } = $props();

	let schedules = $state([]);
	let todos = $state([]);
	let loading = $state(false);
	let error = $state(null);
    
    // Modal State
    let showModal = $state(false);
    let selectedSchedule = $state(null);
    
    // Day Detail Modal State
    let showDayModal = $state(false);
    let selectedDate = $state(null);
    let selectedDaySchedules = $state([]);
    let selectedDayTodos = $state([]);
    
    // Todo Form Modal State
    let showTodoForm = $state(false);
    let editingTodo = $state(null);
    let initialTodoDate = $state(null);
    
    // Drag and Drop State
    let draggingItem = $state(null);
    let dragOverDate = $state(null);

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
            const startDate = `${year}-${String(month).padStart(2, '0')}-01`;
            const lastDay = new Date(year, month, 0).getDate();
            const endDate = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;
            
            const [googleEvents, todoItems] = await Promise.all([
                getGoogleEvents(year, month),
                getTodos(startDate, endDate)
            ]);
            
            schedules = googleEvents;
            todos = todoItems.map(t => ({ ...t, source: 'todo' }));
        } catch (err) {
            console.error("Failed to load data:", err);
            schedules = [];
            todos = [];
        }
		loading = false;
	}

    // 모든 일정 (구글 캘린더 + 할일) 합치기
    let allItems = $derived([
        ...schedules.map(s => ({ ...s, type: 'schedule' })),
        ...todos.map(t => ({ ...t, type: 'todo' }))
    ]);

    function openModal(item) {
        if (item.type === 'todo') {
            editingTodo = item;
            showTodoForm = true;
        } else {
            selectedSchedule = { ...item, type: item.source || 'Google Calendar' };
            showModal = true;
        }
    }
    
    function openDayModal(dateStr) {
        selectedDate = dateStr;
        // 해당 날짜에 걸쳐있는 일정과 할일 필터링
        selectedDaySchedules = schedules.filter(s => 
            s.start_date <= dateStr && s.end_date >= dateStr
        );
        selectedDayTodos = todos.filter(t => 
            t.start_date <= dateStr && t.end_date >= dateStr
        );
        showDayModal = true;
    }
    
    function handleAddTodo(date) {
        showDayModal = false;
        initialTodoDate = date;
        editingTodo = null;
        showTodoForm = true;
    }
    
    function handleEditTodo(todo) {
        showDayModal = false;
        editingTodo = todo;
        initialTodoDate = null;
        showTodoForm = true;
    }
    
    async function handleTodoFormSuccess() {
        await loadData();
        // Day modal이 열려있었으면 데이터 갱신
        if (selectedDate) {
            selectedDayTodos = todos.filter(t => 
                t.start_date <= selectedDate && t.end_date >= selectedDate
            );
        }
    }
    
    async function handleTodoChange() {
        await loadData();
        if (selectedDate) {
            selectedDayTodos = todos.filter(t => 
                t.start_date <= selectedDate && t.end_date >= selectedDate
            );
        }
    }
    
    // Drag and Drop handlers
    function handleDragStart(e, item) {
        if (item.type !== 'todo') {
            e.preventDefault();
            return;
        }
        draggingItem = item;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', JSON.stringify(item));
    }
    
    function handleDragOver(e, dateStr) {
        if (!draggingItem) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        dragOverDate = dateStr;
    }
    
    function handleDragLeave(e) {
        dragOverDate = null;
    }
    
    async function handleDrop(e, targetDateStr) {
        e.preventDefault();
        dragOverDate = null;
        
        if (!draggingItem || draggingItem.type !== 'todo') {
            draggingItem = null;
            return;
        }
        
        const todo = draggingItem;
        draggingItem = null;
        
        // 날짜 차이 계산
        const originalStart = new Date(todo.start_date);
        const targetDate = new Date(targetDateStr);
        const daysDiff = Math.round((targetDate - originalStart) / (1000 * 60 * 60 * 24));
        
        if (daysDiff === 0) return; // 같은 날짜면 무시
        
        // 새 날짜 계산
        const newStart = new Date(originalStart);
        newStart.setDate(newStart.getDate() + daysDiff);
        const newEnd = new Date(todo.end_date);
        newEnd.setDate(newEnd.getDate() + daysDiff);
        
        const newStartStr = newStart.toISOString().split('T')[0];
        const newEndStr = newEnd.toISOString().split('T')[0];
        
        try {
            await moveTodo(todo.id, newStartStr, newEndStr);
            await loadData();
        } catch (err) {
            console.error('Failed to move todo:', err);
        }
    }
    
    function handleDragEnd() {
        draggingItem = null;
        dragOverDate = null;
    }
    
    // Todo 체크박스 토글
    async function handleToggleTodo(e, todo) {
        e.stopPropagation();
        try {
            await toggleTodoCompletion(todo.id);
            await loadData();
        } catch (err) {
            console.error('Failed to toggle todo:', err);
        }
    }
    
    // 색상의 채도를 낮추는 함수 (완료된 할일용)
    function desaturateColor(color) {
        if (!color) return '#999';
        // Hex to RGB
        const hex = color.replace('#', '');
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        // RGB to HSL
        const max = Math.max(r, g, b) / 255;
        const min = Math.min(r, g, b) / 255;
        const l = (max + min) / 2;
        let h = 0, s = 0;
        if (max !== min) {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            const rNorm = r / 255, gNorm = g / 255, bNorm = b / 255;
            if (max === rNorm) h = ((gNorm - bNorm) / d + (gNorm < bNorm ? 6 : 0)) / 6;
            else if (max === gNorm) h = ((bNorm - rNorm) / d + 2) / 6;
            else h = ((rNorm - gNorm) / d + 4) / 6;
        }
        // 채도를 20%로 낮추고, 명도를 약간 높임
        const newS = 0.15;
        const newL = Math.min(l + 0.1, 0.7);
        // HSL to RGB
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        const q = newL < 0.5 ? newL * (1 + newS) : newL + newS - newL * newS;
        const p = 2 * newL - q;
        const newR = Math.round(hue2rgb(p, q, h + 1/3) * 255);
        const newG = Math.round(hue2rgb(p, q, h) * 255);
        const newB = Math.round(hue2rgb(p, q, h - 1/3) * 255);
        return `rgb(${newR}, ${newG}, ${newB})`;
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

        // 2. 일정 배치 로직 (구글 캘린더 + 할일 통합)
        weeks.forEach(week => {
            // 이번 주에 해당하는 날짜 범위 구하기
            const weekStart = week.days.find(d => d !== null)?.date;
            const weekEnd = week.days.slice().reverse().find(d => d !== null)?.date;
            
            if (!weekStart) return;

            // 이번 주에 표시해야 할 일정 필터링 (구글 + 할일)
            const weekItems = allItems.filter(s => {
                return s.end_date >= weekStart && s.start_date <= weekEnd;
            });

            // 일정 정렬 (시작일 빠르고, 기간 긴 순서)
            weekItems.sort((a, b) => {
                if (a.start_date !== b.start_date) return a.start_date.localeCompare(b.start_date);
                const durationA = new Date(a.end_date) - new Date(a.start_date);
                const durationB = new Date(b.end_date) - new Date(b.start_date);
                return durationB - durationA;
            });

            // 슬롯 할당 상태 (각 날짜별로 사용 중인 슬롯 인덱스 추적)
            // week.days는 7개 요소. null인 날짜도 인덱스는 차지함.
            const slotUsage = Array(7).fill().map(() => []); // 각 요일별 사용된 슬롯 인덱스들

            weekItems.forEach(item => {
                // 이 일정이 이번 주에서 차지하는 요일 인덱스 범위(0~6) 구하기
                let startIndex = 0;
                let endIndex = 6;

                // 시작일이 이번 주보다 늦으면 그 요일부터 시작
                if (item.start_date > weekStart) {
                    const startDay = new Date(item.start_date).getDate();
                    // 이번 달의 날짜와 매칭되는 인덱스 찾기
                    const idx = week.days.findIndex(d => d && d.date === item.start_date);
                    if (idx !== -1) startIndex = idx;
                } else {
                    // 지난 주부터 이어지는 경우, 첫 번째 유효한 날짜부터 시작
                    startIndex = week.days.findIndex(d => d !== null);
                }

                // 종료일이 이번 주보다 빠르면 그 요일까지
                if (item.end_date < weekEnd) {
                    const idx = week.days.findIndex(d => d && d.date === item.end_date);
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
                        ...item,
                        isStart: i === startIndex || item.start_date === week.days[i].date,
                        isEnd: i === endIndex || item.end_date === week.days[i].date,
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
							class="calendar-day clickable"
							class:today={isToday(dayInfo.date)}
                            class:drag-over={dragOverDate === dayInfo.date}
                            onclick={() => openDayModal(dayInfo.date)}
                            ondragover={(e) => handleDragOver(e, dayInfo.date)}
                            ondragleave={handleDragLeave}
                            ondrop={(e) => handleDrop(e, dayInfo.date)}
                            role="button"
                            tabindex="0"
                            onkeydown={(e) => e.key === 'Enter' && openDayModal(dayInfo.date)}
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
                                            class:todo={slot.type === 'todo'}
                                            class:completed={slot.is_completed}
                                            style="background-color: {slot.is_completed ? desaturateColor(slot.color) : (slot.color || '#4285F4')};"
                                            onclick={(e) => { e.stopPropagation(); openModal(slot); }}
                                            draggable={slot.type === 'todo'}
                                            ondragstart={(e) => handleDragStart(e, slot)}
                                            ondragend={handleDragEnd}
                                            role="button"
                                            tabindex="0"
                                            onkeydown={(e) => e.key === 'Enter' && openModal(slot)}
                                        >
                                            {#if slot.isStart || !slot.isContinuedFromPrev}
                                                {#if slot.type === 'todo'}
                                                    <!-- svelte-ignore a11y_click_events_have_key_events -->
                                                    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
                                                    <label class="todo-checkbox" onclick={(e) => e.stopPropagation()}>
                                                        <input 
                                                            type="checkbox" 
                                                            checked={slot.is_completed}
                                                            onchange={(e) => handleToggleTodo(e, slot)}
                                                        />
                                                    </label>
                                                {/if}
                                                <span class="item-title" class:strike={slot.is_completed}>{slot.title}</span>
                                                <span class="tooltip">{slot.title}</span>
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

<DayDetailModal 
    bind:visible={showDayModal} 
    date={selectedDate}
    schedules={selectedDaySchedules}
    todos={selectedDayTodos}
    onAddTodo={handleAddTodo}
    onEditTodo={handleEditTodo}
    onTodoChange={handleTodoChange}
/>

<TodoFormModal 
    bind:visible={showTodoForm} 
    todo={editingTodo}
    initialDate={initialTodoDate}
    onSuccess={handleTodoFormSuccess}
/>

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

    /* 클릭 가능한 날짜 셀 */
    .calendar-day.clickable {
        cursor: pointer;
        transition: background-color 0.2s;
    }

    .calendar-day.clickable:hover {
        background: var(--bg-secondary);
    }

    /* 드래그 오버 상태 */
    .calendar-day.drag-over {
        background: var(--bg-tertiary);
        box-shadow: inset 0 0 0 2px var(--accent);
    }

    /* Todo 아이템 스타일 */
    .schedule-item.todo {
        cursor: grab;
    }

    .schedule-item.todo:active {
        cursor: grabbing;
    }

    .schedule-item.completed {
        opacity: 0.7;
    }

    /* 체크박스 스타일 */
    .todo-checkbox {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        width: 14px;
        height: 14px;
        margin-right: 4px;
        cursor: pointer;
    }

    .todo-checkbox input {
        width: 12px;
        height: 12px;
        margin: 0;
        cursor: pointer;
        accent-color: var(--text-primary);
    }

    /* 제목 텍스트 */
    .item-title {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .item-title.strike {
        text-decoration: line-through;
        opacity: 0.7;
    }

    /* 툴팁 */
    .schedule-item .tooltip {
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: var(--bg-primary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 0.75rem;
        white-space: nowrap;
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        z-index: 1000;
        pointer-events: none;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.15s, visibility 0.15s;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    .schedule-item:hover .tooltip {
        opacity: 1;
        visibility: visible;
    }
</style>
