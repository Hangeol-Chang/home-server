<script>
	import { createTransaction, updateTransaction, deleteTransaction, getCategories, getSubCategories, getTiers, getTags } from '$lib/api/asset-manager.js';
	import { onMount, untrack } from 'svelte';
	import { device } from '$lib/stores/device';

	let { 
		isOpen = $bindable(false), 
		onSuccess = () => {},
		initialDate = null,
		initialTransaction = null,
	} = $props();

	// 거래 분류: 1=지출, 2=수익, 3=저축
	let selectedClass = $state(1);
	let categories = $state([]);
	let subCategories = $state([]);
	let tiers = $state([]);
	let availableTags = $state([]);

	// 폼 데이터
	let formData = $state({
		name: '',
		cost: '',
		category_id: '',
		sub_category_id: '',
		date: initialDate || new Date().toISOString().split('T')[0],
		description: '',
		tags: []
	});

	let tagInput = $state('');
	let showTagSuggestions = $state(false);
	let filteredTagSuggestions = $state([]);

	let isSubmitting = $state(false);
	let isDeleting = $state(false);
	let error = $state('');

	const classTypes = [
		{ id: 1, name: 'spend', label: '지출', color: '#f44336', icon: '💸' },
		{ id: 2, name: 'earn', label: '수익', color: '#4caf50', icon: '💰' },
		{ id: 3, name: 'save', label: '저축', color: '#2196f3', icon: '🏦' }
	];

	// 태그 목록 로드
	async function loadTags() {
		try {
			const tags = await getTags();
			// 태그 데이터가 객체 배열인지 문자열 배열인지 확인
			if (tags && tags.length > 0) {
				if (typeof tags[0] === 'string') {
					// 문자열 배열인 경우 객체로 변환
					availableTags = tags.map(tag => ({ name: tag }));
				} else {
					// 이미 객체 배열인 경우 그대로 사용
					availableTags = tags;
				}
			} else {
				availableTags = [];
			}
			console.log('태그 로드 완료:', availableTags);
		} catch (err) {
			console.error('태그 로드 실패:', err);
			availableTags = [];
		}
	}

	// 카테고리와 티어 로드
	async function loadCategoriesAndTiers() {
		try {
			[categories, tiers] = await Promise.all([
				getCategories(selectedClass),
				getTiers(selectedClass)
			]);
			
			// 기본값 설정
			if (categories.length > 0 && !formData.category_id) {
				formData.category_id = categories[0].id;
			}
			
			// 카테고리가 선택되어 있으면 하위 카테고리 로드
			if (formData.category_id) {
				await loadSubCategories(formData.category_id);
			}
		} catch (err) {
			error = '카테고리/티어 로드 실패: ' + err.message;
		}
	}

	// 하위 카테고리 로드
	async function loadSubCategories(categoryId) {
		try {
			subCategories = await getSubCategories(categoryId);
			if (subCategories.length > 0) {
				if (!formData.sub_category_id || !subCategories.find(s => s.id == formData.sub_category_id)) {
					formData.sub_category_id = subCategories[0].id;
				}
			} else {
				formData.sub_category_id = '';
			}
		} catch (err) {
			console.error('하위 카테고리 로드 실패:', err);
			subCategories = [];
		}
	}

	// 카테고리 변경 시 하위 카테고리 로드
	function handleCategoryChange() {
		if (formData.category_id) {
			loadSubCategories(formData.category_id);
		} else {
			subCategories = [];
			formData.sub_category_id = '';
		}
	}

	// 거래 폼 열릴 때 초기화
	$effect(() => {
		if (isOpen) {
			untrack(() => {
				const isFirstLoad = !formData.name;
				if (initialTransaction && isFirstLoad) {
					selectedClass = initialTransaction.class_id;
					formData.name = initialTransaction.name;
					formData.cost = String(Math.abs(initialTransaction.cost));
					formData.date = initialTransaction.date;
					formData.description = initialTransaction.description || '';
					formData.tags = initialTransaction.tags ? [...initialTransaction.tags] : [];
					formData.category_id = initialTransaction.category_id;
					formData.sub_category_id = initialTransaction.sub_category_id || '';
					
					loadCategoriesAndTiers();
				} else if (initialDate && isFirstLoad) {
					formData.date = initialDate;
					loadCategoriesAndTiers();
				} else if (isFirstLoad) {
					loadCategoriesAndTiers();
				}
			});
			// 태그는 폼 열릴때마다 로드
			untrack(() => loadTags());
		}
	});

	// 태그 입력 변경 시 필터링
	$effect(() => {
		if (tagInput.trim()) {
			const input = tagInput.toLowerCase();
			filteredTagSuggestions = availableTags.filter(
				tag => tag.name.toLowerCase().includes(input) && !formData.tags.includes(tag.name)
			);
			showTagSuggestions = filteredTagSuggestions.length > 0;
		} else {
			showTagSuggestions = false;
			filteredTagSuggestions = [];
		}
	});

	function addTag(tagToAdd = null) {
		const tag = (tagToAdd || tagInput).trim();
		if (tag && !formData.tags.includes(tag)) {
			formData.tags = [...formData.tags, tag];
			tagInput = '';
			showTagSuggestions = false;
		}
	}

	function removeTag(tagToRemove) {
		formData.tags = formData.tags.filter(tag => tag !== tagToRemove);
	}

	function handleTagKeydown(e) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addTag();
		} else if (e.key === 'Escape') {
			showTagSuggestions = false;
		}
	}

	function selectSuggestion(tag) {
		addTag(tag.name);
	}

	async function handleSubmit(e) {
		e.preventDefault();
		error = '';
		isSubmitting = true;

		try {
			const transactionData = {
				name: formData.name,
				cost: parseFloat(formData.cost),
				class_id: selectedClass,
				category_id: parseInt(formData.category_id),
				sub_category_id: formData.sub_category_id ? parseInt(formData.sub_category_id) : undefined,
				date: formData.date,
				description: formData.description || undefined,
				tags: formData.tags.length > 0 ? formData.tags : undefined
			};

			if (initialTransaction && initialTransaction.id) {
				console.log('거래 수정 요청:', transactionData);
				const result = await updateTransaction(initialTransaction.id, transactionData);
				console.log('거래 수정 성공:', result);
			} else {
				console.log('거래 등록 요청:', transactionData);
				const result = await createTransaction(transactionData);
				console.log('거래 등록 성공:', result);
			}
			
			// 성공 시 폼 리셋
			try {
				resetForm();
				if (typeof onSuccess === 'function') {
					await onSuccess();
				}
				isOpen = false;
			} catch (callbackErr) {
				console.error('성공 콜백 실행 중 에러:', callbackErr);
				isOpen = false;
			}
		} catch (err) {
			console.error('거래 저장 실패:', err);
			error = err?.message || err?.toString() || '거래 저장에 실패했습니다';
		} finally {
			isSubmitting = false;
		}
	}

	async function handleDelete() {
		if (!initialTransaction || !initialTransaction.id || !confirm('정말 이 거래 내역을 삭제하시겠습니까?')) {
			return;
		}

		error = '';
		isDeleting = true;

		try {
			console.log('거래 삭제 요청:', initialTransaction.id);
			await deleteTransaction(initialTransaction.id);
			console.log('거래 삭제 성공');
			
			try {
				resetForm();
				if (typeof onSuccess === 'function') {
					await onSuccess();
				}
				isOpen = false;
			} catch (callbackErr) {
				console.error('성공 콜백 실행 중 에러:', callbackErr);
				isOpen = false;
			}
		} catch (err) {
			console.error('거래 삭제 실패:', err);
			error = err?.message || err?.toString() || '거래 삭제에 실패했습니다';
		} finally {
			isDeleting = false;
		}
	}

	function resetForm() {
		formData = {
			name: '',
			cost: '',
			category_id: categories[0]?.id || '',
			sub_category_id: '',
			date: initialDate || new Date().toISOString().split('T')[0],
			description: '',
			tags: []
		};
		tagInput = '';
		if (formData.category_id) {
			loadSubCategories(formData.category_id);
		}
	}

	function handleCancel() {
		resetForm();
		error = '';
		isOpen = false;
	}
</script>

{#snippet formContent()}
	<form class="transaction-form" onsubmit={handleSubmit}>
		<div class="chart-header">
			<h3>📝 {initialTransaction ? '거래 수정' : '거래 등록'}</h3>
			<button type="button" class="icon-btn" onclick={handleCancel} aria-label="닫기">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="18" y1="6" x2="6" y2="18"></line>
					<line x1="6" y1="6" x2="18" y2="18"></line>
				</svg>
			</button>
		</div>

		<!-- 거래 분류 선택 -->
		<div class="class-selector">
			{#each classTypes as classType}
				<button
					type="button"
					class="class-btn"
					class:active={selectedClass === classType.id}
					style="--class-color: {classType.color}"
					onclick={() => {
						selectedClass = classType.id;
						formData.category_id = '';
						loadCategoriesAndTiers();
					}}
				>
					<span class="class-icon">{classType.icon}</span>
					<span>{classType.label}</span>
				</button>
			{/each}
		</div>

		{#if error}
			<div class="error-message">⚠️ {error}</div>
		{/if}

		<!-- 날짜 -->
		<div class="form-group">
			<label for="date">
				날짜 <span class="required">*</span>
			</label>
			<input
				id="date"
				type="date"
				bind:value={formData.date}
				required
				onclick={(e) => e.currentTarget.showPicker()}
			/>
		</div>


		<!-- 거래명 -->
		<div class="form-group">
			<label for="name">
				거래명 <span class="required">*</span>
			</label>
			<input
				id="name"
				type="text"
				bind:value={formData.name}
				placeholder="예: 점심 식사, 월급 등"
				required
			/>
		</div>

		<!-- 금액 -->
		<div class="form-group">
			<label for="cost">
				금액 <span class="required">*</span>
			</label>
			<input
				id="cost"
				type="number"
				bind:value={formData.cost}
				placeholder="0"
				min="0"
				step="1"
				required
			/>
		</div>

		<div class="form-row">
			<!-- 카테고리 -->
			<div class="form-group">
				<label for="category">
					카테고리 <span class="required">*</span>
				</label>
				<select id="category" bind:value={formData.category_id} onchange={handleCategoryChange} required>
					{#each categories as category}
						<option value={category.id}>{category.display_name}</option>
					{/each}
				</select>
			</div>

			<!-- 하위 카테고리 -->
			<div class="form-group">
				<label for="sub_category">
					세부 분류 <span class="required">*</span>
				</label>
				<select id="sub_category" bind:value={formData.sub_category_id} required disabled={!formData.category_id || subCategories.length === 0}>
					{#if subCategories.length === 0}
						<option value="">세부 분류 없음</option>
					{:else}
						{#each subCategories as subCategory}
							<option value={subCategory.id}>{subCategory.name}</option>
						{/each}
					{/if}
				</select>
			</div>
		</div>

		<!-- 설명 -->
		<div class="form-group">
			<label for="description">설명 (선택)</label>
			<textarea
				id="description"
				bind:value={formData.description}
				placeholder="추가 설명을 입력하세요"
				rows="3"
			></textarea>
		</div>

		<!-- 태그 -->
		<div class="form-group">
			<label for="tags">태그 (선택)</label>
			<div class="tag-input-container">
				<div class="tag-input-wrapper">
					<input
						id="tags"
						type="text"
						bind:value={tagInput}
						placeholder="태그 입력 후 Enter (예: 차량, 데이트, 카페)"
						onkeydown={handleTagKeydown}
						onfocus={() => {
							if (tagInput.trim() && filteredTagSuggestions.length > 0) {
								showTagSuggestions = true;
							}
						}}
					/>
					<button type="button" class="btn-add-tag" onclick={() => addTag()} disabled={!tagInput.trim()}>
						추가
					</button>
				</div>
				{#if showTagSuggestions}
					<div class="tag-suggestions">
						{#each filteredTagSuggestions as suggestion}
							<button
								type="button"
								class="tag-suggestion-item"
								onclick={() => selectSuggestion(suggestion)}
							>
								{suggestion.name}
							</button>
						{/each}
					</div>
				{/if}
			</div>
			{#if formData.tags.length > 0}
				<div class="tag-list">
					{#each formData.tags as tag}
						<span class="tag">
							{tag}
							<button type="button" class="tag-remove" onclick={() => removeTag(tag)} aria-label="태그 제거">
								×
							</button>
						</span>
					{/each}
				</div>
			{/if}
		</div>

		<!-- 버튼 -->
		<div class="form-actions">
			{#if initialTransaction}
			<button type="button" class="btn-danger" onclick={handleDelete} disabled={isSubmitting || isDeleting}>
				{isDeleting ? '삭제 중...' : '삭제'}
			</button>
			<div style="flex-grow: 1;"></div>
			{/if}
			<button type="button" class="btn-cancel" onclick={handleCancel} disabled={isSubmitting || isDeleting}>
				취소
			</button>
			<button type="submit" class="btn-submit" disabled={isSubmitting || isDeleting}>
				{isSubmitting ? '저장 중...' : (initialTransaction ? '수정하기' : '등록하기')}
			</button>
		</div>
	</form>
{/snippet}	

{#if isOpen}
	<div class="modal-overlay" onclick={handleCancel} role="presentation">
		<div class="modal-container" class:mobile={$device.isMobile} class:tablet={$device.isTablet} onclick={(e) => e.stopPropagation()} role="presentation">
			{@render formContent()}
		</div>
	</div>
{/if}

<style>
	.transaction-form {
		max-width: 800px;
		margin: 0 auto;
	}

	.class-icon {
		font-size: 16px;
	}

	textarea {
		resize: vertical;
		font-family: inherit;
	}
</style>
