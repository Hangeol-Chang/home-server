<script>
	import { signIn } from '@auth/sveltekit/client'
	import { page } from '$app/stores'
	
	async function handleGoogleLogin() {
		try {
			await signIn('google', { 
				callbackUrl: '/',
				redirect: true 
			})
		} catch (error) {
			console.error('Login error:', error)
			window.location.href = '/auth/error?error=OAuthSignin'
		}
	}
</script>

<svelte:head>
	<title>로그인 - Home Server</title>
</svelte:head>

<div class="login-container">
	<div class="login-card">
		<div class="logo">
			<h1>Home Server</h1>
		</div>
		
		<div class="login-content">
			<h2>로그인이 필요합니다</h2>
			<p>허가된 이메일 계정으로만 접근할 수 있습니다.</p>
			
			{#if $page.url.searchParams.get('error')}
				<div class="error-message">
					<p>로그인에 실패했습니다. 허가된 이메일인지 확인해주세요.</p>
				</div>
			{/if}
			
			<button 
				class="google-login-btn"
				onclick={handleGoogleLogin}
			>
				<svg width="18" height="18" viewBox="0 0 24 24">
					<path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
					<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
					<path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
					<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
				</svg>
				Google로 로그인
			</button>
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
		padding: 2rem;
	}

	.login-card {
		background: white;
		border-radius: 16px;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
		padding: 3rem;
		width: 100%;
		max-width: 400px;
		text-align: center;
	}

	.logo h1 {
		color: #333;
		margin: 0 0 2rem 0;
		font-size: 2.5rem;
		font-weight: 700;
	}

	.login-content h2 {
		color: #333;
		margin: 0 0 0.5rem 0;
		font-size: 1.5rem;
		font-weight: 600;
	}

	.login-content p {
		color: #666;
		margin: 0 0 2rem 0;
		line-height: 1.5;
	}

	.error-message {
		background: #fee;
		border: 1px solid #fcc;
		border-radius: 8px;
		padding: 1rem;
		margin: 1rem 0;
		color: #c33;
	}

	.error-message p {
		margin: 0;
		color: #c33;
	}

	.google-login-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
		width: 100%;
		padding: 0.875rem 1.5rem;
		background: white;
		border: 2px solid #ddd;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 500;
		color: #333;
		cursor: pointer;
		transition: all 0.2s;
	}

	.google-login-btn:hover {
		background: #f8f9fa;
		border-color: #ccc;
		transform: translateY(-1px);
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
	}

	.google-login-btn:active {
		transform: translateY(0);
	}
</style>