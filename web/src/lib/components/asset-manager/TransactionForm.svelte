<script>
	import { createTransaction, getCategories, getTiers } from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	let { isOpen = $bindable(false), onSuccess = () => {} } = $props();

	// 거래 분류: 1=지출, 2=수익, 3=저축
	let selectedClass = $state(1);
	let categories = $state([]);
	let tiers = $state([]);

	// 폼 데이터
	let formData = $state({
		name: '',
		cost: '',
		category_id: '',
		tier_id: '',
		date: new Date().toISOString().split('T')[0],
		description: ''
	});

	let isSubmitting = $state(false);
	let error = $state('');

	const classTypes = [
		{ id: 1, name: 'spend', label: '지출', color: '#f44336', icon: '💸' },
		{ id: 2, name: 'earn', label: '수익', color: '#4caf50', icon: '💰' },
		{ id: 3, name: 'save', label: '저축', color: '#2196f3', icon: '🏦' }
	];

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
		}
	});

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
				description: formData.description || undefined
			};

			await createTransaction(transactionData);
			
			// 성공 시 폼 리셋
			resetForm();
			onSuccess();
			isOpen = false;
		} catch (err) {
			error = err.message;
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
			description: ''
		};
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
					step="100"
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
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 12px;
		margin-bottom: 24px;
	}

	.class-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		padding: 16px;
		background: var(--bg-secondary);
		border: 2px solid var(--border-color);
		border-radius: 8px;
		cursor: pointer;
		font-size: 1rem;
		font-weight: 600;
		transition: all 0.2s;
		color: var(--text-secondary);
	}

	.class-btn:hover {
		background: var(--bg-tertiary);
		transform: translateY(-2px);
	}

	.class-btn.active {
		background: var(--class-color);
		color: white;
		border-color: var(--class-color);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	.class-icon {
		font-size: 1.5rem;
	}

	.error-message {
		background: #fee;
		border: 1px solid #fcc;
		border-radius: 8px;
		padding: 12px 16px;
		color: #c33;
		margin-bottom: 20px;
		font-size: 0.9rem;
	}

	.form-group {
		margin-bottom: 20px;
	}

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
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

	.form-actions {
		display: flex;
		gap: 12px;
		justify-content: flex-end;
		margin-top: 24px;
		padding-top: 20px;
		border-top: 1px solid var(--border-color);
	}

	.btn-cancel,
	.btn-submit {
		padding: 12px 24px;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-cancel {
		background: var(--bg-secondary);
		color: var(--text-primary);
		border: 1px solid var(--border-color);
	}

	.btn-cancel:hover:not(:disabled) {
		background: var(--bg-tertiary);
	}

	.btn-submit {
		background: var(--accent);
		color: white;
	}

	.btn-submit:hover:not(:disabled) {
		background: #4f46e5;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
	}

	.btn-cancel:disabled,
	.btn-submit:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	@media (max-width: 768px) {
		.transaction-form-container {
			padding: 16px;
		}

		.class-selector {
			grid-template-columns: 1fr;
		}

		.form-row {
			grid-template-columns: 1fr;
		}

		.form-actions {
			flex-direction: column-reverse;
		}

		.btn-cancel,
		.btn-submit {
			width: 100%;
		}
	}
</style>
