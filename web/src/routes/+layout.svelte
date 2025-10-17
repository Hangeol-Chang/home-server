<script>
	import favicon from '$lib/assets/favicon.svg';
	import { signOut } from '@auth/sveltekit/client';

	let { children, data } = $props();

	async function handleSignOut() {
		await signOut({ callbackUrl: '/login' });
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if data.session?.user}
	<header class="app-header">
		<div class="header-content">
			<div class="user-info">
				{#if data.session.user.image}
					<img src={data.session.user.image} alt="Profile" class="user-avatar" />
				{/if}
				<span class="user-email">{data.session.user.email}</span>
			</div>
			<button class="signout-btn" onclick={handleSignOut}>로그아웃</button>
		</div>
	</header>
{/if}

<main class="app-main">
	{@render children?.()}
</main>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			sans-serif;
	}

	.app-header {
		background: #fff;
		border-bottom: 1px solid #e0e0e0;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
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
		border: 2px solid #e0e0e0;
	}

	.user-email {
		font-size: 0.9rem;
		color: #555;
		font-weight: 500;
	}

	.signout-btn {
		padding: 8px 16px;
		background: #f5f5f5;
		border: 1px solid #ddd;
		border-radius: 6px;
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.signout-btn:hover {
		background: #e8e8e8;
		border-color: #ccc;
	}

	.app-main {
		max-width: 1200px;
		margin: 0 auto;
		padding: 24px;
	}
</style>
