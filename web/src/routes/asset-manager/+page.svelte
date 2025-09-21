<script>
	import { onMount } from 'svelte';
	import axios from 'axios';
	
	let transactions = [];
	let assets = [];
	let categories = [];
	let loading = true;
	let error = null;
	
	let newTransaction = {
		amount: 0,
		description: '',
		category: '',
		transaction_type: 'income'
	};
	
	async function loadData() {
		try {
			loading = true;
			const [transactionsRes, assetsRes, categoriesRes] = await Promise.all([
				axios.get('/api/asset-manager/transactions'),
				axios.get('/api/asset-manager/assets'), 
				axios.get('/api/asset-manager/categories')
			]);
			
			transactions = transactionsRes.data;
			assets = assetsRes.data;
			categories = categoriesRes.data;
		} catch (err) {
			error = '데이터를 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}
	
	async function addTransaction() {
		try {
			const response = await axios.post('/api/asset-manager/transactions', newTransaction);
			transactions = [response.data, ...transactions];
			newTransaction = { amount: 0, description: '', category: '', transaction_type: 'income' };
			await loadData(); // 관련 데이터 새로고침
		} catch (err) {
			error = '거래 추가에 실패했습니다: ' + err.message;
		}
	}
	
	async function deleteTransaction(id) {
		try {
			await axios.delete(`/api/asset-manager/transactions/${id}`);
			transactions = transactions.filter(t => t.id !== id);
			await loadData();
		} catch (err) {
			error = '거래 삭제에 실패했습니다: ' + err.message;
		}
	}
	
	function formatCurrency(amount) {
		return new Intl.NumberFormat('ko-KR', { 
			style: 'currency', 
			currency: 'KRW' 
		}).format(amount);
	}
	
	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString('ko-KR');
	}
	
	onMount(loadData);
</script>

<svelte:head>
	<title>Asset Manager - Home Server</title>
</svelte:head>

<main>
	<div class="header">
		<h1>💰 Asset Manager</h1>
		<p>자산 및 거래 관리</p>
		<nav class="breadcrumb">
			<a href="/">🏠 홈</a> / <span>Asset Manager</span>
		</nav>
	</div>

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>데이터를 불러오는 중...</p>
		</div>
	{:else if error}
		<div class="error">
			<h3>⚠️ 오류 발생</h3>
			<p>{error}</p>
			<button on:click={loadData}>다시 시도</button>
		</div>
	{:else}
		<!-- 요약 카드들 -->
		<section class="summary">
			<div class="summary-card">
				<h3>총 자산</h3>
				<div class="amount positive">
					{formatCurrency(assets.reduce((sum, asset) => sum + asset.value, 0))}
				</div>
			</div>
			<div class="summary-card">
				<h3>총 거래</h3>
				<div class="count">{transactions.length}건</div>
			</div>
			<div class="summary-card">
				<h3>카테고리</h3>
				<div class="count">{categories.length}개</div>
			</div>
		</section>

		<!-- 새 거래 추가 -->
		<section class="add-transaction">
			<h2>새 거래 추가</h2>
			<form on:submit|preventDefault={addTransaction} class="transaction-form">
				<div class="form-group">
					<label for="amount">금액</label>
					<input 
						type="number" 
						id="amount"
						bind:value={newTransaction.amount} 
						required
					/>
				</div>
				<div class="form-group">
					<label for="description">설명</label>
					<input 
						type="text" 
						id="description"
						bind:value={newTransaction.description} 
						required
					/>
				</div>
				<div class="form-group">
					<label for="category">카테고리</label>
					<select id="category" bind:value={newTransaction.category}>
						<option value="">카테고리 선택</option>
						{#each categories as category}
							<option value={category.name}>{category.name}</option>
						{/each}
					</select>
				</div>
				<div class="form-group">
					<label for="type">유형</label>
					<select id="type" bind:value={newTransaction.transaction_type}>
						<option value="income">수입</option>
						<option value="expense">지출</option>
					</select>
				</div>
				<button type="submit" class="submit-btn">거래 추가</button>
			</form>
		</section>

		<!-- 최근 거래 목록 -->
		<section class="transactions">
			<h2>최근 거래</h2>
			{#if transactions.length === 0}
				<div class="empty-state">
					<p>거래 내역이 없습니다.</p>
					<p>위에서 새 거래를 추가해보세요!</p>
				</div>
			{:else}
				<div class="transaction-list">
					{#each transactions.slice(0, 10) as transaction}
						<div class="transaction-item">
							<div class="transaction-info">
								<div class="description">{transaction.description}</div>
								<div class="meta">
									{transaction.category} • {formatDate(transaction.date)}
								</div>
							</div>
							<div class="transaction-amount">
								<span class="amount {transaction.transaction_type}">
									{transaction.transaction_type === 'income' ? '+' : '-'}{formatCurrency(Math.abs(transaction.amount))}
								</span>
								<button 
									class="delete-btn"
									on:click={() => deleteTransaction(transaction.id)}
									title="삭제"
								>
									🗑️
								</button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</section>

		<!-- 자산 목록 -->
		<section class="assets">
			<h2>자산 현황</h2>
			{#if assets.length === 0}
				<div class="empty-state">
					<p>등록된 자산이 없습니다.</p>
				</div>
			{:else}
				<div class="asset-list">
					{#each assets as asset}
						<div class="asset-item">
							<div class="asset-info">
								<div class="name">{asset.name}</div>
								<div class="type">{asset.asset_type}</div>
							</div>
							<div class="asset-value">
								{formatCurrency(asset.value)}
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</section>
	{/if}
</main>

<style>
	main {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		min-height: 100vh;
		color: white;
	}
	
	.header {
		text-align: center;
		margin-bottom: 3rem;
	}
	
	.header h1 {
		font-size: 2.5rem;
		margin: 0;
		text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
	}
	
	.breadcrumb {
		margin-top: 1rem;
		opacity: 0.8;
	}
	
	.breadcrumb a {
		color: white;
		text-decoration: none;
	}
	
	.breadcrumb a:hover {
		text-decoration: underline;
	}
	
	.loading {
		text-align: center;
		padding: 4rem;
	}
	
	.spinner {
		border: 3px solid rgba(255,255,255,0.3);
		border-radius: 50%;
		border-top: 3px solid white;
		width: 40px;
		height: 40px;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	.error {
		text-align: center;
		padding: 2rem;
		background: rgba(239, 68, 68, 0.2);
		border-radius: 12px;
		margin: 2rem 0;
	}
	
	.summary {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
		margin-bottom: 3rem;
	}
	
	.summary-card {
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		border-radius: 12px;
		padding: 1.5rem;
		text-align: center;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.summary-card h3 {
		margin: 0 0 1rem 0;
		opacity: 0.8;
		font-size: 1rem;
	}
	
	.amount {
		font-size: 2rem;
		font-weight: bold;
	}
	
	.amount.positive {
		color: #10b981;
	}
	
	.count {
		font-size: 2rem;
		font-weight: bold;
		color: #3b82f6;
	}
	
	section {
		margin-bottom: 3rem;
	}
	
	section h2 {
		font-size: 1.5rem;
		margin-bottom: 1.5rem;
		text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
	}
	
	.transaction-form {
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		border-radius: 12px;
		padding: 2rem;
		border: 1px solid rgba(255, 255, 255, 0.2);
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		align-items: end;
	}
	
	.form-group {
		display: flex;
		flex-direction: column;
	}
	
	.form-group label {
		margin-bottom: 0.5rem;
		font-weight: 500;
	}
	
	.form-group input,
	.form-group select {
		padding: 0.75rem;
		border: 1px solid rgba(255, 255, 255, 0.3);
		border-radius: 8px;
		background: rgba(255, 255, 255, 0.1);
		color: white;
		font-size: 1rem;
	}
	
	.form-group input::placeholder {
		color: rgba(255, 255, 255, 0.6);
	}
	
	.submit-btn {
		background: #10b981;
		border: none;
		color: white;
		padding: 0.75rem 2rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 1rem;
		font-weight: 500;
		transition: background 0.2s ease;
	}
	
	.submit-btn:hover {
		background: #059669;
	}
	
	.transaction-list,
	.asset-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.transaction-item,
	.asset-item {
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		border-radius: 12px;
		padding: 1rem 1.5rem;
		border: 1px solid rgba(255, 255, 255, 0.2);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.transaction-info,
	.asset-info {
		flex: 1;
	}
	
	.description,
	.name {
		font-weight: 500;
		margin-bottom: 0.25rem;
	}
	
	.meta,
	.type {
		font-size: 0.875rem;
		opacity: 0.7;
	}
	
	.transaction-amount {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.amount.income {
		color: #10b981;
	}
	
	.amount.expense {
		color: #ef4444;
	}
	
	.delete-btn {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0.25rem;
		border-radius: 4px;
		transition: background 0.2s ease;
	}
	
	.delete-btn:hover {
		background: rgba(239, 68, 68, 0.2);
	}
	
	.empty-state {
		text-align: center;
		padding: 3rem;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 12px;
		opacity: 0.7;
	}
	
	button {
		background: rgba(255, 255, 255, 0.2);
		border: 1px solid rgba(255, 255, 255, 0.3);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	button:hover:not(:disabled) {
		background: rgba(255, 255, 255, 0.3);
	}
	
	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>