<script>
	import { createTransaction, getCategories, getTiers, getTags } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	let { isOpen = $bindable(false), onSuccess = () => {} } = $props();

	// 거래 분류: 1=지출, 2=수익, 3=저축
	let selectedClass = $state(1);
	let categories = $state([]);
	let tiers = $state([]);
	let availableTags = $state([]);

	// 폼 데이터
	let formData = $state({
		name: '',
		cost: '',
		category_id: '',
		tier_id: '',
		date: new Date().toISOString().split('T')[0],
		description: '',
		tags: []
	});

	let tagInput = $state('');
	let showTagSuggestions = $state(false);
	let filteredTagSuggestions = $state([]);

	let isSubmitting = $state(false);
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
			if (tiers.length > 0 && !formData.tier_id) {
				// 구분없음(tier_level=99) 찾기
				const defaultTier = tiers.find(t => t.tier_level === 99) || tiers[0];
				formData.tier_id = defaultTier.id;
			}
		} catch (err) {
			error = '카테고리/티어 로드 실패: ' + err.message;
		}
	}

	// 거래 분류 변경 시
	$effect(() => {
		if (isOpen) {
			loadCategoriesAndTiers();
			loadTags();
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
				tier_id: parseInt(formData.tier_id),
				date: formData.date,
				description: formData.description || undefined,
				tags: formData.tags.length > 0 ? formData.tags : undefined
			};

			console.log('거래 등록 요청:', transactionData);
			const result = await createTransaction(transactionData);
			console.log('거래 등록 성공:', result);
			
			// 성공 시 폼 리셋
			try {
				resetForm();
				if (typeof onSuccess === 'function') {
					await onSuccess();
				}
				isOpen = false;
			} catch (callbackErr) {
				console.error('성공 콜백 실행 중 에러:', callbackErr);
				// 콜백 에러는 사용자에게 보여주지 않음 (거래는 성공)
				isOpen = false;
			}
		} catch (err) {
			console.error('거래 등록 실패:', err);
			error = err?.message || err?.toString() || '거래 등록에 실패했습니다';
		} finally {
			isSubmitting = false;
		}
	}

	function resetForm() {
		formData = {
			name: '',
			cost: '',
			category_id: categories[0]?.id || '',
			tier_id: tiers.find(t => t.tier_level === 99)?.id || tiers[0]?.id || '',
			date: new Date().toISOString().split('T')[0],
			description: '',
			tags: []
		};
		tagInput = '';
	}

	function handleCancel() {
		resetForm();
		error = '';
		isOpen = false;
	}
</script>

{#if isOpen}
	<div class="transaction-form-container">
		<form class="transaction-form" onsubmit={handleSubmit}>
			<div class="form-header">
				<h3>📝 거래 등록</h3>
				<button type="button" class="close-btn" onclick={handleCancel} aria-label="닫기">
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
							formData.tier_id = '';
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
					<select id="category" bind:value={formData.category_id} required>
						{#each categories as category}
							<option value={category.id}>{category.display_name}</option>
						{/each}
					</select>
				</div>

				<!-- 티어 -->
				<div class="form-group">
					<label for="tier">
						분류 <span class="required">*</span>
					</label>
					<select id="tier" bind:value={formData.tier_id} required>
						{#each tiers as tier}
							<option value={tier.id}>{tier.display_name}</option>
						{/each}
					</select>
				</div>
			</div>

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
				/>
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
				<button type="button" class="btn-cancel" onclick={handleCancel} disabled={isSubmitting}>
					취소
				</button>
				<button type="submit" class="btn-submit" disabled={isSubmitting}>
					{isSubmitting ? '등록 중...' : '등록하기'}
				</button>
			</div>
		</form>
	</div>
{/if}

<style>
	.transaction-form-container {
		background: var(--bg-primary);
		border: 2px solid var(--border-color);
		border-radius: 12px;
		padding: 24px;
		margin-bottom: 32px;
		box-shadow: var(--shadow-md);
		animation: slideDown 0.3s ease-out;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.transaction-form {
		max-width: 800px;
		margin: 0 auto;
	}

	.form-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 24px;
		padding-bottom: 16px;
		border-bottom: 2px solid var(--border-color);
	}

	.form-header h3 {
		margin: 0;
		font-size: 1.5rem;
		color: var(--text-primary);
	}

	.close-btn {
		background: none;
		border: none;
		cursor: pointer;
		padding: 4px;
		color: var(--text-tertiary);
		transition: all 0.2s;
		border-radius: 4px;
	}

	.close-btn:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
	}

	.class-selector {
		display: flex;
		max-width: 400px;
		gap: 8px;
		background: #f5f5f5;
		padding: 4px;
		border-radius: 10px;
		margin-bottom: 24px;
	}

	.class-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		padding: 8px;
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

	.class-icon {
		font-size: 16px;
	}

	/* 폼 스타일 커스터마이징 */
	.error-message {
		background: #fee;
		border: 1px solid #fcc;
		border-radius: 8px;
		padding: 12px 16px;
		color: #c33;
		margin-bottom: 20px;
		font-size: 0.9rem;
	}

	label {
		display: block;
		margin-bottom: 8px;
		font-weight: 600;
		color: var(--text-primary);
		font-size: 0.95rem;
	}

	.required {
		color: #f44336;
	}

	input[type='text'],
	input[type='number'],
	input[type='date'],
	select,
	textarea {
		width: 100%;
		padding: 12px 16px;
		border: 1px solid var(--border-color);
		border-radius: 8px;
		font-size: 1rem;
		background: var(--bg-secondary);
		color: var(--text-primary);
		transition: all 0.2s;
	}

	.tag-input-container {
		position: relative;
	}

	.tag-input-wrapper {
		display: flex;
		gap: 8px;
	}

	.tag-input-wrapper input {
		flex: 1;
	}

	.tag-suggestions {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		box-shadow: var(--shadow-lg);
		max-height: 200px;
		overflow-y: auto;
		z-index: 100;
		margin-top: 4px;
	}

	.tag-suggestion-item {
		width: 100%;
		padding: 10px 16px;
		text-align: left;
		background: none;
		border: none;
		color: var(--text-primary);
		cursor: pointer;
		transition: background 0.2s;
		font-size: 0.95rem;
	}

	.tag-suggestion-item:hover {
		background: var(--bg-tertiary);
	}

	.btn-add-tag {
		padding: 12px 20px;
		background: var(--primary-color, #2196f3);
		color: white;
		border: none;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
		white-space: nowrap;
	}

	.btn-add-tag:hover:not(:disabled) {
		background: var(--primary-dark, #1976d2);
		transform: translateY(-1px);
	}

	.btn-add-tag:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.tag-list {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-top: 12px;
	}

	.tag {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 6px 12px;
		background: var(--primary-color, #2196f3);
		color: white;
		border-radius: 16px;
		font-size: 0.9rem;
		font-weight: 500;
	}

	.tag-remove {
		background: none;
		border: none;
		color: white;
		font-size: 1.2rem;
		line-height: 1;
		cursor: pointer;
		padding: 0;
		margin: 0;
		width: 18px;
		height: 18px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		transition: background 0.2s;
	}

	.tag-remove:hover {
		background: rgba(255, 255, 255, 0.2);
	}

	input:focus,
	select:focus,
	textarea:focus {
		outline: none;
		border-color: var(--accent);
		box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
	}

	textarea {
		resize: vertical;
		font-family: inherit;
	}

	/* 폼 액션 오버라이드 */
	.form-actions {
		margin-top: 24px;
		padding-top: 20px;
		border-top: 1px solid var(--border-color);
	}

	.btn-cancel,
	.btn-submit {
		padding: 12px 24px;
		font-size: 1rem;
	}

	.btn-cancel:disabled,
	.btn-submit:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* 태블릿 */
	@media (max-width: 1024px) {
		.transaction-form {
			padding: 20px;
		}

		.class-selector {
			max-width: 100%;
		}
	}

	/* 모바일 */
	@media (max-width: 768px) {
		.transaction-form-container {
			padding: 12px;
		}

		.transaction-form {
			padding: 16px;
			max-width: 100%;
		}

		.form-header h3 {
			font-size: 1.3rem;
		}

		.close-btn {
			padding: 6px;
		}

		.class-selector {
			max-width: 100%;
			flex-direction: row;
			gap: 6px;
		}

		.class-btn {
			padding: 10px 8px;
			font-size: 0.85rem;
			flex-direction: column;
			gap: 4px;
		}

		label {
			font-size: 0.9rem;
			margin-bottom: 6px;
		}

		input[type='text'],
		input[type='number'],
		input[type='date'],
		select,
		textarea {
			padding: 10px 12px;
			font-size: 0.95rem;
		}

		.tag-input-wrapper {
			flex-direction: column;
		}

		.btn-add-tag {
			width: 100%;
			padding: 10px 16px;
		}

		.form-actions {
			flex-direction: column-reverse;
			gap: 10px;
		}

		.btn-cancel,
		.btn-submit {
			width: 100%;
			justify-content: center;
		}
	}

	/* 모바일 소형 */
	@media (max-width: 480px) {
		.transaction-form-container {
			padding: 8px;
		}

		.transaction-form {
			padding: 12px;
		}

		.form-header h3 {
			font-size: 1.2rem;
		}

		.class-selector {
			flex-direction: column;
			gap: 6px;
		}

		.class-btn {
			flex-direction: row;
			padding: 10px 12px;
			font-size: 0.9rem;
		}

		label {
			font-size: 0.85rem;
		}

		input[type='text'],
		input[type='number'],
		input[type='date'],
		select,
		textarea {
			padding: 8px 10px;
			font-size: 0.9rem;
		}

		.tag {
			font-size: 0.85rem;
			padding: 5px 10px;
		}
	}
</style>
