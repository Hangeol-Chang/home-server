<script>
	import { onMount } from 'svelte';
	import { useModules } from '$lib/stores/modules';
	
	let availableModules = $state([]);
	let loading = $state(true);
	
	// 동적으로 모든 sub-module 발견
	const moduleComponents = import.meta.glob('$modules/*/web/src/routes/+page.svelte');

	onMount(() => {
		useModules().subscribe(modules => {
			availableModules = modules;
			loading = false;
		});
	});
</script>

<div class="home">
	<header class="hero">
		<h1>🏠 Home Server</h1>
		<p class="subtitle">통합 관리 시스템</p>
	</header>
	
	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>모듈을 검색하는 중...</p>
		</div>
	{:else if availableModules.length > 0}
		<section class="modules">
			<h2>사용 가능한 모듈</h2>
			<div class="module-grid">
				{#each availableModules as module}
					<div class="module-card">
						<h3>
							<a href={module.path}>{module.displayName}</a>
						</h3>
						<p class="module-id">ID: {module.name}</p>
						
						{#if module.routes.length > 0}
							<div class="routes">
								<h4>페이지:</h4>
								<ul>
									{#each module.routes as route}
										<li>
											<a href={route.path}>{route.name}</a>
										</li>
									{/each}
								</ul>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</section>
	{:else}
		<div class="no-modules">
			<h2>📦 모듈을 찾을 수 없습니다</h2>
			<p>modules/ 디렉토리에서 사용 가능한 웹 모듈이 없습니다.</p>
		</div>
	{/if}
</div>

<style>
	.home {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
	}
	
	.hero {
		text-align: center;
		margin-bottom: 3rem;
		padding: 2rem 0;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-radius: 15px;
	}
	
	.hero h1 {
		font-size: 3rem;
		margin-bottom: 0.5rem;
		font-weight: 700;
	}
	
	.subtitle {
		font-size: 1.25rem;
		opacity: 0.9;
		font-weight: 300;
	}
	
	.loading {
		text-align: center;
		padding: 2rem;
	}
	
	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid #f3f4f6;
		border-top: 4px solid #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	.modules h2 {
		color: #1f2937;
		margin-bottom: 2rem;
		font-size: 2rem;
		text-align: center;
	}
	
	.module-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 2rem;
	}
	
	.module-card {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 12px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		transition: all 0.3s ease;
	}
	
	.module-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
	}
	
	.module-card h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1.5rem;
	}
	
	.module-card h3 a {
		color: #3b82f6;
		text-decoration: none;
	}
	
	.module-card h3 a:hover {
		text-decoration: underline;
	}
	
	.module-id {
		color: #6b7280;
		font-size: 0.875rem;
		margin-bottom: 1rem;
		font-family: 'Courier New', monospace;
		background: #f3f4f6;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		display: inline-block;
	}
	
	.routes h4 {
		color: #374151;
		margin: 0 0 0.5rem 0;
		font-size: 1rem;
	}
	
	.routes ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	
	.routes li {
		margin-bottom: 0.5rem;
	}
	
	.routes a {
		color: #6366f1;
		text-decoration: none;
		font-size: 0.9rem;
		padding: 0.25rem 0.5rem;
		background: #f8fafc;
		border-radius: 4px;
		display: inline-block;
		transition: background 0.2s;
	}
	
	.routes a:hover {
		background: #e2e8f0;
		text-decoration: underline;
	}
	
	.no-modules {
		text-align: center;
		padding: 3rem 2rem;
		color: #6b7280;
	}
	
	.no-modules h2 {
		color: #374151;
		margin-bottom: 1rem;
	}
	
	@media (max-width: 768px) {
		.hero h1 {
			font-size: 2rem;
		}
		
		.module-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
