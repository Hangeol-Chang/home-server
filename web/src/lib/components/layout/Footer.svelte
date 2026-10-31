<script>
	import { device } from '$lib/stores/device';
</script>

<footer class="app-footer" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<div class="footer-content">
		<p>&copy; 2025 Home Server. All rights reserved.</p>
	</div>
</footer>

<style>
	.app-footer {
		background: var(--surface);
		border-top: 1px solid var(--line);
		margin-top: auto;
	}

	.footer-content {
		max-width: 1200px;
		margin: 0 auto;
		padding: 16px 24px;
		text-align: center;
	}

	.footer-content p {
		margin: 0;
		font-size: 0.85rem;
		color: var(--ink-muted);
	}

	/* Tablet/Mobile (< 768px) */
	.app-footer {
		&.tablet {
			.footer-content {
				padding: 12px 16px;

				p {
					font-size: 0.8rem;
				}
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			.footer-content {
				padding: 10px 12px;

				p {
					font-size: 0.75rem;
				}
			}
		}
	}
</style>
