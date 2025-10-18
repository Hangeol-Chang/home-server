<script>
	import { signOut } from '@auth/sveltekit/client';

	let { session } = $props();

	async function handleSignOut() {
		await signOut({ callbackUrl: '/login' });
	}
</script>

{#if session?.user}
	<header class="app-header">
		<div class="header-content">
			<div class="user-info">
				{#if session.user.image}
					<img src={session.user.image} alt="Profile" class="user-avatar" />
				{/if}
				<span class="user-email">{session.user.email}</span>
			</div>
			<button class="signout-btn" onclick={handleSignOut}>로그아웃</button>
		</div>
	</header>
{/if}

<style>
	.app-header {
		background: var(--bg-primary);
		border-bottom: 1px solid var(--border-color);
		box-shadow: var(--shadow-sm);
	}

	.header-content {
		max-width: 1200px;
		margin: 0 auto;
		padding: 12px 24px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.user-info {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.user-avatar {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		border: 2px solid var(--border-color);
	}

	.user-email {
		font-size: 0.9rem;
		color: var(--text-secondary);
		font-weight: 500;
	}

	.signout-btn {
		padding: 8px 16px;
		background: var(--button-bg);
		color: var(--button-text);
		border: none;
		border-radius: 6px;
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.signout-btn:hover {
		background: var(--button-hover);
	}
</style>
