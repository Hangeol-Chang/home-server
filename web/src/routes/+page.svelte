<script>
	import Dashboard from './asset-manager/dashboard.svelte';
	import { device } from '$lib/stores/device';
</script>

<svelte:head>
	<title>홈 - Home Server</title>
</svelte:head>

<div class="home-page" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<div class="dashboard-container">
		<!-- Dashboard 표시 -->
		<Dashboard />
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
			padding: 16px;

			.dashboard-container {
				margin-bottom: 36px;
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			padding: 8px;
		}
	}
</style>
