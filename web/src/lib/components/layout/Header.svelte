<script>
	import { signOut } from '@auth/sveltekit/client';
	import { device } from '$lib/stores/device';

	let { session } = $props();
	let isProfileDropdownOpen = $state(false);
	let isMenuDropdownOpen = $state(false);

	async function handleSignOut() {
		await signOut({ callbackUrl: '/login' });
	}

	function toggleProfileDropdown() {
		isProfileDropdownOpen = !isProfileDropdownOpen;
		isMenuDropdownOpen = false;
	}

	function toggleMenuDropdown() {
		isMenuDropdownOpen = !isMenuDropdownOpen;
		isProfileDropdownOpen = false;
	}

	function handleMouseEnter(type) {
		if ($device.isMobile) return;
		
		if (type === 'menu') {
			isMenuDropdownOpen = true;
			isProfileDropdownOpen = false;
		} else if (type === 'profile') {
			isProfileDropdownOpen = true;
			isMenuDropdownOpen = false;
		}
	}

	function handleMouseLeave(type) {
		if ($device.isMobile) return;

		if (type === 'menu') {
			isMenuDropdownOpen = false;
		} else if (type === 'profile') {
			isProfileDropdownOpen = false;
		}
	}
</script>

{#if session?.user}
	<header class="app-header" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
		<div class="header-content">
			<div class="logo">
				<a href="/" style="text-decoration: none;">
					<span class="app-title">Home Server</span>
				</a>
			</div>

			<div class="header-right">
				<div 
					class="menu-dropdown-container"
					onmouseenter={() => handleMouseEnter('menu')}
					onmouseleave={() => handleMouseLeave('menu')}
					role="group"
				>
					<div class="menu-button" aria-label="메뉴">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="3" y1="12" x2="21" y2="12"></line>
							<line x1="3" y1="6" x2="21" y2="6"></line>
							<line x1="3" y1="18" x2="21" y2="18"></line>
						</svg>
						<span>메뉴</span>
					</div>

					{#if isMenuDropdownOpen}
						<div class="menu-dropdown">
							<a href="/asset-manager" class="menu-dropdown-item">
								<span>💰</span>
								<span>자산관리</span>
							</a>
							<a href="/schedule-manager" class="menu-dropdown-item">
								<span>📅</span>
								<span>일정관리</span>
							</a>
							<a href="/notebook" class="menu-dropdown-item">
								<span>📓</span>
								<span>노트북</span>
							</a>
						</div>
					{/if}
				</div>

				<div 
					class="profile-menu"
					onmouseenter={() => handleMouseEnter('profile')}
					onmouseleave={() => handleMouseLeave('profile')}
					role="group"
				>
					<button class="profile-button" onclick={toggleProfileDropdown} aria-label="프로필 메뉴">
						{#if session.user.image}
							<img src={session.user.image} alt="Profile" class="user-avatar" />
						{:else}
							<div class="user-avatar-placeholder">
								{session.user.email?.charAt(0).toUpperCase()}
							</div>
						{/if}
					</button>

					{#if isProfileDropdownOpen}
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
		max-width: 1400px;
		margin: 0 auto;
		padding: 12px 24px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 32px;
	}

	.logo {
		display: flex;
		align-items: center;
	}

	.app-title {
		font-size: 1.1rem;
		font-weight: 400;
		color: var(--text-primary);
	}

	/* Header Right Container */
	.header-right {
		display: flex;
		align-items: center;
		gap: 16px;
	}

	/* Menu Dropdown */
	.menu-dropdown-container {
		position: relative;
	}
	
	.menu-button {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 12px;
		background: none;
		border: none;
		cursor: pointer;
		color: var(--text-primary);
		font-size: 1rem;
		transition: background-color 0.2s;
		border-radius: 4px;
	}

	.menu-dropdown {
		position: absolute;
		right: 0;
		min-width: 200px;
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 4px;
		box-shadow: var(--shadow-lg);
		overflow: hidden;
		z-index: 1000;
		animation: slideDown 0.2s ease-out;
	}

	.menu-dropdown-item {
		display: flex;
		align-items: center;
		gap: 12px;
		width: 100%;
		padding: 12px 16px;
		text-decoration: none;
		color: var(--text-primary);
		font-size: 1rem;
		font-weight: 300;
		transition: background 0.2s;
		border: none;
		background: none;
		cursor: pointer;
	}

	.menu-dropdown-item:hover {
		background: var(--bg-primary-dark);
		color: white;
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
		font-weight: 400;
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
		font-weight: 300;
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



	/* Tablet/Mobile (< 768px) */
	.app-header {
		&.tablet {
			.header-content {
				padding: 8px 12px;
				gap: 12px;
			}

			.app-title {
				font-size: 0.95rem;
			}

			.header-right {
				gap: 12px;
			}

			.menu-dropdown {
				min-width: 180px;
			}

			.menu-dropdown-item {
				padding: 10px 12px;
				font-size: 0.9rem;
			}

			.user-avatar,
			.user-avatar-placeholder {
				width: 36px;
				height: 36px;
				font-size: 1rem;
			}

			.dropdown {
				min-width: 200px;
			}

			.dropdown-item {
				padding: 10px 12px;
				font-size: 0.9rem;
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			.header-content {
				padding: 8px;
				gap: 8px;
			}

			.app-title {
				font-size: 0.9rem;
			}

			.header-right {
				gap: 8px;
			}

			.menu-dropdown {
				min-width: 160px;
			}

			.menu-dropdown-item {
				padding: 8px 10px;
				font-size: 0.85rem;
			}

			.user-avatar,
			.user-avatar-placeholder {
				width: 32px;
				height: 32px;
				font-size: 0.9rem;
			}
		}
	}
</style>
