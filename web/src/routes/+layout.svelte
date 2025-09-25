<script>
	import favicon from '$lib/assets/favicon.svg';
	import { routes } from '$lib/routes.js';
	import Header from '$lib/components/Header.svelte';

	let { children, data } = $props();
</script>

<Header {data} />

<nav class="menu">
    {#each routes as r}
        <a href={r.path}>{r.name}</a>
    {/each}
</nav>

<main>
    {@render children()}
</main>

<style>
    .menu {
        display: flex;
    }
</style>