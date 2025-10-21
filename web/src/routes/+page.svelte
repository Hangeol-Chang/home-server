<script>
	import Dashboard from './asset-manager/dashboard.svelte';
</script>

<svelte:head>
	<title>홈 - Home Server</title>
</svelte:head>

<div class="home-page">
	<header class="welcome-section">
		<h1>환영합니다! 🏠</h1>
		<p>Home Server에서 자산과 일정을 관리하세요</p>
	</header>

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

	.welcome-section {
		text-align: center;
		margin-bottom: 48px;
		padding: 40px 20px;
		background: linear-gradient(135deg, var(--color-lightest), var(--color-light));
		border-radius: 16px;
	}

	.welcome-section h1 {
		margin: 0 0 12px 0;
		font-size: 2.5rem;
		color: var(--text-primary);
	}

	.welcome-section p {
		margin: 0;
		font-size: 1.1rem;
		color: var(--text-secondary);
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

	@media (max-width: 768px) {
		.welcome-section h1 {
			font-size: 2rem;
		}

		.links-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
