<script>
	import { onMount } from 'svelte';
	import axios from 'axios';
	
	let backendStatus = 'checking';
	let submodules = [
		{ name: 'Asset Manager', port: 5174, path: '/asset-manager', status: 'checking', description: '자산 및 거래 관리' },
		{ name: 'Schedule Manager', port: 5175, path: '/schedule-manager', status: 'checking', description: '일정 및 작업 관리' }
	];
	
	async function checkBackendStatus() {
		try {
			const response = await axios.get('/api/');
			backendStatus = 'online';
		} catch (error) {
			try {
				// API 프록시가 안되면 직접 확인
				const response = await axios.get('http://localhost:5000/');
				backendStatus = 'online';
			} catch (directError) {
				backendStatus = 'offline';
			}
		}
	}
	
	async function checkSubmoduleStatus(submodule) {
		try {
			const response = await fetch(`http://localhost:${submodule.port}/`);
			return response.ok ? 'online' : 'offline';
		} catch (error) {
			return 'offline';
		}
	}
	
	onMount(async () => {
		await checkBackendStatus();
		
		// 서브모듈 상태 확인
		for (let i = 0; i < submodules.length; i++) {
			submodules[i].status = await checkSubmoduleStatus(submodules[i]);
		}
		submodules = [...submodules]; // 반응성 트리거
	});
	
	function openSubmodule(submodule) {
		if (submodule.name === 'Asset Manager') {
			window.location.href = '/asset-manager';
		} else if (submodule.name === 'Schedule Manager') {
			window.location.href = '/schedule-manager';
		} else {
			// 기존 방식으로 폴백
			window.open(`http://localhost:${submodule.port}`, '_blank');
		}
	}
	
	function openAPI() {
		window.open('http://localhost:5000/docs', '_blank');
	}
</script>

<svelte:head>
	<title>Home Server Dashboard</title>
</svelte:head>

<main>
	<header>
		<h1>🏠 Home Server Dashboard</h1>
		<p>통합 홈 서버 관리 대시보드</p>
	</header>

	<section class="status-section">
		<h2>📊 시스템 상태</h2>
		
		<div class="status-grid">
			<!-- Backend Status -->
			<div class="status-card">
				<div class="status-header">
					<h3>🔧 Backend API</h3>
					<span class="status-badge status-{backendStatus}">{backendStatus}</span>
				</div>
				<p>FastAPI 백엔드 서버</p>
				<div class="actions">
					<button on:click={openAPI} disabled={backendStatus !== 'online'}>
						API 문서 보기
					</button>
				</div>
			</div>
			
			<!-- Frontend Status -->
			<div class="status-card">
				<div class="status-header">
					<h3>🎨 Frontend</h3>
					<span class="status-badge status-online">online</span>
				</div>
				<p>SvelteKit 프론트엔드</p>
				<div class="port-info">Port: 5173</div>
			</div>
		</div>
	</section>

	<section class="modules-section">
		<h2>🧩 서브모듈</h2>
		
		<div class="modules-grid">
			{#each submodules as submodule}
				<div class="module-card">
					<div class="module-header">
						<h3>{submodule.name}</h3>
						<span class="status-badge status-{submodule.status}">{submodule.status}</span>
					</div>
					<p>{submodule.description}</p>
					<div class="module-info">
						<div class="port-info">Port: {submodule.port}</div>
						<div class="path-info">Path: {submodule.path}</div>
					</div>
					<div class="actions">
						<button 
							on:click={() => openSubmodule(submodule)} 
							disabled={submodule.status !== 'online'}
							class="primary"
						>
							모듈 열기
						</button>
					</div>
				</div>
			{/each}
		</div>
	</section>

	<section class="quick-actions">
		<h2>⚡ 빠른 작업</h2>
		<div class="actions-grid">
			<button on:click={openAPI} disabled={backendStatus !== 'online'}>
				📚 API 문서
			</button>
			<button on:click={() => window.location.href = '/asset-manager'}>
				💰 자산 관리
			</button>
			<button on:click={() => window.location.href = '/schedule-manager'}>
				📅 일정 관리
			</button>
		</div>
	</section>
</main>

<style>
	main {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		min-height: 100vh;
		color: white;
	}
	
	header {
		text-align: center;
		margin-bottom: 3rem;
	}
	
	header h1 {
		font-size: 3rem;
		margin: 0;
		text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
	}
	
	header p {
		font-size: 1.2rem;
		opacity: 0.9;
		margin: 0.5rem 0 0 0;
	}
	
	section {
		margin-bottom: 3rem;
	}
	
	section h2 {
		font-size: 1.5rem;
		margin-bottom: 1.5rem;
		text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
	}
	
	.status-grid, .modules-grid {
		display: grid;
		gap: 1.5rem;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	}
	
	.status-card, .module-card {
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		border-radius: 12px;
		padding: 1.5rem;
		border: 1px solid rgba(255, 255, 255, 0.2);
		transition: transform 0.2s ease, box-shadow 0.2s ease;
	}
	
	.status-card:hover, .module-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 25px rgba(0,0,0,0.15);
	}
	
	.status-header, .module-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.status-header h3, .module-header h3 {
		margin: 0;
		font-size: 1.2rem;
	}
	
	.status-badge {
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.8rem;
		font-weight: bold;
		text-transform: uppercase;
	}
	
	.status-online {
		background: #10b981;
		color: white;
	}
	
	.status-offline {
		background: #ef4444;
		color: white;
	}
	
	.status-checking {
		background: #f59e0b;
		color: white;
	}
	
	.module-info {
		margin: 1rem 0;
		font-size: 0.9rem;
		opacity: 0.8;
	}
	
	.port-info, .path-info {
		margin: 0.25rem 0;
	}
	
	.actions {
		margin-top: 1rem;
	}
	
	.actions-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}
	
	button {
		background: rgba(255, 255, 255, 0.2);
		border: 1px solid rgba(255, 255, 255, 0.3);
		color: white;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.9rem;
		transition: all 0.2s ease;
	}
	
	button:hover:not(:disabled) {
		background: rgba(255, 255, 255, 0.3);
		transform: translateY(-1px);
	}
	
	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	button.primary {
		background: #3b82f6;
		border-color: #3b82f6;
	}
	
	button.primary:hover:not(:disabled) {
		background: #2563eb;
		border-color: #2563eb;
	}
	
	.quick-actions .actions-grid button {
		padding: 1rem;
		font-size: 1rem;
		font-weight: 500;
	}
</style>
