<script>
	import { routes } from '$lib/routes.js';
	import { page } from '$app/stores';
	import { signOut } from '@auth/sveltekit/client';
	
	let { data } = $props();
	
	let currentPath = $state('');
	
	// 현재 페이지 경로를 감지 (클라이언트 사이드에서)
	if (typeof window !== 'undefined') {
		currentPath = window.location.pathname;
	}
</script>

<header>
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
				
				{#if data?.session?.user}
					<li class="nav-item">
						<div class="user-info">
							<span class="user-email">{data.session.user.email}</span>
							<button 
								class="logout-btn"
								onclick={() => signOut({ callbackUrl: '/auth/signin' })}
							>
								로그아웃
							</button>
						</div>
					</li>
				{/if}
			</ul>
		</nav>
	</div>
</header>

<style>
	header {
		background-color : rgba(255, 255, 255, 0.9);
		color: black;
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

	.user-info {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-left: 1rem;
		padding-left: 1rem;
		border-left: 1px solid rgba(255, 255, 255, 0.2);
	}

	.user-email {
		color: white;
		font-size: 0.9rem;
		opacity: 0.9;
	}

	.logout-btn {
		padding: 0.4rem 0.8rem;
		background: rgba(255, 255, 255, 0.1);
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 4px;
		font-size: 0.85rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.logout-btn:hover {
		background: rgba(255, 255, 255, 0.2);
		border-color: rgba(255, 255, 255, 0.3);
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