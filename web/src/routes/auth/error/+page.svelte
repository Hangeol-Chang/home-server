<script>
	import { page } from '$app/stores'
	
	$: errorType = $page.url.searchParams.get('error')
	$: errorMessage = getErrorMessage(errorType)
	
	function getErrorMessage(error) {
		switch(error) {
			case 'AccessDenied':
				return '허가되지 않은 이메일 계정입니다.'
			case 'OAuthSignin':
				return 'OAuth 로그인 과정에서 오류가 발생했습니다.'
			case 'OAuthCallback':
				return 'OAuth 콜백 처리 중 오류가 발생했습니다.'
			case 'Configuration':
				return '서버 설정에 오류가 있습니다.'
			default:
				return '알 수 없는 오류가 발생했습니다.'
		}
	}
</script>

<svelte:head>
	<title>인증 오류 - Home Server</title>
</svelte:head>

<div class="error-container">
	<div class="error-card">
		<div class="error-icon">❌</div>
		<h1>접근이 거부되었습니다</h1>
		<p>{errorMessage}</p>
		<p class="error-detail">
			{#if errorType === 'AccessDenied'}
				관리자에게 문의하여 계정을 허가 목록에 추가해달라고 요청하세요.
			{:else}
				다시 시도하거나 관리자에게 문의하세요.
			{/if}
		</p>
		<div class="error-debug">
			<small>오류 코드: {errorType || 'Unknown'}</small>
		</div>
		<a href="/auth/signin" class="retry-btn">다시 시도</a>
	</div>
</div>

<style>
	.error-container {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
		padding: 2rem;
	}

	.error-card {
		background: white;
		border-radius: 16px;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
		padding: 3rem;
		width: 100%;
		max-width: 400px;
		text-align: center;
	}

	.error-icon {
		font-size: 4rem;
		margin-bottom: 1rem;
	}

	h1 {
		color: #333;
		margin: 0 0 1rem 0;
		font-size: 1.5rem;
		font-weight: 600;
	}

	p {
		color: #666;
		margin: 0 0 1rem 0;
		line-height: 1.5;
	}

	.error-detail {
		color: #888;
		font-size: 0.9rem;
		margin-bottom: 1rem;
	}

	.error-debug {
		margin-bottom: 2rem;
		padding: 0.5rem;
		background: #f5f5f5;
		border-radius: 4px;
		border-left: 3px solid #ddd;
	}

	.error-debug small {
		color: #666;
		font-family: monospace;
	}

	.retry-btn {
		display: inline-block;
		padding: 0.875rem 2rem;
		background: #667eea;
		color: white;
		text-decoration: none;
		border-radius: 8px;
		font-weight: 500;
		transition: all 0.2s;
	}

	.retry-btn:hover {
		background: #5a6fd8;
		transform: translateY(-1px);
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
	}
</style>