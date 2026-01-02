<script>
	import AssetManager_Dashboard from './asset-manager/dashboard.svelte';
	import ScheduleManager_Dashboard from './schedule-manager/dashboard.svelte';
	import { device } from '$lib/stores/device';
	import '$lib/styles/module.css';
	import '$lib/styles/module-common.css';
</script>

<svelte:head>
	<title>홈 - Home Server</title>
</svelte:head>

<div class="home-page" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<div class="dashboard-container">
		<!-- Asset Manager Dashboard -->
		<AssetManager_Dashboard />
	</div>

	<div class="dashboard-container">
		<!-- Schedule Manager Dashboard -->
		<ScheduleManager_Dashboard />
	</div>
</div>

<style>
	.home-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: 20px;
	}

	.dashboard-container {
		margin-bottom: 48px;
	}

	/* Tablet/Mobile (< 768px) */
	.home-page {
		&.tablet {
			padding: 8px;

			.dashboard-container {
				margin-bottom: 36px;
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			padding: 4px;
		}
	}
</style>
