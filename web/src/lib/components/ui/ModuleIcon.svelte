<script>
	let { name, size = 26 } = $props();
</script>

<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
	{#if name === 'asset'}
		<rect x="3" y="6" width="18" height="13" rx="2"></rect>
		<path d="M3 10h18"></path>
		<path d="M16 14h2"></path>
	{:else if name === 'schedule'}
		<rect x="3" y="4.5" width="18" height="17" rx="2"></rect>
		<line x1="16" y1="2.5" x2="16" y2="6.5"></line>
		<line x1="8" y1="2.5" x2="8" y2="6.5"></line>
		<line x1="3" y1="10" x2="21" y2="10"></line>
	{:else if name === 'notebook'}
		<path d="M6.5 2.5H20v19H6.5A2.5 2.5 0 0 1 4 19V5a2.5 2.5 0 0 1 2.5-2.5z"></path>
		<line x1="8" y1="7.5" x2="16" y2="7.5"></line>
		<line x1="8" y1="12" x2="16" y2="12"></line>
	{:else if name === 'projects'}
		<path d="M3 7.5a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-9z"></path>
	{:else if name === 'chat'}
		<path d="M20.5 11.5a8 8 0 0 1-8 8 8 8 0 0 1-3.6-.85L4 20l1.35-4.9A8 8 0 1 1 20.5 11.5z"></path>
	{:else if name === 'gdrive'}
		<path d="M17.5 19H6.5a4 4 0 0 1-.6-7.95 5.5 5.5 0 0 1 10.7-2.8A4.5 4.5 0 0 1 17.5 19z"></path>
	{:else if name === 'test'}
		<path d="M14.7 6.3a3.5 3.5 0 0 1-4.6 4.6L4 17l3 3 6.1-6.1a3.5 3.5 0 0 1 4.6-4.6l-2.4 2.4-2.6-2.6z"></path>
	{/if}
</svg>
