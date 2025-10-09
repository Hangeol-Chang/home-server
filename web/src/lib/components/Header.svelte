<script>
	import { routes } from '$lib/routes.js';
	import { page } from '$app/stores';
	import { signOut } from '@auth/sveltekit/client';
	import { onMount } from 'svelte';
	
	let { data } = $props();
	
	let currentPath = $state('');
	let sessionTimeLeft = $state('');
	let isMenuOpen = $state(false);
	let isModulesDropdownOpen = $state(false);
	
	// Modules 목록
	const modules = [
		{ name: 'Asset Manager', path: '/modules/asset-manager' },
		{ name: 'Auto Trader', path: '/modules/auto-trader' },
		{ name: 'Schedule Manager', path: '/modules/schedule-manager' }
	];
	
	// 현재 페이지 경로를 감지 (클라이언트 사이드에서)
	if (typeof window !== 'undefined') {
		currentPath = window.location.pathname;
	}
	
	// 세션 만료 시간 계산
	function updateSessionTime() {
		if (data?.session?.expires) {
			const expires = new Date(data.session.expires);
			const now = new Date();
			const diff = expires.getTime() - now.getTime();
			
			if (diff <= 0) {
				sessionTimeLeft = '만료됨';
				// 자동 로그아웃
				signOut({ callbackUrl: '/auth/signin' });
				return;
			}
			
			const hours = Math.floor(diff / (1000 * 60 * 60));
			const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
			sessionTimeLeft = `${hours}시간 ${minutes}분`;
		}
	}
	
	function toggleMenu() {
		isMenuOpen = !isMenuOpen;
	}
	
	function toggleModulesDropdown() {
		isModulesDropdownOpen = !isModulesDropdownOpen;
	}
	
	function closeMenus() {
		isMenuOpen = false;
		isModulesDropdownOpen = false;
	}
	
	onMount(() => {
		// 1분마다 세션 시간 업데이트
		updateSessionTime();
		const interval = setInterval(updateSessionTime, 60000);
		
		return () => clearInterval(interval);
	});
</script>

<header>
	<div class="container">
		<div class="nav-brand">
			<h1><a href="/">Home Server</a></h1>
		</div>
		
		<!-- Desktop Navigation -->
		<nav class="nav-menu">
			<ul class="nav-list">
				{#each routes as route}
					<li class="nav-item">
						<a 
							href={route.path} 
							class="nav-link {currentPath === route.path ? 'active' : ''}"
						>
							{route.name}
						</a>
					</li>
				{/each}
				
				<!-- Modules Dropdown -->
				<li class="nav-item dropdown" onmouseleave={() => isModulesDropdownOpen = false}>
					<button 
						class="nav-link dropdown-toggle"
						onmouseenter={() => isModulesDropdownOpen = true}
						onclick={toggleModulesDropdown}
					>
						Modules
						<span class="dropdown-arrow">▼</span>
					</button>
					{#if isModulesDropdownOpen}
						<ul class="dropdown-menu">
							{#each modules as module}
								<li>
									<a href={module.path} class="dropdown-item" onclick={closeMenus}>
										{module.name}
									</a>
								</li>
							{/each}
						</ul>
					{/if}
				</li>
				
				{#if data?.session?.user}
					<li class="nav-item">
						<div class="user-info">
							<div class="user-details">
								<span class="user-email">{data.session.user.email}</span>
								{#if sessionTimeLeft}
									<small class="session-timer">세션 만료: {sessionTimeLeft}</small>
								{/if}
							</div>
							<button 
								class="logout-btn"
								onclick={() => signOut({ callbackUrl: '/auth/signin' })}
							>
								로그아웃
							</button>
						</div>
					</li>
				{/if}
			</ul>
		</nav>

		<!-- Hamburger Menu Button -->
		<button class="hamburger-menu" onclick={toggleMenu} aria-label="메뉴 열기">
			<span class="line"></span>
			<span class="line"></span>
			<span class="line"></span>
		</button>
	</div>
</header>

<!-- Mobile Side Menu Background -->
{#if isMenuOpen}
	<div 
		class="side-menu-background" 
		onclick={toggleMenu}
		onkeydown={(e) => e.key === 'Escape' && toggleMenu()}
		role="button"
		tabindex="0"
		aria-label="메뉴 닫기"
	></div>
{/if}

<!-- Mobile Side Menu -->
<div class="side-menu {isMenuOpen ? 'open' : ''}">
	<button class="close-btn" onclick={toggleMenu}>×</button>
	
	<ul class="mobile-nav-list">
		{#each routes as route}
			<li class="mobile-nav-item">
				<a 
					href={route.path} 
					class="mobile-nav-link {currentPath === route.path ? 'active' : ''}"
					onclick={closeMenus}
				>
					{route.name}
				</a>
			</li>
		{/each}
		
		<!-- Mobile Modules Section -->
		<li class="mobile-nav-item">
			<div class="mobile-modules-section">
				<h4>Modules</h4>
				{#each modules as module}
					<a href={module.path} class="mobile-module-link" onclick={closeMenus}>
						{module.name}
					</a>
				{/each}
			</div>
		</li>
		
		{#if data?.session?.user}
			<li class="mobile-nav-item">
				<div class="mobile-user-info">
					<span class="user-email">{data.session.user.email}</span>
					{#if sessionTimeLeft}
						<small class="session-timer">세션 만료: {sessionTimeLeft}</small>
					{/if}
					<button 
						class="logout-btn mobile"
						onclick={() => signOut({ callbackUrl: '/auth/signin' })}
					>
						로그아웃
					</button>
				</div>
			</li>
		{/if}
	</ul>
</div>

<style>
	/* Header Container */
	header {
		position: fixed;
		top: 0;
		width: 100%;
		z-index: 100;
		height: 60px;
		box-shadow: 0 4px 6px rgba(250, 250, 250, 0.1);
		background: linear-gradient(0deg, rgba(255, 255, 255, 0.6) 0%, white 65%);
		color: black;
	}

	.container {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0 5vw;
		height: 60px;
		max-width: 1200px;
		margin: 0 auto;
	}

	/* Logo */
	.nav-brand h1 {
		margin: 0;
		font-size: 20px;
		font-weight: bold;
	}

	.nav-brand a {
		color: black;
		text-decoration: none;
		transition: opacity 0.2s;
	}

	.nav-brand a:hover {
		opacity: 0.8;
	}

	/* Desktop Navigation */
	.nav-menu {
		display: block;
	}

	.nav-list {
		display: flex;
		list-style: none;
		height: 60px;
		margin: 0;
		padding: 0;
		align-items: center;
		z-index: 10;
	}

	.nav-item {
		padding: 0 1vw;
		display: flex;
		align-items: center;
		position: relative;
	}

	.nav-link {
		color: black;
		text-decoration: none;
		font-weight: 500;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		transition: all 0.2s;
		border: none;
		background: none;
		cursor: pointer;
		font-size: inherit;
		font-family: inherit;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.nav-link:hover {
		color: #0056b3;
		background-color: #f5f5f5;
	}

	.nav-link.active {
		background: rgba(255, 255, 255, 0.2);
		font-weight: 600;
	}

	/* Dropdown */
	.dropdown {
		position: relative;
	}

	.dropdown-arrow {
		font-size: 0.8em;
		transition: transform 0.2s;
	}

	.dropdown:hover .dropdown-arrow {
		transform: rotate(180deg);
	}

	.dropdown-menu {
		position: absolute;
		top: 100%;
		left: 0;
		background: white;
		border: 1px solid #ddd;
		border-radius: 6px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		list-style: none;
		margin: 0;
		padding: 0.5rem 0;
		min-width: 180px;
		z-index: 20;
	}

	.dropdown-item {
		display: block;
		padding: 0.5rem 1rem;
		color: black;
		text-decoration: none;
		transition: background-color 0.2s;
	}

	.dropdown-item:hover {
		background-color: #f5f5f5;
		color: #0056b3;
	}

	/* User Info */
	.user-info {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-left: 1rem;
		padding-left: 1rem;
		border-left: 1px solid rgba(255, 255, 255, 0.2);
	}

	.user-details {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
	}

	.user-email {
		color: black;
		font-size: 0.9rem;
		opacity: 0.9;
	}

	.session-timer {
		color: black;
		opacity: 0.7;
		font-size: 0.75rem;
		margin-top: 2px;
	}

	.logout-btn {
		padding: 0.4rem 0.8rem;
		background-color: rgba(255, 255, 255, 0.1);
		color: rgba(255, 100, 100, 1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 4px;
		font-size: 0.85rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.logout-btn:hover {
		background-color: rgba(255, 255, 255, 0.5);
		border-color: rgba(255, 255, 255, 0.3);
	}

	/* Hamburger Menu */
	.hamburger-menu {
		display: none;
		background: none;
		border: none;
		cursor: pointer;
		flex-direction: column;
		justify-content: space-between;
		height: 20px;
		width: 20px;
	}

	.line {
		width: 100%;
		height: 3px;
		background-color: black;
		border-radius: 12px;
		transition: all 0.3s;
	}

	/* Side Menu Background */
	.side-menu-background {
		display: block;
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background-color: rgba(230, 230, 230, 0.5);
		z-index: 50;
	}

	/* Side Menu */
	.side-menu {
		display: none; /* 기본적으로 숨김 */
		flex-direction: column;
		align-items: flex-start;
		position: fixed;
		top: 0;
		right: 0;
		width: 250px;
		height: 100%;
		background-color: #ffffff;
		opacity: 0.95;
		box-shadow: -4px 0 6px rgba(50, 50, 50, 0.2);
		transition: transform 0.3s ease-in-out;
		transform: translateX(100%); /* 완전히 화면 밖으로 이동 */
		z-index: 60;
		padding: 20px;
		overflow-y: auto;
	}

	.side-menu.open {
		transform: translateX(0);
	}

	.close-btn {
		background: none;
		border: none;
		color: black;
		font-size: 24px;
		cursor: pointer;
		margin-bottom: 20px;
		align-self: flex-end;
	}

	/* Mobile Navigation */
	.mobile-nav-list {
		list-style: none;
		padding: 0;
		margin: 0;
		width: 100%;
	}

	.mobile-nav-item {
		margin-bottom: 10px;
	}

	.mobile-nav-link {
		display: block;
		padding: 12px 0;
		color: black;
		text-decoration: none;
		font-weight: 500;
		border-bottom: 1px solid #f0f0f0;
		transition: color 0.2s;
	}

	.mobile-nav-link:hover {
		color: #0056b3;
	}

	.mobile-nav-link.active {
		color: #0056b3;
		font-weight: 600;
	}

	/* Mobile Modules Section */
	.mobile-modules-section {
		padding: 15px 0;
		border-bottom: 1px solid #f0f0f0;
	}

	.mobile-modules-section h4 {
		margin: 0 0 10px 0;
		font-size: 16px;
		color: #666;
	}

	.mobile-module-link {
		display: block;
		padding: 8px 0 8px 15px;
		color: black;
		text-decoration: none;
		font-size: 14px;
		transition: color 0.2s;
	}

	.mobile-module-link:hover {
		color: #0056b3;
	}

	/* Mobile User Info */
	.mobile-user-info {
		padding: 15px 0;
		border-top: 1px solid #f0f0f0;
	}

	.mobile-user-info .user-email {
		display: block;
		margin-bottom: 5px;
	}

	.mobile-user-info .session-timer {
		display: block;
		margin-bottom: 15px;
	}

	.logout-btn.mobile {
		width: 100%;
		padding: 10px;
		text-align: center;
	}

	/* Responsive Design */
	@media (max-width: 768px) {
		.nav-menu {
			display: none;
		}

		.hamburger-menu {
			display: flex;
		}

		.container {
			padding: 0 20px;
		}

		/* 모바일에서만 사이드 메뉴 활성화 */
		.side-menu {
			display: flex;
		}
	}

	/* Body padding to account for fixed header */
	:global(body) {
		padding-top: 60px;
	}
</style>