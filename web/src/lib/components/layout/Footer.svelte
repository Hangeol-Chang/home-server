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
		background: #f8f9fa;
		border-top: 1px solid #e0e0e0;
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
		color: #666;
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
