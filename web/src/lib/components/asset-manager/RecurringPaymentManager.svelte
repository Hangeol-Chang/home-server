<script>
	import {
		getRecurringPayments,
		createRecurringPayment,
		updateRecurringPayment,
		deleteRecurringPayment,
		getCategories,
		getSubCategories,
	} from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';

	let payments = $state([]);
	let loading = $state(true);
	let error = $state('');

	// 모달 상태
	let isFormOpen = $state(false);
	let editTarget = $state(null);

	// 폼 데이터
	let selectedClass = $state(1);
	let categories = $state([]);
	let subCategories = $state([]);
	let formData = $state({
		name: '',
		cost: '',
		category_id: '',
		sub_category_id: '',
		day_of_month: 1,
		description: ''
	});
	let isSubmitting = $state(false);
	let isDeleting = $state(false);
	let formError = $state('');

	const classTypes = [
		{ id: 1, label: '지출', color: '#f44336', icon: '💸' },
		{ id: 2, label: '수익', color: '#4caf50', icon: '💰' },
		{ id: 3, label: '저축', color: '#2196f3', icon: '🏦' }
	];

	async function load() {
		loading = true;
		error = '';
		try {
			payments = await getRecurringPayments(false);
		} catch (e) {
			error = e.message || '불러오기 실패';
		} finally {
			loading = false;
		}
	}

	async function loadCategories() {
		try {
			categories = await getCategories(selectedClass);
			if (categories.length > 0 && !formData.category_id) {
				formData.category_id = categories[0].id;
			}
			if (formData.category_id) {
				await loadSubCategories(formData.category_id);
			}
		} catch (e) {
			console.error('카테고리 로드 실패', e);
		}
	}

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
		} catch (e) {
			subCategories = [];
		}
	}

	function handleCategoryChange() {
		if (formData.category_id) {
			loadSubCategories(formData.category_id);
		} else {
			subCategories = [];
			formData.sub_category_id = '';
		}
	}

	function openNew() {
		editTarget = null;
		selectedClass = 1;
		formData = { name: '', cost: '', category_id: '', sub_category_id: '', day_of_month: 1, description: '' };
		formError = '';
		isFormOpen = true;
		loadCategories();
	}

	function openEdit(p) {
		editTarget = p;
		selectedClass = p.class_id;
		formData = {
			name: p.name,
			cost: String(p.cost),
			category_id: p.category_id,
			sub_category_id: p.sub_category_id || '',
			day_of_month: p.day_of_month,
			description: p.description || ''
		};
		formError = '';
		isFormOpen = true;
		loadCategories();
	}

	function closeForm() {
		isFormOpen = false;
		editTarget = null;
	}

	async function handleSubmit(e) {
		e.preventDefault();
		formError = '';
		isSubmitting = true;
		try {
			const payload = {
				name: formData.name,
				cost: parseFloat(formData.cost),
				class_id: selectedClass,
				category_id: parseInt(formData.category_id),
				sub_category_id: formData.sub_category_id ? parseInt(formData.sub_category_id) : undefined,
				day_of_month: parseInt(formData.day_of_month),
				description: formData.description || undefined,
				is_active: true
			};

			if (editTarget) {
				await updateRecurringPayment(editTarget.id, payload);
			} else {
				await createRecurringPayment(payload);
			}
			closeForm();
			await load();
		} catch (e) {
			formError = e.message || '저장 실패';
		} finally {
			isSubmitting = false;
		}
	}

	async function handleDelete() {
		if (!editTarget || !confirm(`"${editTarget.name}" 정기결제를 삭제하시겠습니까?`)) return;
		isDeleting = true;
		try {
			await deleteRecurringPayment(editTarget.id);
			closeForm();
			await load();
		} catch (e) {
			formError = e.message || '삭제 실패';
		} finally {
			isDeleting = false;
		}
	}

	async function handleToggleActive(p) {
		try {
			await updateRecurringPayment(p.id, { is_active: !p.is_active });
			await load();
		} catch (e) {
			alert('상태 변경 실패: ' + e.message);
		}
	}

	onMount(load);
</script>

<div class="module-container">
	<div class="chart-header">
		<h3>🔄 정기 결제 관리</h3>
		<button class="add-btn" onclick={openNew}>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<line x1="12" y1="5" x2="12" y2="19" />
				<line x1="5" y1="12" x2="19" y2="12" />
			</svg>
			추가
		</button>
	</div>

	<p class="recurring-subtitle">매월 설정한 날 KST 정오에 자동으로 소비가 등록됩니다.</p>

	{#if loading}
		<div class="loading"><div class="spinner"></div></div>
	{:else if error}
		<div class="error"><p>{error}</p></div>
	{:else if payments.length === 0}
		<div class="no-data">등록된 정기 결제가 없습니다.</div>
	{:else}
		<div class="items-list">
			{#each payments as p (p.id)}
				{@const classType = classTypes.find(c => c.id === p.class_id)}
				<div class="item-card" class:inactive={!p.is_active}>
					<div class="recurring-left">
						<div class="day-badge">{p.day_of_month}일</div>
						<div class="recurring-info">
							<span class="recurring-name">{p.name}</span>
							<span class="recurring-meta">
								{p.category_display_name}{p.sub_category_name ? ` · ${p.sub_category_name}` : ''}
							</span>
						</div>
					</div>
					<div class="recurring-right">
						<span class="recurring-cost">{p.cost.toLocaleString()}원</span>
						<span class="badge" style="background: {classType?.color}22; color: {classType?.color}">
							{classType?.icon} {classType?.label}
						</span>
						<div class="recurring-actions">
							<button
								class="icon-btn"
								class:danger={false}
								onclick={() => handleToggleActive(p)}
								title={p.is_active ? '비활성화' : '활성화'}
							>
								{#if p.is_active}
									<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
										<rect x="6" y="4" width="4" height="16"></rect>
										<rect x="14" y="4" width="4" height="16"></rect>
									</svg>
								{:else}
									<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
										<polygon points="5 3 19 12 5 21 5 3"></polygon>
									</svg>
								{/if}
							</button>
							<button class="icon-btn" onclick={() => openEdit(p)} title="수정">
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
									<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
								</svg>
							</button>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- 등록/수정 모달 -->
{#if isFormOpen}
	<div class="modal-overlay" onclick={closeForm} role="presentation">
		<div class="modal-container" onclick={(e) => e.stopPropagation()} role="presentation">
			<form onsubmit={handleSubmit}>
				<div class="chart-header">
					<h3>🔄 {editTarget ? '정기결제 수정' : '정기결제 추가'}</h3>
					<button type="button" class="icon-btn" onclick={closeForm} aria-label="닫기">
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
								loadCategories();
							}}
						>
							<span class="class-icon">{classType.icon}</span>
							<span>{classType.label}</span>
						</button>
					{/each}
				</div>

				{#if formError}
					<div class="error-message">⚠️ {formError}</div>
				{/if}

				<!-- 결제명 -->
				<div class="form-group">
					<label for="rp-name">결제명 <span class="required">*</span></label>
					<input
						id="rp-name"
						type="text"
						bind:value={formData.name}
						placeholder="예: 넷플릭스 구독, 월세"
						required
					/>
				</div>

				<!-- 금액 -->
				<div class="form-group">
					<label for="rp-cost">금액 <span class="required">*</span></label>
					<input
						id="rp-cost"
						type="number"
						bind:value={formData.cost}
						placeholder="0"
						min="1"
						step="1"
						required
					/>
				</div>

				<!-- 결제일 -->
				<div class="form-group">
					<label for="rp-day">
						결제일 <span class="required">*</span>
					</label>
					<input
						id="rp-day"
						type="number"
						bind:value={formData.day_of_month}
						min="1"
						max="31"
						required
					/>
					<span class="field-hint">매월 몇 일 (31일 설정 시 말일 처리)</span>
				</div>

				<!-- 카테고리 / 세부 분류 -->
				<div class="form-row">
					<div class="form-group">
						<label for="rp-category">카테고리 <span class="required">*</span></label>
						<select id="rp-category" bind:value={formData.category_id} onchange={handleCategoryChange} required>
							{#each categories as cat}
								<option value={cat.id}>{cat.display_name}</option>
							{/each}
						</select>
					</div>
					<div class="form-group">
						<label for="rp-sub">세부 분류</label>
						<select id="rp-sub" bind:value={formData.sub_category_id} disabled={subCategories.length === 0}>
							{#if subCategories.length === 0}
								<option value="">없음</option>
							{:else}
								{#each subCategories as sc}
									<option value={sc.id}>{sc.name}</option>
								{/each}
							{/if}
						</select>
					</div>
				</div>

				<!-- 메모 -->
				<div class="form-group">
					<label for="rp-desc">메모</label>
					<input
						id="rp-desc"
						type="text"
						bind:value={formData.description}
						placeholder="선택사항"
					/>
				</div>

				<!-- 버튼 -->
				<div class="form-actions">
					{#if editTarget}
						<button type="button" class="btn-danger" onclick={handleDelete} disabled={isSubmitting || isDeleting}>
							{isDeleting ? '삭제 중...' : '삭제'}
						</button>
						<div style="flex-grow: 1;"></div>
					{/if}
					<button type="button" class="btn-cancel" onclick={closeForm} disabled={isSubmitting || isDeleting}>
						취소
					</button>
					<button type="submit" class="btn-submit" disabled={isSubmitting || isDeleting}>
						{isSubmitting ? '저장 중...' : (editTarget ? '수정하기' : '등록하기')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<style>
	.recurring-subtitle {
		margin: -16px 0 20px 0;
		font-size: 0.85rem;
		color: var(--text-tertiary);
	}

	/* 카드 레이아웃 */
	.item-card {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 16px;
		transition: opacity 0.2s;
	}

	.item-card.inactive {
		opacity: 0.4;
	}

	.recurring-left {
		display: flex;
		align-items: center;
		gap: 12px;
		min-width: 0;
	}

	.day-badge {
		min-width: 48px;
		text-align: center;
		font-size: 1rem;
		font-weight: 600;
		color: var(--accent);
		background: var(--bg-tertiary);
		border-radius: 8px;
		padding: 6px 4px;
		flex-shrink: 0;
	}

	.recurring-info {
		display: flex;
		flex-direction: column;
		gap: 3px;
		min-width: 0;
	}

	.recurring-name {
		font-weight: 400;
		font-size: 0.95rem;
		color: var(--text-primary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.recurring-meta {
		font-size: 0.8rem;
		color: var(--text-tertiary);
	}

	.recurring-right {
		display: flex;
		align-items: center;
		gap: 12px;
		flex-shrink: 0;
	}

	.recurring-cost {
		font-weight: 600;
		font-size: 0.95rem;
		color: var(--text-primary);
		white-space: nowrap;
	}

	.recurring-actions {
		display: flex;
		gap: 4px;
	}

	/* 결제일 힌트 */
	.field-hint {
		font-size: 0.78rem;
		color: var(--text-tertiary);
		white-space: nowrap;
	}

	/* class-icon */
	.class-icon {
		font-size: 16px;
	}
</style>
