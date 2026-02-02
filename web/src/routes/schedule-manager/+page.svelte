<script>
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
	import CalendarView from '$lib/components/schedule-manager/CalendarView.svelte';
	import WeeklyCalendarView from '$lib/components/schedule-manager/WeeklyCalendarView.svelte';
	import WeeklyTimetableView from '$lib/components/schedule-manager/WeeklyTimetableView.svelte';
    import ScheduleListView from '$lib/components/schedule-manager/ScheduleListView.svelte';
	import '$lib/styles/module.css';
	import '$lib/styles/module-common.css';

	// 상태 관리
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		// TODO: Load schedule data
		loading = false;
	});
</script>

<svelte:head>
	<title>일정 관리 - Home Server</title>
</svelte:head>

<div class="schedule-manager-page" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<!-- 헤더 -->
	<header class="page-header">
		<h1>📅 일정 관리</h1>
		<div class="header-actions">
            <a href="/schedule-manager/admin" class="admin-link">
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="12" cy="12" r="3"></circle>
					<path d="M12 1v6m0 6v6"></path>
					<path d="M1 12h6m6 0h6"></path>
				</svg>
				관리
			</a>
		</div>
	</header>

	<ScheduleListView />
	<WeeklyTimetableView />
	<WeeklyCalendarView />
	<CalendarView />
</div>

<style>
	.schedule-manager-page {
		max-width: 1400px;
		margin: 0 auto;
		padding: 20px;
	}

    .admin-link {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        background: var(--bg-secondary);
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        text-decoration: none;
        font-size: 0.9rem;
        transition: all 0.2s;
    }
    
    .admin-link:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }
</style>
