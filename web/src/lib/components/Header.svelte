<script>
	import { routes } from '$lib/routes.js';
	
	let currentPath = '';
	
	// 현재 페이지 경로를 감지 (클라이언트 사이드에서)
	if (typeof window !== 'undefined') {
		currentPath = window.location.pathname;
	}
</script>

<header class="header">
	<div class="container">
		<div class="nav-brand">
			<h1><a href="/">Home Server</a></h1>
		</div>
		
		<nav class="nav-menu">
			<ul class="nav-list">
				{#each routes as route}
					<li class="nav-item">
						<a 
							href={route.path} 
							class="nav-link {currentPath === route.path ? 'active' : ''}"
						>
							{route.name}
						</a>
					</li>
				{/each}
			</ul>
		</nav>
	</div>
</header>

<style>
	.header {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1rem 0;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		position: sticky;
		top: 0;
		z-index: 1000;
	}

	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 1rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.nav-brand h1 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 700;
	}

	.nav-brand a {
		color: white;
		text-decoration: none;
		transition: opacity 0.2s;
	}

	.nav-brand a:hover {
		opacity: 0.8;
	}

	.nav-list {
		display: flex;
		list-style: none;
		margin: 0;
		padding: 0;
		gap: 2rem;
	}

	.nav-link {
		color: white;
		text-decoration: none;
		font-weight: 500;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		transition: all 0.2s;
	}

	.nav-link:hover {
		background: rgba(255, 255, 255, 0.1);
	}

	.nav-link.active {
		background: rgba(255, 255, 255, 0.2);
		font-weight: 600;
	}

	@media (max-width: 768px) {
		.container {
			flex-direction: column;
			gap: 1rem;
		}

		.nav-list {
			gap: 1rem;
		}

		.nav-link {
			padding: 0.25rem 0.5rem;
			font-size: 0.9rem;
		}
	}
</style>