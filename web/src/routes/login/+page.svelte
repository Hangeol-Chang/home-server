<script>
	import { signIn } from '@auth/sveltekit/client';

	let error = '';
	
	// URL에서 에러 파라미터 확인
	if (typeof window !== 'undefined') {
		const urlParams = new URLSearchParams(window.location.search);
		if (urlParams.get('error')) {
			error = '로그인에 실패했습니다. 허용된 이메일이 아니거나 권한이 없습니다.';
		}
	}

	async function handleGoogleSignIn() {
		await signIn('google', { callbackUrl: '/' });
	}
</script>

<svelte:head>
	<title>로그인 - Home Server</title>
</svelte:head>

<div class="login-container">
	<div class="login-card">
		<h1>🏠 Home Server</h1>
		<p class="subtitle">허가된 사용자만 접근할 수 있습니다</p>

		{#if error}
			<div class="error-message">
				⚠️ {error}
			</div>
		{/if}

		<button class="google-signin-btn" onclick={handleGoogleSignIn}>
			<svg viewBox="0 0 24 24" width="20" height="20">
				<path
					fill="#4285F4"
					d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
				/>
				<path
					fill="#34A853"
					d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
				/>
				<path
					fill="#FBBC05"
					d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
				/>
				<path
					fill="#EA4335"
					d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
				/>
			</svg>
			<span>Google로 로그인</span>
		</button>

		<div class="info">
			<p>
				<strong>안내:</strong><br />
				등록된 Google 계정으로만 로그인할 수 있습니다.<br />
				접근 권한이 필요한 경우 관리자에게 문의하세요.
			</p>
		</div>
	</div>
</div>

<style>
	.login-container {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		padding: 20px;
	}

	.login-card {
		background: white;
		border-radius: 16px;
		padding: 48px;
		max-width: 440px;
		width: 100%;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
		text-align: center;
	}

	h1 {
		margin: 0 0 12px 0;
		font-size: 2.5rem;
		color: #333;
	}

	.subtitle {
		margin: 0 0 32px 0;
		color: #666;
		font-size: 1rem;
	}

	.error-message {
		background: #fee;
		border: 1px solid #fcc;
		color: #c33;
		padding: 12px 16px;
		border-radius: 8px;
		margin-bottom: 24px;
		font-size: 0.9rem;
	}

	.google-signin-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		width: 100%;
		padding: 14px 24px;
		background: white;
		border: 2px solid #ddd;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		color: #555;
		cursor: pointer;
		transition: all 0.2s;
	}

	.google-signin-btn:hover {
		background: #f8f8f8;
		border-color: #ccc;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.google-signin-btn:active {
		transform: translateY(0);
	}

	.info {
		margin-top: 32px;
		padding-top: 24px;
		border-top: 1px solid #eee;
	}

	.info p {
		margin: 0;
		color: #666;
		font-size: 0.85rem;
		line-height: 1.6;
	}

	.info strong {
		color: #333;
	}
</style>
