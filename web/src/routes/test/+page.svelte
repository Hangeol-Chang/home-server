<script>
	import { checkDiscordWebhook } from '$lib/api/test.js';

	// 상태 변수
	let isDiscordLoading = $state(false);
	let discordResult = $state(null);
	let discordError = $state(null);

	// 여러 테스트들을 배열이나 개별 함수로 관리하여 추후 확장이 용이하도록 설정
	async function runDiscordWebhookTest() {
		isDiscordLoading = true;
		discordResult = null;
		discordError = null;

		try {
			const res = await checkDiscordWebhook();
			discordResult = res.message;
		} catch (err) {
			discordError = err.message || '알 수 없는 오류가 발생했습니다.';
		} finally {
			isDiscordLoading = false;
		}
	}
</script>

<svelte:head>
	<title>시스템 테스트 | Home Server</title>
</svelte:head>

<div class="test-page-container">
	<header class="page-header">
		<h1>🛠️ 시스템 테스트 대시보드</h1>
		<p class="subtitle">서버의 여러 기능과 서비스 연동을 테스트할 수 있는 관리자 페이지입니다.</p>
	</header>

	<div class="test-card-grid">
		<!-- 디스코드 웹훅 테스트 카드 -->
		<section class="test-card">
			<div class="card-header">
				<h2><span class="icon">💬</span> 디스코드(Discord) 웹훅</h2>
			</div>
			
			<div class="card-body">
				<p class="description">
					<code>.env</code> 파일에 설정된 <code>DISCORD_WEBHOOK_URL</code>을 사용하여
					정상적으로 메시지가 전송되는지 확인합니다.
				</p>
				
				<div class="action-area">
					<button 
						class="btn-run-test" 
						onclick={runDiscordWebhookTest} 
						disabled={isDiscordLoading}
					>
						{#if isDiscordLoading}
							<span class="spinner"></span> 테스트 중...
						{:else}
							<span>전송 테스트 실행 ▶</span>
						{/if}
					</button>
				</div>
                
                <!-- 결과 표시 영역 -->
				{#if discordResult}
					<div class="result-box success">
						<pre>✅ {discordResult}</pre>
					</div>
				{/if}

				{#if discordError}
					<div class="result-box error">
						<pre>❌ {discordError}</pre>
					</div>
				{/if}
			</div>
		</section>

		<!-- 앞으로 추가될 다른 테스트 기능들을 위한 더미 카드 -->
		<section class="test-card placeholder">
			<div class="card-header">
				<h2><span class="icon">🗂️</span> 추가 시스템 테스트 (예정)</h2>
			</div>
			<div class="card-body">
				<p class="description">추후 외부 연동 (예: 구글 드라이브 스토리지 확인 등) 테스트가 추가될 자리입니다.</p>
			</div>
		</section>
	</div>
</div>

<style>
	.test-page-container {
		padding: 2rem;
		max-width: 1200px;
		margin: 0 auto;
	}

	.page-header {
		margin-bottom: 2rem;
		border-bottom: 1px solid var(--surface-2);
		padding-bottom: 1rem;
	}

	.page-header h1 {
		margin: 0 0 0.5rem 0;
		font-size: 2rem;
		color: var(--text-1);
	}

	.subtitle {
		color: var(--text-2);
		margin: 0;
	}

	.test-card-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
		gap: 1.5rem;
	}

	.test-card {
		background-color: var(--surface-1);
		border-radius: 12px;
		border: 1px solid var(--surface-2);
		overflow: hidden;
		display: flex;
		flex-direction: column;
		transition: transform 0.2s ease, box-shadow 0.2s ease;
	}

	.test-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.card-header {
		background-color: var(--surface-2);
		padding: 1.2rem 1.5rem;
		border-bottom: 1px solid var(--surface-3);
	}

	.card-header h2 {
		margin: 0;
		font-size: 1.25rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: var(--text-1);
	}

	.card-body {
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		height: 100%;
	}

	.description {
		margin: 0;
		color: var(--text-2);
		font-size: 0.95rem;
		line-height: 1.5;
	}

	code {
		background-color: var(--surface-3);
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		font-family: monospace;
		font-size: 0.9em;
		color: var(--primary-color, #ff6b6b);
	}

	.action-area {
		margin-top: auto;
		display: flex;
		justify-content: flex-end;
	}

	.btn-run-test {
		background-color: var(--primary-color, #4a6cfa);
		color: white;
		border: none;
		padding: 0.7rem 1.2rem;
		border-radius: 8px;
		font-weight: 600;
		font-size: 0.95rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		transition: background-color 0.2s ease, opacity 0.2s ease;
	}

	.btn-run-test:hover:not(:disabled) {
		filter: brightness(1.1);
	}

	.btn-run-test:active:not(:disabled) {
		transform: translateY(1px);
	}

	.btn-run-test:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* 스피너 아이콘 */
	.spinner {
		display: inline-block;
		width: 16px;
		height: 16px;
		border: 2px solid rgba(255,255,255,0.3);
		border-radius: 50%;
		border-top-color: white;
		animation: spin 1s ease-in-out infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.result-box {
		margin-top: 1rem;
		padding: 1rem;
		border-radius: 8px;
		font-size: 0.9rem;
	}

	.result-box pre {
		margin: 0;
		white-space: pre-wrap;
		word-break: break-word;
		font-family: inherit;
	}

	.result-box.success {
		background-color: rgba(46, 204, 113, 0.1);
		border: 1px solid rgba(46, 204, 113, 0.3);
		color: #2ecc71;
	}

	.result-box.error {
		background-color: rgba(255, 107, 107, 0.1);
		border: 1px solid rgba(255, 107, 107, 0.3);
		color: #ff6b6b;
	}

	.placeholder {
		opacity: 0.6;
		border-style: dashed;
	}
	
	.placeholder .card-header {
		background-color: transparent;
	}
</style>
