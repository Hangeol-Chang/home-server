<script>
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Header from '$lib/components/layout/Header.svelte';
	import Footer from '$lib/components/layout/Footer.svelte';
	import { device } from '$lib/stores/device';

	let { children, data } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="app-container" class:mobile={$device.isMobile} class:tablet={$device.isTablet} class:desktop={$device.isDesktop}>
	<Header session={data.session} />

	<main class="app-main">
		{@render children?.()}
	</main>

	<Footer />
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
			sans-serif;
	}	

	.app-container {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	.app-main {
		flex: 1;
		max-width: 1200px;
		width: 100%;
		margin: 0 auto;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		padding: 8px;
	}

	/* Tablet/Mobile (< 768px) */
	.app-container.tablet .app-main {
		padding: 0px;
		box-shadow: none;
	}

	/* Mobile (< 320px) */
	.app-container.mobile .app-main {
		padding: 0px;
	}
</style>
