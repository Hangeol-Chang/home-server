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

	.quick-links h2 {
		margin: 0 0 24px 0;
		font-size: 1.5rem;
		color: var(--text-primary);
	}

	.links-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 20px;
	}

	.link-card {
		display: block;
		background: var(--bg-primary);
		border: 2px solid var(--border-color);
		border-radius: 12px;
		padding: 32px 24px;
		text-decoration: none;
		transition: all 0.3s;
		text-align: center;
	}

	.link-card:hover {
		transform: translateY(-4px);
		box-shadow: var(--shadow-lg);
		border-color: var(--accent);
	}

	.link-icon {
		font-size: 3rem;
		margin-bottom: 16px;
	}

	.link-card h3 {
		margin: 0 0 8px 0;
		font-size: 1.3rem;
		color: var(--text-primary);
	}

	.link-card p {
		margin: 0;
		color: var(--text-tertiary);
		font-size: 0.95rem;
	}

	/* Tablet/Mobile (< 768px) */
	.home-page {
		&.tablet {
			padding: 16px;

			.dashboard-container {
				margin-bottom: 36px;
			}

			.quick-links h2 {
				font-size: 1.3rem;
				margin-bottom: 16px;
			}

			.links-grid {
				grid-template-columns: 1fr;
				gap: 16px;
			}

			.link-card {
				padding: 24px 20px;

				h3 {
					font-size: 1.2rem;
				}

				p {
					font-size: 0.9rem;
				}
			}

			.link-icon {
				font-size: 2.5rem;
				margin-bottom: 12px;
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			padding: 8px;

			.quick-links h2 {
				font-size: 1.2rem;
			}

			.link-card {
				padding: 20px 16px;

				h3 {
					font-size: 1.1rem;
				}

				p {
					font-size: 0.85rem;
				}
			}

			.link-icon {
				font-size: 2.2rem;
			}
		}
	}
</style>
