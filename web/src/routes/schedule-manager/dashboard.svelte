<script>
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
	import CalendarView from '$lib/components/schedule-manager/CalendarView.svelte';
	import WeeklyCalendarView from '$lib/components/schedule-manager/WeeklyCalendarView.svelte';
	import WeekCalendarRow from '$lib/components/schedule-manager/WeekCalendarRow.svelte';

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
	<div class="content">
		<WeeklyCalendarView year={currentYear} style="border: transparent; padding: 0px;" />
		<WeekCalendarRow style="border: transparent; padding: 0px;" />
	</div>
</div>
