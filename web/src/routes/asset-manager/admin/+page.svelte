<script>
	import { 
		getClasses, 
		getCategories, 
		createCategory, 
		deleteCategory,
		getSubCategories,
		createSubCategory,
		deleteSubCategory,
		getTiers,
		createTier,
		deleteTier,
		getTags,
		createTag,
		updateTag,
		deleteTag,
		getUnclassifiedTransactions,
		updateTransaction
	} from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';

	// 상태 관리
	let classes = $state([]);
	let categories = $state([]);
	let subCategories = $state([]);
	let tiers = $state([]);
	let tags = $state([]);
	let unclassifiedTransactions = $state([]);
	let loading = $state(true);
	let error = $state('');

	// 섹션 토글 상태
	let expandedSections = $state({
		unclassified: false,
		category: false,
		subCategory: false,
		tier: false,
		tag: false
	});

	// 선택된 분류
	let selectedClassForCategory = $state(1);
	let selectedClassForTier = $state(1);
	let selectedCategoryForSub = $state(null);

	// 폼 상태
	let showCategoryForm = $state(false);
	let showSubCategoryForm = $state(false);
	let showTierForm = $state(false);
	let showTagForm = $state(false);
	let editingTag = $state(null);

	// 미분류 거래 수정 상태
	let editingTransactionId = $state(null);
	let editTransactionForm = $state({
		category_id: '',
		sub_category_id: ''
	});

	// 카테고리 폼
	let categoryForm = $state({
		class_id: 1,
		name: '',
		display_name: '',
		description: '',
		is_active: true,
		sort_order: 0
	});

	// 하위 카테고리 폼
	let subCategoryForm = $state({
		category_id: '',
		name: '',
		tier_id: '',
		is_active: true
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

	// 태그 폼
	let tagForm = $state({
		name: '',
		description: '',
		color: '#6366f1',
		is_active: true
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
			[classes, categories, subCategories, tiers, tags, unclassifiedTransactions] = await Promise.all([
				getClasses(),
				getCategories(),
				getSubCategories(),
				getTiers(),
				getTags(false), // 모든 태그 조회 (비활성 포함)
				getUnclassifiedTransactions()
			]);
		} catch (err) {
			error = '데이터를 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	function toggleSection(section) {
		expandedSections[section] = !expandedSections[section];
	}

	// 미분류 거래 관련
	function startEditTransaction(transaction) {
		editingTransactionId = transaction.id;
		editTransactionForm = {
			category_id: transaction.category_id,
			sub_category_id: ''
		};
	}

	function cancelEditTransaction() {
		editingTransactionId = null;
		editTransactionForm = {
			category_id: '',
			sub_category_id: ''
		};
	}

	async function handleUpdateTransaction(e) {
		e.preventDefault();
		if (!editTransactionForm.sub_category_id) {
			alert('세부 분류를 선택해주세요.');
			return;
		}
		try {
			await updateTransaction(editingTransactionId, editTransactionForm);
			await loadData();
			cancelEditTransaction();
		} catch (err) {
			alert('거래 업데이트 실패: ' + err.message);
		}
	}

	// 카테고리 관련
	const filteredCategories = $derived(
		categories.filter(c => c.class_id === selectedClassForCategory)
	);

	// 하위 카테고리 관련
	const filteredSubCategories = $derived(
		selectedCategoryForSub 
			? subCategories.filter(sc => sc.category_id === selectedCategoryForSub)
			: []
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

	async function handleCreateSubCategory(e) {
		e.preventDefault();
		try {
			await createSubCategory({
				...subCategoryForm,
				category_id: selectedCategoryForSub
			});
			await loadData();
			resetSubCategoryForm();
			showSubCategoryForm = false;
		} catch (err) {
			alert('하위 카테고리 생성 실패: ' + err.message);
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

	async function handleDeleteSubCategory(subCategoryId) {
		if (!confirm('이 하위 카테고리를 삭제하시겠습니까?\n관련 거래가 있으면 비활성화됩니다.')) return;
		try {
			const result = await deleteSubCategory(subCategoryId);
			alert(result.message);
			await loadData();
		} catch (err) {
			alert('하위 카테고리 삭제 실패: ' + err.message);
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

	function resetSubCategoryForm() {
		subCategoryForm = {
			category_id: selectedCategoryForSub,
			name: '',
			tier_id: '',
			is_active: true
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

	// 태그 관련
	async function handleCreateOrUpdateTag(e) {
		e.preventDefault();
		try {
			if (editingTag) {
				await updateTag(editingTag.id, tagForm);
			} else {
				await createTag(tagForm);
			}
			await loadData();
			resetTagForm();
			showTagForm = false;
			editingTag = null;
		} catch (err) {
			alert('태그 저장 실패: ' + err.message);
		}
	}

	async function handleDeleteTag(tagId) {
		const tag = tags.find(t => t.id === tagId);
		if (!confirm(`'${tag.name}' 태그를 삭제하시겠습니까?\n사용 중이면 비활성화됩니다.`)) return;
		try {
			const result = await deleteTag(tagId, false);
			alert(result.message);
			await loadData();
		} catch (err) {
			alert('태그 삭제 실패: ' + err.message);
		}
	}

	function startEditTag(tag) {
		editingTag = tag;
		tagForm = {
			name: tag.name,
			description: tag.description || '',
			color: tag.color,
			is_active: tag.is_active
		};
		showTagForm = true;
	}

	function resetTagForm() {
		tagForm = {
			name: '',
			description: '',
			color: '#6366f1',
			is_active: true
		};
		editingTag = null;
	}
</script>

<svelte:head>
	<title>관리자 설정 - 가계부</title>
</svelte:head>

<div class="admin-page" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
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
			<section class="manage-section">
				<div class="section-header">
					<h2>📊 거래 분류</h2>
				</div>
				<div class="section-content">
					<div class="class-grid">
						{#each classes as classItem}
							<div class="class-card">
								<div class="class-info">
									<h3>{classItem.display_name}</h3>
									<p class="class-name">{classItem.name}</p>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</section>

			<!-- 미분류 거래 관리 -->
			<section class="manage-section">
				<div class="section-header" onclick={() => toggleSection('unclassified')} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && toggleSection('unclassified')}>
					<h2>⚠️ 미분류 거래 관리 ({unclassifiedTransactions.length})</h2>
					<span class="toggle-icon">{expandedSections.unclassified ? '▼' : '▶'}</span>
				</div>
				
				{#if expandedSections.unclassified}
					<div class="section-content">
						{#if unclassifiedTransactions.length > 0}
							<div class="table-wrapper">
								<table class="data-table">
									<thead>
										<tr>
											<th>날짜</th>
											<th>내용</th>
											<th>금액</th>
											<th>현재 분류</th>
											<th>분류 설정</th>
											<th>작업</th>
										</tr>
									</thead>
									<tbody>
										{#each unclassifiedTransactions as transaction}
											<tr>
												<td>{transaction.date}</td>
												<td>{transaction.name}</td>
												<td>{transaction.cost.toLocaleString()}원</td>
												<td>
													{transaction.class_display_name} &gt; {transaction.category_display_name}
												</td>
												<td>
													{#if editingTransactionId === transaction.id}
														<div class="edit-row">
															<select bind:value={editTransactionForm.category_id}>
																{#each categories.filter(c => c.class_id === transaction.class_id) as cat}
																	<option value={cat.id}>{cat.display_name}</option>
																{/each}
															</select>
															<select bind:value={editTransactionForm.sub_category_id}>
																<option value="">세부 분류 선택</option>
																{#each subCategories.filter(sc => sc.category_id === editTransactionForm.category_id) as sub}
																	<option value={sub.id}>{sub.name}</option>
																{/each}
															</select>
														</div>
													{:else}
														<span class="text-muted">미지정</span>
													{/if}
												</td>
												<td>
													{#if editingTransactionId === transaction.id}
														<div class="action-buttons">
															<button class="save-btn" onclick={handleUpdateTransaction}>저장</button>
															<button class="cancel-btn" onclick={cancelEditTransaction}>취소</button>
														</div>
													{:else}
														<button class="edit-btn" onclick={() => startEditTransaction(transaction)}>수정</button>
													{/if}
												</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						{:else}
							<p class="empty-message">미분류 거래가 없습니다. 모두 분류되었습니다! 🎉</p>
						{/if}
					</div>
				{/if}
			</section>

			<!-- 카테고리 관리 -->
			<section class="manage-section">
				<div class="section-header" onclick={() => toggleSection('category')} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && toggleSection('category')}>
					<h2>🏷️ 카테고리 관리</h2>
					<div class="header-actions">
						<button class="add-btn" onclick={(e) => { 
							e.stopPropagation();
							categoryForm.class_id = selectedClassForCategory;
							showCategoryForm = !showCategoryForm;
							if(showCategoryForm) expandedSections.category = true;
						}}>
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<line x1="12" y1="5" x2="12" y2="19"></line>
								<line x1="5" y1="12" x2="19" y2="12"></line>
							</svg>
							{showCategoryForm ? '닫기' : '새 카테고리'}
						</button>
						<span class="toggle-icon">{expandedSections.category ? '▼' : '▶'}</span>
					</div>
				</div>

				{#if expandedSections.category}
					<div class="section-content">
						<!-- 분류 선택 -->
						<div class="class-filter">
				{#each classTypes as classType}
					<button
						class="class-btn"
						class:active={selectedClassForCategory === classType.id}
						style="--class-color: {classType.color}"
						onclick={() => (selectedClassForCategory = classType.id)}
					>
						{classType.label}
					</button>
				{/each}
			</div>				<!-- 카테고리 추가 폼 -->
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
			<div class="table-wrapper">
				{#if filteredCategories.length > 0}
					<table class="data-table">
						<thead>
							<tr>
								<th>표시명</th>
								<th>영문명</th>
								<th class="text-center" style="width: 60px;">설명</th>
								<th class="text-center">순서</th>
								<th class="text-center">상태</th>
								<th class="text-center">작업</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredCategories as category}
								<tr>
									<td><strong>{category.display_name}</strong></td>
									<td><code>{category.name}</code></td>
									<td class="text-center">
										{#if category.description}
											<span class="tooltip-wrapper">
												<span class="info-icon">ⓘ</span>
												<span class="tooltip-content">{category.description}</span>
											</span>
										{:else}
											-
										{/if}
									</td>
									<td class="text-center">{category.sort_order}</td>
									<td class="text-center">
										<span class="badge" class:active={category.is_active}>
											{category.is_active ? '활성' : '비활성'}
										</span>
									</td>
									<td class="text-center">
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
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{:else}
					<p class="empty-message">카테고리가 없습니다</p>
				{/if}
			</div>
					</div>
				{/if}
			</section>

		<!-- 하위 카테고리 관리 -->
		<section class="manage-section">
			<div class="section-header" onclick={() => toggleSection('subCategory')} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && toggleSection('subCategory')}>
				<h2>📑 세부 분류 관리</h2>
				<div class="header-actions">
					<button class="add-btn" onclick={(e) => { 
						e.stopPropagation();
						if (!selectedCategoryForSub) {
							alert('먼저 카테고리를 선택해주세요.');
							return;
						}
						subCategoryForm.category_id = selectedCategoryForSub;
						showSubCategoryForm = !showSubCategoryForm;
						if(showSubCategoryForm) expandedSections.subCategory = true;
					}}>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="12" y1="5" x2="12" y2="19"></line>
							<line x1="5" y1="12" x2="19" y2="12"></line>
						</svg>
						{showSubCategoryForm ? '닫기' : '새 세부 분류'}
					</button>
					<span class="toggle-icon">{expandedSections.subCategory ? '▼' : '▶'}</span>
				</div>
			</div>

			{#if expandedSections.subCategory}
				<div class="section-content">
					<!-- 카테고리 선택 -->
					<div class="form-group" style="margin-bottom: 1rem;">
				<label>카테고리 선택</label>
				<select bind:value={selectedCategoryForSub} onchange={() => { showSubCategoryForm = false; }}>
					<option value={null}>카테고리를 선택하세요</option>
					{#each categories as category}
						<option value={category.id}>[{classes.find(c => c.id === category.class_id)?.display_name}] {category.display_name}</option>
					{/each}
				</select>
			</div>

			<!-- 하위 카테고리 추가 폼 -->
			{#if showSubCategoryForm && selectedCategoryForSub}
				<div class="form-container">
					<form class="admin-form" onsubmit={handleCreateSubCategory}>
						<div class="form-row">
							<div class="form-group">
								<label>세부 분류명 *</label>
								<input type="text" bind:value={subCategoryForm.name} placeholder="예: 점심" required />
							</div>
							<div class="form-group">
								<label>티어 *</label>
								<select bind:value={subCategoryForm.tier_id} required>
									<option value="">선택하세요</option>
									{#each tiers.filter(t => t.class_id === categories.find(c => c.id === selectedCategoryForSub)?.class_id) as tier}
										<option value={tier.id}>{tier.display_name}</option>
									{/each}
								</select>
							</div>
						</div>
						<div class="form-row">
							<div class="form-group checkbox-group">
								<label>
									<input type="checkbox" bind:checked={subCategoryForm.is_active} />
									활성화
								</label>
							</div>
						</div>
						<div class="form-actions">
							<button type="button" class="btn-cancel" onclick={() => { showSubCategoryForm = false; resetSubCategoryForm(); }}>
								취소
							</button>
							<button type="submit" class="btn-submit">생성</button>
						</div>
					</form>
				</div>
			{/if}

			<!-- 하위 카테고리 리스트 -->
			<div class="table-wrapper">
				{#if selectedCategoryForSub}
					{#if filteredSubCategories.length > 0}
						<table class="data-table">
							<thead>
								<tr>
									<th>세부 분류명</th>
									<th>티어</th>
									<th class="text-center">상태</th>
									<th class="text-center">작업</th>
								</tr>
							</thead>
							<tbody>
								{#each filteredSubCategories as subCategory}
									<tr>
										<td><strong>{subCategory.name}</strong></td>
										<td>
											{tiers.find(t => t.id === subCategory.tier_id)?.display_name || '-'}
										</td>
										<td class="text-center">
											<span class="badge" class:active={subCategory.is_active}>
												{subCategory.is_active ? '활성' : '비활성'}
											</span>
										</td>
										<td class="text-center">
											<button
												class="delete-btn"
												onclick={() => handleDeleteSubCategory(subCategory.id)}
												title="삭제"
												aria-label="세부 분류 삭제"
											>
												<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
													<polyline points="3 6 5 6 21 6" />
													<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
												</svg>
											</button>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					{:else}
						<p class="empty-message">등록된 세부 분류가 없습니다</p>
					{/if}
				{:else}
					<p class="empty-message">카테고리를 선택해주세요</p>
				{/if}
			</div>
				</div>
			{/if}
		</section>

			<!-- 티어 관리 -->
			<section class="manage-section">
				<div class="section-header" onclick={() => toggleSection('tier')} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && toggleSection('tier')}>
					<h2>🎯 티어 관리</h2>
					<div class="header-actions">
						<button class="add-btn" onclick={(e) => { 
							e.stopPropagation();
							tierForm.class_id = selectedClassForTier;
							showTierForm = !showTierForm;
							if(showTierForm) expandedSections.tier = true;
						}}>
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<line x1="12" y1="5" x2="12" y2="19"></line>
								<line x1="5" y1="12" x2="19" y2="12"></line>
							</svg>
							{showTierForm ? '닫기' : '새 티어'}
						</button>
						<span class="toggle-icon">{expandedSections.tier ? '▼' : '▶'}</span>
					</div>
				</div>

				{#if expandedSections.tier}
					<div class="section-content">
						<!-- 분류 선택 -->
						<div class="class-filter">
				{#each classTypes as classType}
					<button
						class="class-btn"
						class:active={selectedClassForTier === classType.id}
						style="--class-color: {classType.color}"
						onclick={() => (selectedClassForTier = classType.id)}
					>
						{classType.label}
					</button>
				{/each}
			</div>				<!-- 티어 추가 폼 -->
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
			<div class="table-wrapper">
				{#if filteredTiers.length > 0}
					<table class="data-table">
						<thead>
							<tr>
								<th>표시명</th>
								<th>영문명</th>
								<th class="text-center">레벨</th>
								<th class="text-center" style="width: 60px;">설명</th>
								<th class="text-center">순서</th>
								<th class="text-center">상태</th>
								<th class="text-center">작업</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredTiers as tier}
								<tr>
									<td><strong>{tier.display_name}</strong></td>
									<td><code>{tier.name}</code></td>
									<td class="text-center">{tier.tier_level}</td>
									<td class="text-center">
										{#if tier.description}
											<span class="tooltip-wrapper">
												<span class="info-icon">ⓘ</span>
												<span class="tooltip-content">{tier.description}</span>
											</span>
										{:else}
											-
										{/if}
									</td>
									<td class="text-center">{tier.sort_order}</td>
									<td class="text-center">
										<span class="badge" class:active={tier.is_active}>
											{tier.is_active ? '활성' : '비활성'}
										</span>
									</td>
									<td class="text-center">
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
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{:else}
					<p class="empty-message">티어가 없습니다</p>
				{/if}
			</div>
					</div>
				{/if}
			</section>			<!-- 태그 관리 -->
			<section class="manage-section">
				<div class="section-header" onclick={() => toggleSection('tag')} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && toggleSection('tag')}>
					<h2>🏷️ 태그 관리</h2>
					<div class="header-actions">
						<button class="add-btn" onclick={(e) => { 
							e.stopPropagation();
							resetTagForm();
							showTagForm = !showTagForm;
							if(showTagForm) expandedSections.tag = true;
						}}>
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<line x1="12" y1="5" x2="12" y2="19"></line>
								<line x1="5" y1="12" x2="19" y2="12"></line>
							</svg>
							{showTagForm ? '닫기' : '새 태그'}
						</button>
						<span class="toggle-icon">{expandedSections.tag ? '▼' : '▶'}</span>
					</div>
				</div>

				{#if expandedSections.tag}
					<div class="section-content">
						<!-- 태그 추가/수정 폼 -->
						{#if showTagForm}
					<div class="form-container">
						<form class="admin-form" onsubmit={handleCreateOrUpdateTag}>
							<h3>{editingTag ? '태그 수정' : '새 태그 추가'}</h3>
							<div class="form-row">
								<div class="form-group">
									<label for="tag-name">태그명 *</label>
									<input
										id="tag-name"
										type="text"
										bind:value={tagForm.name}
										placeholder="예: 차량, 데이트, 카페"
										required
									/>
								</div>
								<div class="form-group">
									<label for="tag-color">색상</label>
									<input
										id="tag-color"
										type="color"
										bind:value={tagForm.color}
									/>
								</div>
							</div>
							<div class="form-group">
								<label for="tag-description">설명</label>
								<input
									id="tag-description"
									type="text"
									bind:value={tagForm.description}
									placeholder="태그 설명 (선택)"
								/>
							</div>
							<div class="form-group">
								<label>
									<input type="checkbox" bind:checked={tagForm.is_active} />
									활성화
								</label>
							</div>
							<div class="form-actions">
								<button type="button" class="btn-cancel" onclick={() => { 
									showTagForm = false; 
									resetTagForm(); 
								}}>
									취소
								</button>
								<button type="submit" class="btn-submit">
									{editingTag ? '수정' : '생성'}
								</button>
							</div>
						</form>
					</div>
				{/if}

				<!-- 태그 리스트 -->
				{#if tags.length > 0}
					<div class="tag-stats">
						<p>총 <strong>{tags.length}개</strong>의 태그 (사용 중: <strong>{tags.filter(t => t.is_active).length}개</strong>)</p>
					</div>
					<div class="table-wrapper">
						<table class="data-table">
							<thead>
								<tr>
									<th style="width: 40px;"></th>
									<th>태그명</th>
									<th>설명</th>
									<th class="text-center">사용 횟수</th>
									<th class="text-center">상태</th>
									<th class="text-center">작업</th>
								</tr>
							</thead>
							<tbody>
								{#each tags as tag}
									<tr>
										<td style="padding: 0;">
											<div style="width: 4px; height: 100%; background: {tag.color}; margin-left: 8px;"></div>
										</td>
										<td><strong>{tag.name}</strong></td>
										<td>{tag.description || '-'}</td>
										<td class="text-center">{tag.usage_count}</td>
										<td class="text-center">
											<span class="badge" class:active={tag.is_active}>
												{tag.is_active ? '활성' : '비활성'}
											</span>
										</td>
										<td class="text-center">
											<div style="display: flex; gap: 8px; justify-content: center;">
												<button
													class="edit-btn"
													onclick={() => startEditTag(tag)}
													title="수정"
													aria-label="태그 수정"
												>
													<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
														<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
														<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
													</svg>
												</button>
												<button
													class="delete-btn"
													onclick={() => handleDeleteTag(tag.id)}
													title="삭제"
													aria-label="태그 삭제"
												>
													<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
														<polyline points="3 6 5 6 21 6" />
														<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
													</svg>
												</button>
											</div>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="empty-message">아직 태그가 없습니다</p>
				{/if}
					</div>
				{/if}
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
		gap: 10px;
	}

	.manage-section {
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 12px;
		padding: 24px;
	}

	.class-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 16px;
	}

	.class-card {
		background: var(--bg-secondary);
		border: 2px solid var(--border-color);
		border-radius: 8px;
		padding: 8px 12px;
	}
	.class-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.class-info h3 {
		font-size: 1.2rem;
		color: var(--text-primary);
	}

	.class-name {
		font-size: 0.9rem;
		color: var(--text-tertiary);
		font-family: monospace;
	}

	.class-filter {
		display: flex;
		max-width: 400px;
		gap: 8px;
		background: #f5f5f5;
		padding: 4px;
		border-radius: 10px;
		margin-bottom: 20px;
	}

	.class-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		padding: 8px 16px;
		background: transparent;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-size: 14px;
		font-weight: 500;
		color: #666;
		transition: all 0.2s ease;
		flex: 1;
	}

	.class-btn:hover {
		background: rgba(33, 150, 243, 0.1);
	}

	.class-btn.active {
		background: white;
		color: var(--class-color);
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
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

	.edit-btn {
		padding: 8px;
		background: transparent;
		border: 1px solid var(--border-color);
		border-radius: 6px;
		color: var(--text-tertiary);
		cursor: pointer;
		transition: all 0.2s;
		flex-shrink: 0;
	}

	.edit-btn:hover {
		background: #e3f2fd;
		border-color: #90caf9;
		color: #1976d2;
	}

	/* 테이블 래퍼 - 스크롤 지원 */
	.table-wrapper {
		max-height: 600px;
		overflow-y: auto;
		overflow-x: auto;
		border-radius: 8px;
		border: 1px solid var(--border-color);
	}

	.table-wrapper::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}

	.table-wrapper::-webkit-scrollbar-track {
		background: var(--bg-secondary);
		border-radius: 4px;
	}

	.table-wrapper::-webkit-scrollbar-thumb {
		background: var(--border-color-dark);
		border-radius: 4px;
	}

	.table-wrapper::-webkit-scrollbar-thumb:hover {
		background: var(--accent);
	}

	/* 정보 아이콘 (툴팁) */
	.tooltip-wrapper {
		position: relative;
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}

	.info-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		cursor: help;
		transition: all 0.2s;
		font-size: 16px;
	}

	.tooltip-wrapper:hover .info-icon {
		transform: scale(1.2);
	}

	.tooltip-content {
		visibility: hidden;
		opacity: 0;
		position: absolute;
		bottom: 100%;
		left: 50%;
		transform: translateX(-50%) translateY(-8px);
		background: var(--text-primary);
		color: white;
		padding: 8px 12px;
		border-radius: 6px;
		font-size: 13px;
		white-space: nowrap;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
		z-index: 1000;
		pointer-events: none;
		transition: all 0.2s ease;
		margin-bottom: 4px;
	}

	.tooltip-content::after {
		content: '';
		position: absolute;
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		border: 6px solid transparent;
		border-top-color: var(--text-primary);
	}

	.tooltip-wrapper:hover .tooltip-content {
		visibility: visible;
		opacity: 1;
		transform: translateX(-50%) translateY(-4px);
	}

	.info-icon:hover {
		color: var(--accent);
		transform: scale(1.1);
	}

	/* 섹션 헤더 및 토글 스타일 */
	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		cursor: pointer;
		user-select: none;
	}

	.section-header:hover h2 {
		color: var(--primary-color);
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 16px;
	}

	.toggle-icon {
		font-size: 1.2rem;
		color: var(--text-tertiary);
		transition: transform 0.2s;
		width: 24px;
		text-align: center;
	}

	.section-content {
		margin-top: 16px;
		animation: slideDown 0.3s ease-out;
	}

	@keyframes slideDown {
		from { opacity: 0; transform: translateY(-10px); }
		to { opacity: 1; transform: translateY(0); }
	}

	/* 미분류 거래 수정 스타일 */
	.edit-row {
		display: flex;
		gap: 8px;
	}

	.edit-row select {
		padding: 6px;
		border: 1px solid var(--border-color);
		border-radius: 4px;
		font-size: 0.9rem;
	}

	.action-buttons {
		display: flex;
		gap: 6px;
		justify-content: center;
	}

	.save-btn, .cancel-btn {
		padding: 6px 12px;
		border-radius: 4px;
		font-size: 0.85rem;
		cursor: pointer;
		border: none;
	}

	.save-btn {
		background: var(--primary-color);
		color: white;
	}

	.cancel-btn {
		background: var(--bg-tertiary);
		color: var(--text-secondary);
	}

	.text-muted {
		color: var(--text-tertiary);
		font-style: italic;
	}

	.tag-stats {
		margin-top: 20px;
		padding: 16px;
		background: var(--bg-tertiary);
		border-radius: 8px;
		text-align: center;
	}

	.tag-stats p {
		margin: 0;
		color: var(--text-secondary);
	}

	.tag-stats strong {
		color: var(--primary-color);
		font-size: 1.1rem;
	}

	.badge.active {
		background: #d4edda;
		color: #155724;
		font-weight: 600;
	}

	/* Tablet/Mobile (< 768px) */
	.admin-page {
		&.tablet {
			padding: 12px;

			.page-header {
				flex-direction: column;
				align-items: flex-start;
				gap: 12px;

				h1 {
					font-size: 1.5rem;
				}
			}

			.section-header {
				align-items: flex-start;
				gap: 8px;

				h2 {
					font-size: 1.3rem;
				}
			}

			.class-grid {
				gap: 4px;
			}

			.class-btn {
				padding: 10px 12px;
				font-size: 0.85rem;
			}

			.form-group {
				flex-direction: column;
				align-items: stretch;

				label {
					min-width: auto;
				}
			}

			.form-actions {
				flex-direction: column-reverse;

				button {
					width: 100%;
				}
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			padding: 8px;

			.page-header h1 {
				font-size: 1.3rem;
			}

			.section-header {
				flex-direction: column;
				align-items: flex-start;
				gap: 4px;
			}

			.section-header h2 {
				font-size: 1.2rem;
			}

			.class-grid {
				grid-template-columns: 1fr 1fr;
				gap: 6px;
			}

			.class-btn {
				width: 100%;
			}

			.badge {
				font-size: 0.7rem;
				padding: 2px 6px;
			}
		}
	}
</style>
