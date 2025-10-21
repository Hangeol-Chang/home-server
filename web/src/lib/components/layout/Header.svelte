<script>
	import { signOut } from '@auth/sveltekit/client';

	let { session } = $props();
	let isDropdownOpen = $state(false);

	async function handleSignOut() {
		await signOut({ callbackUrl: '/login' });
	}

	function toggleDropdown() {
		isDropdownOpen = !isDropdownOpen;
	}

	// 외부 클릭 시 드롭다운 닫기
	function handleClickOutside(event) {
		if (!event.target.closest('.profile-menu')) {
			isDropdownOpen = false;
		}
	}
</script>

<svelte:window onclick={handleClickOutside} />

{#if session?.user}
	<header class="app-header">
		<div class="header-content">
			<div class="logo">
				<span class="app-title">Home Server</span>
			</div>

			<div class="profile-menu">
				<button class="profile-button" onclick={toggleDropdown} aria-label="프로필 메뉴">
					{#if session.user.image}
						<img src={session.user.image} alt="Profile" class="user-avatar" />
					{:else}
						<div class="user-avatar-placeholder">
							{session.user.email?.charAt(0).toUpperCase()}
						</div>
					{/if}
				</button>

				{#if isDropdownOpen}
					<div class="dropdown">
						<div class="dropdown-header">
							<div class="user-email">{session.user.email}</div>
						</div>
						<div class="dropdown-divider"></div>
						<button class="dropdown-item" onclick={handleSignOut}>
							<svg
								width="16"
								height="16"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
							>
								<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
								<polyline points="16 17 21 12 16 7" />
								<line x1="21" y1="12" x2="9" y2="12" />
							</svg>
							<span style="height: 26px;">로그아웃</span>
						</button>
					</div>
				{/if}
			</div>
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

	.logo {
		display: flex;
		align-items: center;
	}

	.app-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: var(--text-primary);
	}

	/* Profile Menu */
	.profile-menu {
		position: relative;
	}

	.profile-button {
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		display: flex;
		align-items: center;
		transition: opacity 0.2s;
	}

	.profile-button:hover {
		opacity: 0.8;
	}

	.user-avatar {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		border: 2px solid var(--border-color);
		transition: border-color 0.2s;
	}

	.profile-button:hover .user-avatar {
		border-color: var(--accent);
	}

	.user-avatar-placeholder {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		background: var(--accent);
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 600;
		font-size: 1.1rem;
	}

	/* Dropdown */
	.dropdown {
		position: absolute;
		top: calc(100% + 8px);
		right: 0;
		min-width: 240px;
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		box-shadow: var(--shadow-lg);
		overflow: hidden;
		z-index: 1000;
		animation: slideDown 0.2s ease-out;
		text-align: right;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.dropdown-header {
		padding: 12px 16px;
		background: var(--bg-primary);
	}

	.user-email {
		font-size: 0.85rem;
		color: var(--text-secondary);
		font-weight: 500;
		word-break: break-all;
	}

	.dropdown-divider {
		height: 1px;
		background: var(--border-color);
		margin: 0;
	}

	.dropdown-item {
		width: 100%;
		padding: 12px 16px;
		border: none;
		background: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 10px;
		color: var(--text-primary);
		font-size: 1.0rem;
		transition: background 0.2s;
	}

	.dropdown-item:hover {
		background: var(--bg-secondary);
	}

	.dropdown-item svg {
		flex-shrink: 0;
	}
</style>
