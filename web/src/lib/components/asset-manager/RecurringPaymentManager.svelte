<script>
	import { tabNav } from '$lib/tabNav.js';
	import {
		getRecurringPayments,
		createRecurringPayment,
		updateRecurringPayment,
		deleteRecurringPayment,
		getCategories,
		getSubCategories,
	} from '$lib/api/asset-manager.js';
	import { onMount } from 'svelte';
	import TransactionTypeIcon from '$lib/components/ui/TransactionTypeIcon.svelte';

	let payments = $state([]);
	let loading = $state(true);
	let error = $state('');
	let isExpanded = $state(false);

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
		{ id: 1, label: '지출', color: 'var(--danger)', type: 'spend' },
		{ id: 2, label: '수익', color: 'var(--success)', type: 'earn' },
		{ id: 3, label: '저축', color: 'var(--ink)', type: 'save' }
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
		<button class="recurring-toggle" onclick={() => (isExpanded = !isExpanded)}>
			<svg
				class="chevron"
				class:expanded={isExpanded}
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
			>
				<polyline points="9 18 15 12 9 6"></polyline>
			</svg>
			<h3>정기 결제 관리</h3>
			<span class="recurring-count">{payments.length}건</span>
		</button>
		<button class="add-btn" onclick={openNew}>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<line x1="12" y1="5" x2="12" y2="19" />
				<line x1="5" y1="12" x2="19" y2="12" />
			</svg>
			추가
		</button>
	</div>

	{#if isExpanded}
		<p class="recurring-subtitle">매월 설정한 날 KST 정오에 자동으로 소비가 등록됩니다.</p>

		{#if loading}
			<div class="loading"><div class="spinner"></div></div>
		{:else if error}
			<div class="error"><p>{error}</p></div>
		{:else if payments.length === 0}
			<div class="no-data">등록된 정기 결제가 없습니다.</div>
		{:else}
			<div class="table-wrapper">
				<table class="data-table">
					<thead>
						<tr>
							<th>결제일</th>
							<th>결제명</th>
							<th>분류</th>
							<th class="text-right">금액</th>
							<th class="text-center">작업</th>
						</tr>
					</thead>
					<tbody>
						{#each payments as p (p.id)}
							{@const classType = classTypes.find((c) => c.id === p.class_id)}
							<tr class:inactive={!p.is_active}>
								<td>매월 {p.day_of_month}일</td>
								<td>{p.name}</td>
								<td>
									<span class="badge" style="background: color-mix(in srgb, {classType?.color} 13%, transparent); color: {classType?.color}">
										{classType?.label}
									</span>
									<span class="recurring-meta">
										{p.category_display_name}{p.sub_category_name ? ` · ${p.sub_category_name}` : ''}
									</span>
								</td>
								<td class="text-right"><span class="cell-amount">{p.cost.toLocaleString()}원</span></td>
								<td class="text-center">
									<div class="recurring-actions">
										<button
											class="icon-btn"
											onclick={() => handleToggleActive(p)}
											title={p.is_active ? '비활성화' : '활성화'}
											aria-label={p.is_active ? '비활성화' : '활성화'}
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
										<button class="icon-btn" onclick={() => openEdit(p)} title="수정" aria-label="수정">
											<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
												<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
												<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
											</svg>
										</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	{/if}
</div>

<!-- 등록/수정 모달 -->
{#if isFormOpen}
	<div class="modal-overlay" onclick={closeForm} role="presentation">
		<div class="modal-container" onclick={(e) => e.stopPropagation()} role="presentation">
			<form use:tabNav onsubmit={handleSubmit}>
				<div class="chart-header">
					<h3>{editTarget ? '정기결제 수정' : '정기결제 추가'}</h3>
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
							<span class="class-icon"><TransactionTypeIcon type={classType.type} /></span>
							<span>{classType.label}</span>
						</button>
					{/each}
				</div>

				{#if formError}
					<div class="error-message">{formError}</div>
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
	.recurring-toggle {
		display: flex;
		align-items: center;
		gap: 8px;
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
	}

	.recurring-toggle h3 {
		margin: 0;
	}

	.recurring-count {
		font-size: 0.85rem;
		color: var(--text-tertiary);
	}

	.chevron {
		color: var(--text-tertiary);
		transition: transform 0.2s;
		flex-shrink: 0;
	}

	.chevron.expanded {
		transform: rotate(90deg);
	}

	.recurring-subtitle {
		margin: -16px 0 20px 0;
		font-size: 0.85rem;
		color: var(--text-tertiary);
	}

	tr.inactive {
		opacity: 0.4;
	}

	.recurring-meta {
		margin-left: 6px;
		font-size: 0.8rem;
		color: var(--text-tertiary);
	}

	.recurring-actions {
		display: flex;
		justify-content: center;
		gap: 4px;
	}

	/* 결제일 힌트 */
	.field-hint {
		font-size: 0.78rem;
		color: var(--text-tertiary);
		white-space: normal;
		word-break: keep-all;
	}

	/* class-icon */
	.class-icon {
		font-size: 16px;
	}
</style>
