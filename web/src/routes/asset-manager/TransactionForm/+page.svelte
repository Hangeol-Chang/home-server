<script>
	import { goto } from '$app/navigation';
	import TransactionForm from '$lib/components/asset-manager/TransactionForm.svelte';
	import '$lib/styles/module.css';
	import '$lib/styles/module-extended.css';

	let successCount = $state(0);
	let showSuccess = $state(false);

	async function handleSuccess() {
		successCount++;
		showSuccess = true;
		setTimeout(() => { showSuccess = false; }, 2500);
	}

	function handleCancel() {
		goto('/asset-manager');
	}
</script>

<svelte:head>
	<title>거래 등록</title>
</svelte:head>

<div class="quick-entry-page">
	{#if showSuccess}
		<div class="success-banner" role="status">
			거래가 등록되었습니다
			{#if successCount > 1}<span class="count-badge">{successCount}</span>{/if}
		</div>
	{/if}

	<TransactionForm
		standalone
		onSuccess={handleSuccess}
		onCancel={handleCancel}
	/>
</div>

<style>
	.quick-entry-page {
		max-width: 640px;
		margin: 0 auto;
		padding: 16px;
	}

	.success-banner {
		display: flex;
		align-items: center;
		gap: 8px;
		background: var(--text-success, #4caf50);
		color: white;
		padding: 12px 16px;
		border-radius: 8px;
		margin-bottom: 16px;
		font-size: 0.95rem;
		animation: slideDown 0.3s ease-out;
	}

	.count-badge {
		background: rgba(255, 255, 255, 0.3);
		border-radius: 12px;
		padding: 1px 8px;
		font-size: 0.85rem;
		font-weight: 600;
	}

	@keyframes slideDown {
		from { opacity: 0; transform: translateY(-8px); }
		to   { opacity: 1; transform: translateY(0); }
	}

	@media (max-width: 480px) {
		.quick-entry-page {
			padding: 8px;
		}
	}
</style>
