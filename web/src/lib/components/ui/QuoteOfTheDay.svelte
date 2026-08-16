<script>
	let quote = $state(null);
	let error = $state(false);

	$effect(() => {
		fetch('https://myeongeon-injul.vercel.app/api/quote')
			.then((res) => res.json())
			.then((data) => (quote = data))
			.catch(() => (error = true));
	});
</script>

{#if quote}
	<div class="quote-box">
		{#each quote.contents as line, i}
			<p style="animation-delay: {i}s">{line}</p>
		{/each}
	</div>
{:else if !error}
	<div class="quote-box">
		<p>&nbsp;</p>
	</div>
{/if}

<style>
	@font-face {
		font-family: 'KookminUniversitySunggokSerif';
		src: url('https://cdn.jsdelivr.net/gh/Project-Noonnu/2607101542@kmu80sungkokserif/kmu80sungkokserif/KMU80SungkokSerif.woff2')
			format('woff2');
		font-weight: 400;
		font-display: swap;
	}

	.quote-box {
		font-family: 'KookminUniversitySunggokSerif', serif;
		text-align: center;
		max-width: 600px;
		margin: 0 auto 40px;
		color: var(--text-secondary);
	}

	.quote-box p {
		font-size: 20px;
		line-height: 1.6;
		margin: 0;
		opacity: 0;
		animation: quote-fade-in 1s ease-out forwards;
	}

	@keyframes quote-fade-in {
		from {
			opacity: 0;
			transform: translateY(8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
