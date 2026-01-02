<script>
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
    import { fade } from 'svelte/transition';

	let { year = $bindable(new Date().getFullYear()) } = $props();

	let schedules = $state([]);
    let showAddModal = $state(false);
    let newPlan = $state({
        title: '',
        description: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        color: '#3BBA9C'
    });

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
                    color: '#3BBA9C'
                };
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

<div class="section" class:tablet={$device.isTablet}>
	<div class="chart-header">
		<div class="month-nav">
			<button class="nav-btn" onclick={() => changeYear(-1)} aria-label="이전 해">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="15 18 9 12 15 6"></polyline>
				</svg>
			</button>
			<h3>📅 {year}년 연간 일정</h3>
			<button class="nav-btn" onclick={() => changeYear(1)} aria-label="다음 해">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="9 18 15 12 9 6"></polyline>
				</svg>
			</button>
		</div>
        <button class="add-btn" onclick={() => showAddModal = true}>+ 일정 추가</button>
	</div>

    {#if showAddModal}
        <div class="modal-backdrop" transition:fade onclick={() => showAddModal = false}>
            <div class="modal" onclick={(e) => e.stopPropagation()}>
                <h4>새 장기 일정</h4>
                <div class="form-group">
                    <label>제목</label>
                    <input type="text" bind:value={newPlan.title} placeholder="예: 1분기 프로젝트" />
                </div>
                <div class="form-group">
                    <label>기간</label>
                    <div class="date-range">
                        <input type="date" bind:value={newPlan.start_date} />
                        <span>~</span>
                        <input type="date" bind:value={newPlan.end_date} />
                    </div>
                </div>
                <div class="form-group">
                    <label>색상</label>
                    <input type="color" bind:value={newPlan.color} />
                </div>
                <div class="form-group">
                    <label>설명</label>
                    <input type="text" bind:value={newPlan.description} />
                </div>
                <div class="actions">
                    <button class="cancel-btn" onclick={() => showAddModal = false}>취소</button>
                    <button class="save-btn" onclick={addPlan}>저장</button>
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
								class="schedule-bar" 
								style={getBarStyle(schedule)}
								title="{schedule.title} (W{schedule.startWeek}~W{schedule.endWeek})"
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

	.grid-line {
		flex: 1;
		border-right: 1px solid var(--border-color);
	}

	.grid-line:last-child {
		border-right: none;
	}

    /* .add-btn is defined in module-common.css */

    .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }

    .modal {
        background: var(--bg-primary);
        padding: 2rem;
        border-radius: 12px;
        width: 90%;
        max-width: 400px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        border: 1px solid var(--border-color);
    }
    
    .modal h4 {
        margin-top: 0;
        margin-bottom: 1.5rem;
        color: var(--text-primary);
    }

    .form-group {
        margin-bottom: 1rem;
    }

    .form-group label {
        display: block;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        color: var(--text-secondary);
    }

    .form-group input {
        width: 100%;
        padding: 0.5rem;
        border-radius: 6px;
        border: 1px solid var(--border-color);
        background: var(--bg-secondary);
        color: var(--text-primary);
    }
    
    .form-group input:focus {
        outline: none;
        border-color: var(--accent);
    }

    .date-range {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .date-range span {
        color: var(--text-secondary);
    }

    .actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 1.5rem;
    }

    .actions button {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        border: none;
        cursor: pointer;
        font-weight: 500;
    }

    .save-btn {
        background: var(--accent);
        color: var(--text-primary);
    }
    
    .save-btn:hover {
        background: var(--accent-hover);
    }

    .cancel-btn {
        background: var(--bg-tertiary);
        color: var(--text-secondary);
    }
    
    .cancel-btn:hover {
        background: var(--bg-secondary);
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
		border-radius: 4px;
		display: flex;
		align-items: center;
		padding: 0 8px;
		color: white;
		font-size: 0.75rem;
		font-weight: 600;
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
</style>
