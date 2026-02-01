<script>
	import { device } from '$lib/stores/device';
	import { getGoogleEventsForWeek, getTodos, moveTodo, toggleTodoCompletion } from '$lib/api/schedule-manager.js';
	import ScheduleDetailModal from './ScheduleDetailModal.svelte';
	import DayDetailModal from './DayDetailModal.svelte';
	import TodoFormModal from './TodoFormModal.svelte';
	let { style = '' } = $props();

	let loading = $state(false);

	// Schedule Detail Modal State
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

	// 현재 표시 중인 주의 기준 날짜 (해당 주의 일요일)
	let weekOffset = $state(0);
	
	// 로드된 할일 목록
	let loadedTodos = $state([]);

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
			const [fetchedSchedules, fetchedTodos] = await Promise.all([
				getGoogleEventsForWeek(startDate, endDate),
				getTodos(startDate, endDate)
			]);
			loadedTodos = fetchedTodos.map(t => ({ ...t, source: 'todo', type: 'todo' }));
			const allItems = [
				...fetchedSchedules.map(s => ({ ...s, type: 'schedule' })),
				...loadedTodos
			];
			weekDates = assignSchedulesToSlots(dates, allItems);
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
		selectedDaySchedules = weekDates.find(d => d.date === dateStr)?.slots
			?.filter(s => s && s.type === 'schedule')
			?.map(s => ({ ...s, type: s.source || 'Google Calendar' })) || [];
		selectedDayTodos = loadedTodos.filter(t => 
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
		const dates = getWeekDates(weekOffset);
		await loadDataForWeek(dates);
	}
	
	async function handleTodoChange() {
		const dates = getWeekDates(weekOffset);
		await loadDataForWeek(dates);
		// Day modal 데이터 갱신
		if (selectedDate) {
			selectedDayTodos = loadedTodos.filter(t => 
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
		
		const originalStart = new Date(todo.start_date);
		const targetDate = new Date(targetDateStr);
		const daysDiff = Math.round((targetDate - originalStart) / (1000 * 60 * 60 * 24));
		
		if (daysDiff === 0) return;
		
		const newStart = new Date(originalStart);
		newStart.setDate(newStart.getDate() + daysDiff);
		const newEnd = new Date(todo.end_date);
		newEnd.setDate(newEnd.getDate() + daysDiff);
		
		const newStartStr = newStart.toISOString().split('T')[0];
		const newEndStr = newEnd.toISOString().split('T')[0];
		
		try {
			await moveTodo(todo.id, newStartStr, newEndStr);
			const dates = getWeekDates(weekOffset);
			await loadDataForWeek(dates);
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
			const dates = getWeekDates(weekOffset);
			await loadDataForWeek(dates);
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
		// 채도를 15%로 낮추고, 명도를 약간 높임
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
						class:drag-over={dragOverDate === dayInfo.date}
						onclick={() => openDayModal(dayInfo.date)}
						ondragover={(e) => handleDragOver(e, dayInfo.date)}
						ondragleave={handleDragLeave}
						ondrop={(e) => handleDrop(e, dayInfo.date)}
						role="button"
						tabindex="0"
						onkeydown={(e) => e.key === 'Enter' && openDayModal(dayInfo.date)}
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
										class:todo={slot.type === 'todo'}
										class:completed={slot.is_completed}
										style="background-color: {slot.is_completed ? desaturateColor(slot.color) : (slot.color || '#4285F4')};"
										onclick={(e) => { e.stopPropagation(); openModal(slot); }}
										draggable={slot.type === 'todo'}
										ondragstart={(e) => handleDragStart(e, slot)}
										ondragend={handleDragEnd}
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

	/* 클릭 가능한 날짜 셀 */
	.calendar-day {
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.calendar-day:hover {
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
