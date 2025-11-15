<script>
	import Dashboard from './asset-manager/dashboard.svelte';
</script>

<svelte:head>
	<title>홈 - Home Server</title>
</svelte:head>

<div class="home-page">
	<div class="dashboard-container">
		<!-- compact 모드로 Dashboard 표시 -->
		<Dashboard compact={true} />
	</div>

	<div class="quick-links">
		<h2>빠른 링크</h2>
		<div class="links-grid">
			<a href="/asset-manager" class="link-card">
				<div class="link-icon">💰</div>
				<h3>자산 관리</h3>
				<p>자산을 추가하고 관리하세요</p>
			</a>
			<a href="/schedule-manager" class="link-card">
				<div class="link-icon">📅</div>
				<h3>일정 관리</h3>
				<p>일정을 확인하고 추가하세요</p>
			</a>
		</div>
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

	/* 태블릿 */
	@media (max-width: 1024px) {
		.home-page {
			padding: 16px;
		}

		.dashboard-container {
			margin-bottom: 36px;
		}
	}

	/* 모바일 */
	@media (max-width: 768px) {
		.home-page {
			padding: 12px;
		}

		.dashboard-container {
			margin-bottom: 24px;
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
		}

		.link-icon {
			font-size: 2.5rem;
			margin-bottom: 12px;
		}

		.link-card h3 {
			font-size: 1.2rem;
		}

		.link-card p {
			font-size: 0.9rem;
		}
	}

	/* 모바일 소형 */
	@media (max-width: 480px) {
		.home-page {
			padding: 8px;
		}

		.quick-links h2 {
			font-size: 1.2rem;
		}

		.link-card {
			padding: 20px 16px;
		}

		.link-icon {
			font-size: 2.2rem;
		}

		.link-card h3 {
			font-size: 1.1rem;
		}

		.link-card p {
			font-size: 0.85rem;
		}
	}
</style>
