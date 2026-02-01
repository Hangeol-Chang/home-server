<script>
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
    import { CHART_COLORS } from '$lib/constants';

	let { year = $bindable(new Date().getFullYear()) ,
		style = ''
	} = $props();

    function getRandomColor() {
        return CHART_COLORS[Math.floor(Math.random() * CHART_COLORS.length)];
    }

	let schedules = $state([]);
    let showAddModal = $state(false);
    let showDetailModal = $state(false);
    let editingSchedule = $state(null);
    let newPlan = $state({
        title: '',
        description: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        color: getRandomColor()
    });

    function adjustColor(color, amount) {
        return '#' + color.replace(/^#/, '').replace(/../g, color => ('0'+Math.min(255, Math.max(0, parseInt(color, 16) + amount)).toString(16)).substr(-2));
    }

    const colorPalette = CHART_COLORS.map(color => [
        adjustColor(color, 40), // Light 2
        adjustColor(color, 20), // Light 1
        color,                  // Original
        adjustColor(color, -20), // Dark 1
        adjustColor(color, -40)  // Dark 2
    ]);

	const months = [
		'1월', '2월', '3월', '4월', '5월', '6월', 
		'7월', '8월', '9월', '10월', '11월', '12월'
	];

	let currentWeek = $state(0);

	onMount(async () => {
		calculateCurrentWeek();
        await fetchPlans();
	});

	$effect(() => {
		// year가 변경되면 현재 주차 재계산 및 데이터 다시 가져오기
		calculateCurrentWeek();
        fetchPlans();
	});

    async function fetchPlans() {
        try {
            const start = `${year}-01-01`;
            const end = `${year}-12-31`;
            const res = await fetch(`/api/schedule-manager/long-term-plans?start_date=${start}&end_date=${end}`);
            if (res.ok) {
                const plans = await res.json();
                schedules = plans.map(p => ({
                    ...p,
                    startWeek: getWeekNumber(new Date(p.start_date)),
                    endWeek: getWeekNumber(new Date(p.end_date))
                }));
            }
        } catch (e) {
            console.error(e);
        }
    }

    async function addPlan() {
        try {
            const res = await fetch('/api/schedule-manager/long-term-plans', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newPlan)
            });
            if (res.ok) {
                showAddModal = false;
                await fetchPlans();
                newPlan = {
                    title: '',
                    description: '',
                    start_date: new Date().toISOString().split('T')[0],
                    end_date: new Date().toISOString().split('T')[0],
                    color: getRandomColor()
                };
            }
        } catch (e) {
            console.error(e);
        }
    }

    function openDetailModal(schedule) {
        editingSchedule = { ...schedule };
        showDetailModal = true;
    }

    async function updatePlan() {
        if (!editingSchedule) return;
        try {
            const res = await fetch(`/api/schedule-manager/long-term-plans/${editingSchedule.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(editingSchedule)
            });
            if (res.ok) {
                showDetailModal = false;
                await fetchPlans();
            }
        } catch (e) {
            console.error(e);
        }
    }

    async function deletePlan() {
        if (!editingSchedule || !confirm('정말 삭제하시겠습니까?')) return;
        try {
            const res = await fetch(`/api/schedule-manager/long-term-plans/${editingSchedule.id}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                showDetailModal = false;
                await fetchPlans();
            }
        } catch (e) {
            console.error(e);
        }
    }

    function getWeekNumber(d) {
        d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
        d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay()||7));
        var yearStart = new Date(Date.UTC(d.getUTCFullYear(),0,1));
        var weekNo = Math.ceil(( ( (d - yearStart) / 86400000) + 1)/7);
        return weekNo;
    }

	function calculateCurrentWeek() {
		const now = new Date();
		// 현재 연도와 표시 연도가 다르면 현재 주차 표시 안함 (또는 해당 연도 기준 계산)
		if (now.getFullYear() !== year) {
			currentWeek = 0;
			return;
		}
		
		const start = new Date(year, 0, 1);
		const diff = now - start;
		const oneWeek = 1000 * 60 * 60 * 24 * 7;
		currentWeek = Math.floor(diff / oneWeek) + 1;
	}

	function getBarStyle(schedule) {
		const totalWeeks = 52;
		const start = Math.max(1, schedule.startWeek);
		const end = Math.min(52, schedule.endWeek);
		const duration = end - start + 1;
		
		const left = ((start - 1) / totalWeeks) * 100;
		const width = (duration / totalWeeks) * 100;
		
		return `left: ${left}%; width: ${width}%; background-color: ${schedule.color || '#3BBA9C'}`;
	}

	function changeYear(delta) {
		year += delta;
	}
</script>

<div class="section" class:tablet={$device.isTablet} style={style}>
	<div class="chart-header">
		<div class="month-nav">
			<button class="nav-btn" onclick={() => changeYear(-1)} aria-label="이전 해">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="15 18 9 12 15 6"></polyline>
				</svg>
			</button>
			<a href="/schedule-manager">
				<h3>📅 {year}년 연간 일정</h3>
			</a>
			<button class="nav-btn" onclick={() => changeYear(1)} aria-label="다음 해">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="9 18 15 12 9 6"></polyline>
				</svg>
			</button>
		</div>
        <button class="add-btn" onclick={() => showAddModal = true}>+ 일정 추가</button>
	</div>

    {#if showAddModal}
        <div role="none" class="modal-overlay" onclick={() => showAddModal = false}>
            <div role="none" class="modal-container" onclick={(e) => e.stopPropagation()}>
				<div class="chart-header">
					<h3>🗓️ 새 장기 일정</h3>
				</div>
					
                <div class="form-group">
                    <label for="title">제목</label>
                    <input id="title" type="text" bind:value={newPlan.title} placeholder="예: 1분기 프로젝트" />
                </div>
                <div class="form-row">
					<div class="form-group">
						<label for="start_date">시작 날짜</label>
						<input 
							id="start_date" type="date" 
							onclick={(e) => e.currentTarget.showPicker()}
							bind:value={newPlan.start_date} 
						/>
					</div>
					<div class="form-group">
						<label for="end_date">종료 날짜</label>
						<input 
							id="end_date" type="date" 
							onclick={(e) => e.currentTarget.showPicker()}
							bind:value={newPlan.end_date} 
						/>
					</div>
                </div>
                <div class="form-group">
                    <label for="color">색상</label>
                    <div class="color-palette-container">
                        <div class="color-palette">
                            {#each colorPalette as shades}
                                <div class="color-column">
                                    {#each shades as shade}
                                        <button 
                                            class="color-chip" 
                                            class:selected={newPlan.color === shade}
                                            style="background-color: {shade}"
                                            onclick={() => newPlan.color = shade}
                                            aria-label="Select color {shade}"
                                        ></button>
                                    {/each}
                                </div>
                            {/each}
                        </div>
                    </div>
                </div>
                <div class="form-group">
                    <label for="description">설명</label>
					<textarea 
						id="description" 
						bind:value={newPlan.description} 
						placeholder="일정에 대한 설명을 입력하세요..."
						rows="4"
					></textarea>
                </div>
                <div class="form-actions">
                    <button class="btn-cancel" onclick={() => showAddModal = false}>취소</button>
                    <button class="btn-submit" onclick={addPlan}>저장</button>
                </div>
            </div>
        </div>
    {/if}

    {#if showDetailModal && editingSchedule}
        <div role="none" class="modal-overlay" onclick={() => showDetailModal = false}>
            <div role="none" class="modal-container" onclick={(e) => e.stopPropagation()}>
				<div class="chart-header">
					<h3>✏️ 일정 상세 / 수정</h3>
                    <button class="delete-btn" onclick={deletePlan} aria-label="삭제">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
				</div>
					
                <div class="form-group">
                    <label for="edit-title">제목</label>
                    <input id="edit-title" type="text" bind:value={editingSchedule.title} />
                </div>
                <div class="form-row">
					<div class="form-group">
						<label for="edit-start_date">시작 날짜</label>
						<input id="edit-start_date" type="date" bind:value={editingSchedule.start_date} />
					</div>
					<div class="form-group">
						<label for="edit-end_date">종료 날짜</label>
						<input id="edit-end_date" type="date" bind:value={editingSchedule.end_date} />
					</div>
                </div>
                <div class="form-group">
                    <label for="edit-color">색상</label>
                    <div class="color-palette-container">
                        <div class="color-palette">
                            {#each colorPalette as shades}
                                <div class="color-column">
                                    {#each shades as shade}
                                        <button 
                                            class="color-chip" 
                                            class:selected={editingSchedule.color === shade}
                                            style="background-color: {shade}"
                                            onclick={() => editingSchedule.color = shade}
                                            aria-label="Select color {shade}"
                                        ></button>
                                    {/each}
                                </div>
                            {/each}
                        </div>
                    </div>
                </div>
                <div class="form-group">
                    <label for="edit-description">설명</label>
					<textarea 
						id="edit-description" 
						bind:value={editingSchedule.description} 
						rows="4"
					></textarea>
                </div>
                <div class="form-actions">
                    <button class="btn-cancel" onclick={() => showDetailModal = false}>취소</button>
                    <button class="btn-submit" onclick={updatePlan}>수정 저장</button>
                </div>
            </div>
        </div>
    {/if}

	<div class="calendar-scroll-area">
		<div class="timeline-container">
			<!-- Month Header -->
			<div class="months-row">
				{#each months as month}
					<div class="month-label">{month}</div>
				{/each}
			</div>

			<!-- Grid & Bars -->
			<div class="grid-area">
				<!-- Vertical Grid Lines (52 weeks) -->
				<div class="grid-lines">
					{#each Array(52) as _, i}
						<div class="grid-line" class:active={i + 1 === currentWeek}></div>
					{/each}
				</div>

				<!-- Schedule Bars -->
				<div class="tracks">
					{#each schedules as schedule}
						<div class="track-row">
							<div 
                                role="button"
                                tabindex="0"
								class="schedule-bar" 
								style={getBarStyle(schedule)}
								title="{schedule.title} (W{schedule.startWeek}~W{schedule.endWeek})"
                                onclick={() => openDetailModal(schedule)}
                                onkeydown={(e) => e.key === 'Enter' && openDetailModal(schedule)}
							>
								<span class="bar-label">{schedule.title}</span>
							</div>
						</div>
					{/each}
				</div>
				
				<!-- Current Week Indicator -->
				{#if currentWeek > 0 && currentWeek <= 52}
					<div 
						class="current-week-line" 
						style="left: {((currentWeek - 1) / 52) * 100}%"
						title="이번 주"
					></div>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.calendar-scroll-area {
		width: 100%;
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
	}

	.timeline-container {
		width: 100%;
		position: relative;
	}

	/* Tablet & Mobile: Show 6 months (200% width) */
	.tablet .timeline-container {
		width: 200%;
	}

	.months-row {
		display: flex;
		border-bottom: 1px solid var(--border-color);
		margin-bottom: 8px;
	}

	.month-label {
		flex: 1;
		text-align: center;
		font-size: 0.85rem;
		color: var(--text-secondary);
		padding-bottom: 8px;
		border-right: 1px dashed var(--border-color);
	}

	.month-label:last-child {
		border-right: none;
	}

	.grid-area {
		position: relative;
		min-height: 200px;
		padding-top: 10px;
	}

	.grid-lines {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		display: flex;
		pointer-events: none;
	}

	.grid-line:nth-child(4n) {
		border-right: 1px solid var(--border-color);
	}

	.grid-line {
		flex: 1;
		border-right: 1px solid var(--border-color-light);
	}

	.grid-line:last-child {
		border-right: none;
	}

	.grid-line.active {
		background-color: var(--bg-tertiary);
	}

	.tracks {
		position: relative;
		display: flex;
		flex-direction: column;
		gap: 8px;
		z-index: 1;
	}

	.track-row {
		position: relative;
		height: 24px;
		width: 100%;
	}

	.schedule-bar {
		position: absolute;
		height: 100%;
		border-radius: 2px;
		display: flex;
		align-items: center;
		padding: 0 8px;
		color: white;
		font-size: 0.75rem;
		font-weight: 400;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		transition: transform 0.2s;
		cursor: pointer;
	}

	.schedule-bar:hover {
		transform: scaleY(1.1);
		z-index: 2;
	}

	.current-week-line {
		position: absolute;
		top: 0;
		bottom: 0;
		width: 2px;
		background-color: var(--accent);
		z-index: 10;
		pointer-events: none;
	}

	.current-week-line::after {
		content: '';
		position: absolute;
		top: -4px;
		left: -3px;
		width: 8px;
		height: 8px;
		background-color: var(--accent);
		border-radius: 50%;
	}

    .color-palette-container {
        overflow-x: auto;
        padding-bottom: 8px;
    }

    .color-palette {
        display: flex;
        gap: 4px;
        min-width: max-content;
		padding: 8px 0;
    }

    .color-column {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .color-chip {
        width: 20px;
        height: 20px;
        border-radius: 2px;
        border: 2px solid transparent;
        cursor: pointer;
        transition: transform 0.1s;
        padding: 0;
    }

    .color-chip:hover {
        transform: scale(1.1);
        z-index: 1;
    }

    .color-chip.selected {
        transform: scale(1.1);
        box-shadow: 0 0 0 1px var(--bg-primary), 0 0 0 3px var(--text-primary);
        z-index: 2;
    }

    .delete-btn {
        background: none;
        border: none;
        color: var(--text-danger);
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .delete-btn:hover {
        background: rgba(244, 67, 54, 0.1);
    }
</style>
