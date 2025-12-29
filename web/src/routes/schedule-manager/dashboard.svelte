<script>
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
	import CalendarView from '$lib/components/schedule-manager/CalendarView.svelte';
	import WeeklyCalendarView from '$lib/components/schedule-manager/WeeklyCalendarView.svelte';

	// 상태 관리
	let loading = $state(true);
	let error = $state('');

	const now = new Date();
	let currentYear = $state(now.getFullYear());
	let currentMonth = $state(now.getMonth() + 1);

	onMount(async () => {
		// TODO: Load schedule summary
		loading = false;
	});
</script>

<div class="section" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<div class="chart-header">
		<h3><a href="/schedule-manager" style="text-decoration: none; color: inherit;">📅 Schedule Manager</a></h3>
		<div class="header-actions">
			<button class="add-btn" title="일정 등록">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path d="M12 5v14m-7-7h14" stroke-width="2" stroke-linecap="round" />
				</svg>
				<span>일정 등록</span>
			</button>
		</div>
	</div>
	
	<div class="content">
		<WeeklyCalendarView year={currentYear} />
	</div>
</div>
