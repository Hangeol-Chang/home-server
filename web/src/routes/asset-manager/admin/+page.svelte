<script>
	import { 
		getClasses, 
		getCategories, 
		createCategory, 
		deleteCategory,
		getTiers,
		createTier,
		deleteTier
	} from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	// 상태 관리
	let classes = $state([]);
	let categories = $state([]);
	let tiers = $state([]);
	let loading = $state(true);
	let error = $state('');

	// 선택된 분류
	let selectedClassForCategory = $state(1);
	let selectedClassForTier = $state(1);

	// 폼 상태
	let showCategoryForm = $state(false);
	let showTierForm = $state(false);

	// 카테고리 폼
	let categoryForm = $state({
		class_id: 1,
		name: '',
		display_name: '',
		description: '',
		is_active: true,
		sort_order: 0
	});

	// 티어 폼
	let tierForm = $state({
		class_id: 1,
		tier_level: 0,
		name: '',
		display_name: '',
		description: '',
		is_active: true,
		sort_order: 0
	});

	const classTypes = [
		{ id: 1, name: 'spend', label: '지출', color: '#f44336' },
		{ id: 2, name: 'earn', label: '수익', color: '#4caf50' },
		{ id: 3, name: 'save', label: '저축', color: '#2196f3' }
	];

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		loading = true;
		error = '';
		try {
			[classes, categories, tiers] = await Promise.all([
				getClasses(),
				getCategories(),
				getTiers()
			]);
		} catch (err) {
			error = '데이터를 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	// 카테고리 관련
	const filteredCategories = $derived(
		categories.filter(c => c.class_id === selectedClassForCategory)
	);

	async function handleCreateCategory(e) {
		e.preventDefault();
		try {
			await createCategory(categoryForm);
			await loadData();
			resetCategoryForm();
			showCategoryForm = false;
		} catch (err) {
			alert('카테고리 생성 실패: ' + err.message);
		}
	}

	async function handleDeleteCategory(categoryId) {
		if (!confirm('이 카테고리를 삭제하시겠습니까?\n관련 거래가 있으면 비활성화됩니다.')) return;
		try {
			const result = await deleteCategory(categoryId);
			alert(result.message);
			await loadData();
		} catch (err) {
			alert('카테고리 삭제 실패: ' + err.message);
		}
	}

	function resetCategoryForm() {
		categoryForm = {
			class_id: selectedClassForCategory,
			name: '',
			display_name: '',
			description: '',
			is_active: true,
			sort_order: 0
		};
	}

	// 티어 관련
	const filteredTiers = $derived(
		tiers.filter(t => t.class_id === selectedClassForTier)
	);

	async function handleCreateTier(e) {
		e.preventDefault();
		try {
			await createTier(tierForm);
			await loadData();
			resetTierForm();
			showTierForm = false;
		} catch (err) {
			alert('티어 생성 실패: ' + err.message);
		}
	}

	async function handleDeleteTier(tierId) {
		if (!confirm('이 티어를 삭제하시겠습니까?\n관련 거래가 있으면 비활성화됩니다.')) return;
		try {
			const result = await deleteTier(tierId);
			alert(result.message);
			await loadData();
		} catch (err) {
			alert('티어 삭제 실패: ' + err.message);
		}
	}

	function resetTierForm() {
		tierForm = {
			class_id: selectedClassForTier,
			tier_level: 0,
			name: '',
			display_name: '',
			description: '',
			is_active: true,
			sort_order: 0
		};
	}

	function getClassLabel(classId) {
		return classTypes.find(c => c.id === classId)?.label || '';
	}

	function getClassColor(classId) {
		return classTypes.find(c => c.id === classId)?.color || '#6366f1';
	}
</script>

<svelte:head>
	<title>관리자 설정 - 가계부</title>
</svelte:head>

<div class="admin-page">
	<header class="page-header">
		<div>
			<h1>⚙️ 관리자 설정</h1>
			<p class="subtitle">카테고리와 티어를 관리합니다</p>
		</div>
		<a href="/asset-manager" class="back-btn">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<line x1="19" y1="12" x2="5" y2="12"></line>
				<polyline points="12 19 5 12 12 5"></polyline>
			</svg>
			돌아가기
		</a>
	</header>

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>데이터를 불러오는 중...</p>
		</div>
	{:else if error}
		<div class="error">
			<p>⚠️ {error}</p>
			<button class="retry-btn" onclick={loadData}>다시 시도</button>
		</div>
	{:else}
		<div class="admin-content">
			<!-- 거래 분류 정보 -->
			<section class="info-section">
				<h2>📊 거래 분류</h2>
				<div class="class-grid">
					{#each classes as classItem}
						<div class="class-card" style="--class-color: {getClassColor(classItem.id)}">
							<div class="class-info">
								<h3>{classItem.display_name}</h3>
								<p class="class-name">{classItem.name}</p>
								{#if classItem.description}
									<p class="class-desc">{classItem.description}</p>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</section>

			<!-- 카테고리 관리 -->
			<section class="manage-section">
				<div class="section-header">
					<h2>🏷️ 카테고리 관리</h2>
					<button class="add-btn" onclick={() => { 
						categoryForm.class_id = selectedClassForCategory;
						showCategoryForm = !showCategoryForm;
					}}>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="12" y1="5" x2="12" y2="19"></line>
							<line x1="5" y1="12" x2="19" y2="12"></line>
						</svg>
						{showCategoryForm ? '닫기' : '새 카테고리'}
					</button>
				</div>

				<!-- 분류 선택 -->
				<div class="class-filter">
					{#each classTypes as classType}
						<button
							class="filter-btn"
							class:active={selectedClassForCategory === classType.id}
							style="--class-color: {classType.color}"
							onclick={() => (selectedClassForCategory = classType.id)}
						>
							{classType.label}
						</button>
					{/each}
				</div>

				<!-- 카테고리 추가 폼 -->
				{#if showCategoryForm}
					<div class="form-container">
						<form class="admin-form" onsubmit={handleCreateCategory}>
							<div class="form-row">
								<div class="form-group">
									<label>카테고리명 (영문) *</label>
									<input type="text" bind:value={categoryForm.name} placeholder="예: coffee" required />
								</div>
								<div class="form-group">
									<label>표시명 (한글) *</label>
									<input type="text" bind:value={categoryForm.display_name} placeholder="예: 커피" required />
								</div>
							</div>
							<div class="form-group">
								<label>설명</label>
								<input type="text" bind:value={categoryForm.description} placeholder="선택사항" />
							</div>
							<div class="form-row">
								<div class="form-group">
									<label>정렬 순서</label>
									<input type="number" bind:value={categoryForm.sort_order} min="0" />
								</div>
								<div class="form-group checkbox-group">
									<label>
										<input type="checkbox" bind:checked={categoryForm.is_active} />
										활성화
									</label>
								</div>
							</div>
							<div class="form-actions">
								<button type="button" class="btn-cancel" onclick={() => { showCategoryForm = false; resetCategoryForm(); }}>
									취소
								</button>
								<button type="submit" class="btn-submit">생성</button>
							</div>
						</form>
					</div>
				{/if}

				<!-- 카테고리 리스트 -->
				<div class="items-list">
					{#if filteredCategories.length > 0}
						{#each filteredCategories as category}
							<div class="item-card">
								<div class="item-info">
									<h3>{category.display_name}</h3>
									<p class="item-name">{category.name}</p>
									{#if category.description}
										<p class="item-desc">{category.description}</p>
									{/if}
									<div class="item-meta">
										<span class="badge">순서: {category.sort_order}</span>
										<span class="badge" class:active={category.is_active}>
											{category.is_active ? '활성' : '비활성'}
										</span>
									</div>
								</div>
								<button
									class="delete-btn"
									onclick={() => handleDeleteCategory(category.id)}
									title="삭제"
									aria-label="카테고리 삭제"
								>
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
										<polyline points="3 6 5 6 21 6" />
										<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
									</svg>
								</button>
							</div>
						{/each}
					{:else}
						<p class="empty-message">카테고리가 없습니다</p>
					{/if}
				</div>
			</section>

			<!-- 티어 관리 -->
			<section class="manage-section">
				<div class="section-header">
					<h2>🎯 티어 관리</h2>
					<button class="add-btn" onclick={() => { 
						tierForm.class_id = selectedClassForTier;
						showTierForm = !showTierForm;
					}}>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="12" y1="5" x2="12" y2="19"></line>
							<line x1="5" y1="12" x2="19" y2="12"></line>
						</svg>
						{showTierForm ? '닫기' : '새 티어'}
					</button>
				</div>

				<!-- 분류 선택 -->
				<div class="class-filter">
					{#each classTypes as classType}
						<button
							class="filter-btn"
							class:active={selectedClassForTier === classType.id}
							style="--class-color: {classType.color}"
							onclick={() => (selectedClassForTier = classType.id)}
						>
							{classType.label}
						</button>
					{/each}
				</div>

				<!-- 티어 추가 폼 -->
				{#if showTierForm}
					<div class="form-container">
						<form class="admin-form" onsubmit={handleCreateTier}>
							<div class="form-row">
								<div class="form-group">
									<label>티어 레벨 *</label>
									<input type="number" bind:value={tierForm.tier_level} min="0" max="99" required />
								</div>
								<div class="form-group">
									<label>티어명 (영문) *</label>
									<input type="text" bind:value={tierForm.name} placeholder="예: luxury" required />
								</div>
							</div>
							<div class="form-group">
								<label>표시명 (한글) *</label>
								<input type="text" bind:value={tierForm.display_name} placeholder="예: 사치품" required />
							</div>
							<div class="form-group">
								<label>설명</label>
								<input type="text" bind:value={tierForm.description} placeholder="선택사항" />
							</div>
							<div class="form-row">
								<div class="form-group">
									<label>정렬 순서</label>
									<input type="number" bind:value={tierForm.sort_order} min="0" />
								</div>
								<div class="form-group checkbox-group">
									<label>
										<input type="checkbox" bind:checked={tierForm.is_active} />
										활성화
									</label>
								</div>
							</div>
							<div class="form-actions">
								<button type="button" class="btn-cancel" onclick={() => { showTierForm = false; resetTierForm(); }}>
									취소
								</button>
								<button type="submit" class="btn-submit">생성</button>
							</div>
						</form>
					</div>
				{/if}

				<!-- 티어 리스트 -->
				<div class="items-list">
					{#if filteredTiers.length > 0}
						{#each filteredTiers as tier}
							<div class="item-card">
								<div class="item-info">
									<h3>{tier.display_name}</h3>
									<p class="item-name">{tier.name} (Level {tier.tier_level})</p>
									{#if tier.description}
										<p class="item-desc">{tier.description}</p>
									{/if}
									<div class="item-meta">
										<span class="badge">순서: {tier.sort_order}</span>
										<span class="badge" class:active={tier.is_active}>
											{tier.is_active ? '활성' : '비활성'}
										</span>
									</div>
								</div>
								<button
									class="delete-btn"
									onclick={() => handleDeleteTier(tier.id)}
									title="삭제"
									aria-label="티어 삭제"
								>
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
										<polyline points="3 6 5 6 21 6" />
										<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
									</svg>
								</button>
							</div>
						{/each}
					{:else}
						<p class="empty-message">티어가 없습니다</p>
					{/if}
				</div>
			</section>
		</div>
	{/if}
</div>

<style>
	.admin-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: 20px;
	}

	/* 페이지 특화 스타일 */
	.back-btn {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 20px;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		color: var(--text-primary);
		text-decoration: none;
		font-weight: 600;
		transition: all 0.2s;
	}

	.back-btn:hover {
		background: var(--bg-tertiary);
		transform: translateX(-4px);
	}

	.admin-content {
		display: flex;
		flex-direction: column;
		gap: 32px;
	}

	.info-section,
	.manage-section {
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 12px;
		padding: 24px;
	}

	.info-section h2,
	.manage-section h2 {
		margin: 0 0 20px 0;
		font-size: 1.3rem;
		color: var(--text-primary);
	}

	.class-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 16px;
	}

	.class-card {
		background: var(--bg-secondary);
		border: 2px solid var(--class-color);
		border-radius: 10px;
		padding: 20px;
	}

	.class-info h3 {
		margin: 0 0 8px 0;
		font-size: 1.2rem;
		color: var(--class-color);
	}

	.class-name {
		margin: 0 0 8px 0;
		font-size: 0.9rem;
		color: var(--text-tertiary);
		font-family: monospace;
	}

	.class-desc {
		margin: 0;
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.class-filter {
		display: flex;
		gap: 12px;
		margin-bottom: 20px;
	}

	/* 필터 버튼 오버라이드 */
	.filter-btn.active {
		background: var(--class-color);
		color: white;
		border-color: var(--class-color);
	}

	.form-container {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 10px;
		padding: 20px;
		margin-bottom: 20px;
	}

	.admin-form {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	/* 체크박스 그룹 특수 스타일 */
	.checkbox-group {
		flex-direction: row;
		align-items: center;
	}

	.checkbox-group label {
		display: flex;
		align-items: center;
		gap: 8px;
		cursor: pointer;
	}

	.checkbox-group input[type='checkbox'] {
		width: 18px;
		height: 18px;
		cursor: pointer;
	}

	/* 항목 카드 */
	.item-info {
		flex: 1;
	}

	.item-info h3 {
		margin: 0 0 4px 0;
		font-size: 1.1rem;
		color: var(--text-primary);
	}

	.item-name {
		margin: 0 0 8px 0;
		font-size: 0.85rem;
		color: var(--text-tertiary);
		font-family: monospace;
	}

	.item-desc {
		margin: 0 0 12px 0;
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.item-meta {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}

	.delete-btn {
		padding: 8px;
		background: transparent;
		border: 1px solid var(--border-color);
		border-radius: 6px;
		color: var(--text-tertiary);
		cursor: pointer;
		transition: all 0.2s;
		flex-shrink: 0;
	}

	.delete-btn:hover {
		background: #fee;
		border-color: #fcc;
		color: #c33;
	}

	@media (max-width: 768px) {
		.class-grid {
			grid-template-columns: 1fr;
		}

		.class-filter {
			flex-direction: column;
		}

		.section-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 12px;
		}

		.add-btn {
			width: 100%;
			justify-content: center;
		}
	}
</style>
