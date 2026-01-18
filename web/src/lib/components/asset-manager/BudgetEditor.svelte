<script>
    import { updateBudget, updateCategory, getSubCategories, getCategories, getBudgets } from '$lib/api/asset-manager.js';
    import { onMount } from 'svelte';

    let { 
        year, 
        month, 
        transactions = [], 
        categories = $bindable([]), 
        budgets = $bindable([]) 
    } = $props();

    let selectedCategoryId = $state('');
    let subCategories = $state([]);
    let subCatLoading = $state(false);

    onMount(async () => {
        if (categories.length === 0) {
            await loadCategories();
        }
        if (budgets.length === 0 && year && month) {
            await loadBudgets();
        }
    });

    $effect(() => {
        if (year && month) {
            loadBudgets();
        }
    });

    async function loadCategories() {
        try {
            categories = await getCategories();
        } catch (err) {
            console.error('Failed to load categories:', err);
        }
    }

    async function loadBudgets() {
        try {
            budgets = await getBudgets(year, month);
        } catch (err) {
            console.error('Failed to load budgets:', err);
        }
    }

    // 카테고리 그룹화를 위한 파생 상태
    let groupedCategories = $derived.by(() => {
        const groups = {
            'spend': { name: '지출', items: [] },
            'earn': { name: '수익', items: [] },
            'save': { name: '저축', items: [] }
        };
        
        categories.forEach(cat => {
            if (cat.class_id === 1) groups.spend.items.push(cat);
            else if (cat.class_id === 2) groups.earn.items.push(cat);
            else if (cat.class_id === 3) groups.save.items.push(cat);
        });
        return groups;
    });

    let selectedCategory = $derived(categories.find(c => c.id === selectedCategoryId));
    let selectedBudget = $derived(budgets.find(b => b.category_id === selectedCategoryId));
    
    let currentSpent = $derived.by(() => {
        if (!selectedCategoryId || !transactions) return 0;
        return transactions
            .filter(t => t.category_id === selectedCategoryId)
            .reduce((sum, t) => sum + t.cost, 0);
    });

    let remainingBudget = $derived.by(() => {
        if (!selectedBudget) return 0;
        return selectedBudget.budget_amount - currentSpent;
    });

    // 카테고리 선택 시 하위 카테고리 로드
    $effect(() => {
        if (selectedCategoryId) {
            loadSubCategories(selectedCategoryId);
        } else {
            subCategories = [];
        }
    });

    async function loadSubCategories(categoryId) {
        subCatLoading = true;
        try {
            subCategories = await getSubCategories(categoryId);
        } catch (err) {
            console.error('Failed to load sub categories:', err);
            subCategories = [];
        } finally {
            subCatLoading = false;
        }
    }

    async function handleBudgetChange(e) {
        const newAmount = parseFloat(e.target.value);
        if (!selectedBudget) return;

        try {
            const updated = await updateBudget(selectedCategoryId, year, month, { budget_amount: newAmount });
            const index = budgets.findIndex(b => b.category_id === selectedCategoryId);
            if (index !== -1) {
                budgets[index] = updated;
            }
        } catch (err) {
            alert('예산 수정 실패: ' + err.message);
        }
    }

    async function handleDefaultBudgetChange(e) {
        const newAmount = parseFloat(e.target.value);
        if (!selectedCategory) return;

        try {
            await updateCategory(selectedCategoryId, { default_budget: newAmount });
            const index = categories.findIndex(c => c.id === selectedCategoryId);
            if (index !== -1) {
                categories[index].default_budget = newAmount;
            }
        } catch (err) {
            alert('기본 예산 수정 실패: ' + err.message);
        }
    }

    async function handleRolloverChange(e) {
        const checked = e.target.checked;
        if (!selectedCategory) return;

        try {
            await updateCategory(selectedCategoryId, { rollover_enabled: checked });
            const index = categories.findIndex(c => c.id === selectedCategoryId);
            if (index !== -1) {
                categories[index].rollover_enabled = checked;
            }
        } catch (err) {
            alert('이월 설정 수정 실패: ' + err.message);
            // Revert checkbox state if needed, but simplistic here
            e.target.checked = !checked;
        }
    }

    function formatCurrency(value) {
        return new Intl.NumberFormat('ko-KR').format(value) + '원';
    }
</script>

<div class="module-container">
    <div class="header">
        <h3>예산 관리</h3>
        <div class="select-wrapper">
            <select bind:value={selectedCategoryId} class="category-select">
                <option value="">카테고리 선택</option>
                <optgroup label="지출">
                    {#each groupedCategories.spend.items as cat}
                        <option value={cat.id}>{cat.display_name}</option>
                    {/each}
                </optgroup>
                <optgroup label="수익">
                    {#each groupedCategories.earn.items as cat}
                        <option value={cat.id}>{cat.display_name}</option>
                    {/each}
                </optgroup>
                <optgroup label="저축">
                    {#each groupedCategories.save.items as cat}
                        <option value={cat.id}>{cat.display_name}</option>
                    {/each}
                </optgroup>
            </select>
        </div>
    </div>

    {#if selectedCategoryId && selectedCategory && selectedBudget}
        <div class="budget-detail-card">
            <div class="info-section">
                <div class="sub-categories">
                    <span class="label">포함 항목:</span>
                    {#if subCatLoading}
                        <span class="loading-text">로딩중...</span>
                    {:else if subCategories.length > 0}
                        <div class="tags">
                            {#each subCategories as sub}
                                <span class="badge">{sub.name}</span>
                            {/each}
                        </div>
                    {:else}
                        <span class="empty-text">하위 카테고리 없음</span>
                    {/if}
                </div>
            </div>

            <div class="budget-grid">
                <div class="budget-item">
                    <label>이번달 예산</label>
                    <div class="input-wrapper">
                        <input 
                            type="number" 
                            value={selectedBudget.budget_amount} 
                            onchange={handleBudgetChange}
                        />
                        {#if selectedBudget.rollover_amount > 0}
                            <span class="rollover-badge" title="지난달에서 이월됨">
                                +{formatCurrency(selectedBudget.rollover_amount)} 이월됨
                            </span>
                        {/if}
                    </div>
                </div>

                <div class="budget-item">
                    <label>기본 예산 (매월)</label>
                    <div class="input-wrapper">
                        <input 
                            type="number" 
                            value={selectedCategory.default_budget || 0} 
                            onchange={handleDefaultBudgetChange}
                        />
                    </div>
                    {#if selectedCategory.class_id === 1}
                        <div class="checkbox-wrapper">
                            <input 
                                type="checkbox" 
                                id="rollover-check"
                                checked={selectedCategory.rollover_enabled !== false}
                                onchange={handleRolloverChange}
                            />
                            <label for="rollover-check">남은 예산 이월 허용</label>
                        </div>
                    {/if}
                </div>

                <div class="stat-item">
                    <label>현재 지출</label>
                    <span class="value">{formatCurrency(currentSpent)}</span>
                </div>

                <div class="stat-item">
                    <label>잔액</label>
                    <span class="value {remainingBudget < 0 ? 'negative' : 'positive'}">
                        {formatCurrency(remainingBudget)}
                    </span>
                </div>
            </div>
        </div>
    {:else if !selectedCategoryId}
        <div class="no-data">
            <p>카테고리를 선택하여 예산을 설정하세요.</p>
        </div>
    {/if}
</div>

<style>
    .module-container {
		padding: 28px;
		margin: 24px 0;
		container-type: inline-size;
    }

    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }

    h3 {
        margin: 0;
        font-size: 1.1rem;
        color: var(--text-primary);
    }

    .category-select {
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid var(--border-color);
        background: var(--bg-secondary);
        color: var(--text-primary);
        font-size: 0.95rem;
        min-width: 200px;
    }

    .budget-detail-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 20px;
    }

    .info-section {
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border-color);
    }

    .sub-categories {
        display: flex;
        align-items: flex-start;
        gap: 12px;
    }

    .sub-categories .label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin-top: 4px;
        white-space: nowrap;
    }

    .tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .empty-text, .loading-text {
        font-size: 0.9rem;
        color: var(--text-secondary);
        font-style: italic;
    }

    .budget-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr 1fr;
        gap: 24px;
    }

    .budget-item label, .stat-item label {
        display: block;
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin-bottom: 8px;
    }

    .input-wrapper {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .checkbox-wrapper {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
    }

    .checkbox-wrapper input[type="checkbox"] {
        width: auto;
        margin: 0;
        cursor: pointer;
    }

    .checkbox-wrapper label {
        margin: 0;
        font-size: 0.85rem;
        cursor: pointer;
        color: var(--text-secondary);
    }

    input[type="number"] {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        background: var(--bg-primary);
        color: var(--text-primary);
        font-size: 1rem;
    }

    .rollover-badge {
        font-size: 0.8rem;
        color: var(--text-success);
    }

    .stat-item .value {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .stat-item .value.positive { color: var(--text-success); }
    .stat-item .value.negative { color: var(--text-danger); }


    @media (max-width: 768px) {
        .budget-grid {
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
    }

</style>