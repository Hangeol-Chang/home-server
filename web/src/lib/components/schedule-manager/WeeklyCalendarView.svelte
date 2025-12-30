<script>
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';

	let { year = $bindable(new Date().getFullYear()) } = $props();

	// 임시 데이터: 실제로는 API에서 가져와야 함
	// startWeek, endWeek는 1~52 사이의 값
	let schedules = $state([
		{ id: 1, title: '1분기 프로젝트', startWeek: 2, endWeek: 12, color: '#FF6B6B' },
		{ id: 2, title: '해외 출장', startWeek: 18, endWeek: 19, color: '#4ECDC4' },
		{ id: 3, title: '여름 휴가', startWeek: 30, endWeek: 31, color: '#45B7D1' },
		{ id: 4, title: '하반기 프로젝트', startWeek: 35, endWeek: 48, color: '#FFA07A' },
		{ id: 5, title: '컨퍼런스', startWeek: 42, endWeek: 42, color: '#98D8C8' }
	]);

	const months = [
		'1월', '2월', '3월', '4월', '5월', '6월', 
		'7월', '8월', '9월', '10월', '11월', '12월'
	];

	let currentWeek = $state(0);

	onMount(() => {
		calculateCurrentWeek();
	});

	$effect(() => {
		// year가 변경되면 현재 주차 재계산
		calculateCurrentWeek();
	});

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
		
		return `left: ${left}%; width: ${width}%; background-color: ${schedule.color}`;
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
	</div>

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
		border-right: 1px solid #f0f0f0;
	}

	.grid-line:last-child {
		border-right: none;
	}

	.grid-line.active {
		background-color: rgba(99, 102, 241, 0.05);
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
