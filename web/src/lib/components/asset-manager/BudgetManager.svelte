<script>
    import { getBudgets, updateBudget, updateCategoryDefaultBudget, getCategories, getSubCategories } from '$lib/api/asset-manager.js';
    import { onMount } from 'svelte';

    let { year, month, transactions = [] } = $props();

    let categories = $state([]);
    let budgets = $state([]);
    let selectedCategoryId = $state('');
    let subCategories = $state([]);
    let loading = $state(false);
    let subCatLoading = $state(false);

    // 카테고리 그룹화를 위한 파생 상태
    let groupedCategories = $derived.by(() => {
        const groups = {
            'spend': { name: '지출', items: [] },
            'earn': { name: '수익', items: [] },
            'save': { name: '저축', items: [] }
        };
        
        categories.forEach(cat => {
            // class_id 1: spend, 2: earn, 3: save (DB 초기 데이터 기준)
            // 하지만 class_id가 다를 수 있으므로 API에서 class 정보를 같이 주면 좋겠지만
            // 현재 getCategories는 class_id만 줌.
            // 편의상 1,2,3으로 가정하거나, 그냥 평면 리스트로 보여주되 이름순 정렬
            // 여기서는 단순하게 평면 리스트로 하되 class_id로 정렬된 상태를 이용
            
            // 더 정확하게 하려면 classes 정보도 가져와야 하지만, 
            // 일단은 단순 리스트로 구현하고 이름 옆에 (지출) 등을 붙여주는게 나을수도 있음.
            // 하지만 DB 스키마상 class_id 1=spend, 2=earn, 3=save가 고정적이므로 이를 활용
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

    onMount(async () => {
        await loadData();
    });

    // year, month가 바뀌면 예산 데이터 다시 로드
    $effect(() => {
        if (year && month) {
            loadBudgets();
        }
    });

    // 카테고리 선택 시 하위 카테고리 로드
    $effect(() => {
        if (selectedCategoryId) {
            loadSubCategories(selectedCategoryId);
        } else {
            subCategories = [];
        }
    });

    async function loadData() {
        loading = true;
        try {
            const [catData, budgetData] = await Promise.all([
                getCategories(),
                getBudgets(year, month)
            ]);
            categories = catData;
            budgets = budgetData;
        } catch (err) {
            console.error('Failed to load budget data:', err);
        } finally {
            loading = false;
        }
    }

    async function loadBudgets() {
        try {
            budgets = await getBudgets(year, month);
        } catch (err) {
            console.error('Failed to reload budgets:', err);
        }
    }

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
            await updateCategoryDefaultBudget(selectedCategoryId, newAmount);
            const index = categories.findIndex(c => c.id === selectedCategoryId);
            if (index !== -1) {
                categories[index].default_budget = newAmount;
            }
        } catch (err) {
            alert('기본 예산 수정 실패: ' + err.message);
        }
    }

    function formatCurrency(value) {
        return new Intl.NumberFormat('ko-KR').format(value) + '원';
    }
</script>

<div class="budget-manager">
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
                                <span class="tag">{sub.name}</span>
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
        <div class="placeholder">
            <p>카테고리를 선택하여 예산을 설정하세요.</p>
        </div>
    {/if}
</div>

<style>
    .budget-manager {
        margin-top: 32px;
        border-top: 1px solid var(--border-color);
        padding-top: 24px;
    }

    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
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
        border: 1px solid var(--border-color);
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

    .tag {
        font-size: 0.85rem;
        padding: 4px 10px;
        background: var(--bg-tertiary);
        border-radius: 12px;
        color: var(--text-primary);
    }

    .empty-text, .loading-text {
        font-size: 0.9rem;
        color: var(--text-secondary);
        font-style: italic;
    }

    .budget-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

    .placeholder {
        text-align: center;
        padding: 40px;
        background: var(--bg-secondary);
        border-radius: 12px;
        color: var(--text-secondary);
    }
</style>