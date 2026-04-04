<script>
	import AssetManager_Dashboard from './asset-manager/dashboard.svelte';
	import ScheduleManager_Dashboard from './schedule-manager/dashboard.svelte';
	import { device } from '$lib/stores/device';
	import '$lib/styles/module.css';
	import '$lib/styles/module-common.css';

	const modules = [
		{ name: 'Asset Manager', href: '/asset-manager', icon: '💰' },
		{ name: 'Schedule', href: '/schedule-manager', icon: '📅' },
		{ name: 'Notebook', href: '/notebook', icon: '📓' },
		{ name: 'Chat', href: '/chat', icon: '💬' },
		{ name: 'Google Drive', href: '/gdrive', icon: '☁️' },
		{ name: 'System Test', href: '/test', icon: '🛠️' }
	];
</script>

<svelte:head>
	<title>홈 - Home Server</title>
</svelte:head>

<div class="home-page" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<nav class="module-nav">
		{#each modules as mod}
			<a href={mod.href} class="module-btn">
				<span class="module-icon">{mod.icon}</span>
				<span class="module-name">{mod.name}</span>
			</a>
		{/each}
	</nav>

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

	.module-nav {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 12px;
		margin-bottom: 40px;
	}

	.module-btn {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 8px;
		padding: 20px 12px;
		border-radius: 4px;
		border: 1px solid transparent;
		background: var(--bg-primary-dark);
		text-decoration: none;
		color: var(--text-primary);

		transition: background 0.15s, border-color 0.15s, transform 0.1s;
		cursor: pointer;
	}

	.module-btn:hover {
		background: var(--bg-primary);
		border: 1px solid var(--border-color-dark);
		transform: translateY(-2px);
	}

	.module-icon {
		font-size: 28px;
		line-height: 1;
	}

	.module-name {
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.02em;
	}

	.dashboard-container {
		margin-bottom: 48px;
	}

	/* Tablet/Mobile (< 768px) */
	.home-page {
		&.tablet {
			padding: 8px;

			.module-nav {
				gap: 8px;
				margin-bottom: 28px;
			}

			.dashboard-container {
				margin-bottom: 36px;
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			padding: 4px;

			.module-nav {
				gap: 6px;
			}

			.module-btn {
				padding: 14px 8px;
			}

			.module-icon {
				font-size: 22px;
			}
		}
	}
</style>
