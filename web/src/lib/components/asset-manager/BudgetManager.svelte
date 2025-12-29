<script>
    import { getBudgets, getCategories, getSubCategories, getTransactions } from '$lib/api/asset-manager.js';
    import TransactionDropdown from './TransactionDropdown.svelte';
    import BudgetEditor from './BudgetEditor.svelte';
    import { onMount } from 'svelte';

    let { year, month, transactions = $bindable([]) } = $props();

    let categories = $state([]);
    let budgets = $state([]);
    let loading = $state(false);

    let allSubCategories = $state([]); // 모든 하위 카테고리 (툴팁용)

    // Transaction Dropdown State
    let showTransactionDropdown = $state(false);
    let transactionDropdownTitle = $state('');
    let transactionDropdownList = $state([]);

    function openTransactionDropdown(categoryName, categoryId) {
        transactionDropdownTitle = `${categoryName} 지출 내역`;
        transactionDropdownList = transactions.filter(t => t.category_id === categoryId);
        showTransactionDropdown = true;
    }

    // 지출 예산 분포 계산
    let budgetDistribution = $derived.by(() => {
        // 지출 카테고리 ID 목록
        const spendCategoryIds = new Set(categories.filter(c => c.class_id === 1).map(c => c.id));
        
        // 지출 예산만 필터링 (0원 초과)
        const spendBudgets = budgets.filter(b => spendCategoryIds.has(b.category_id) && b.budget_amount > 0);
        
        const totalSpend = spendBudgets.reduce((sum, b) => sum + b.budget_amount, 0);
        
        if (totalSpend === 0) return { total: 0, items: [] };

        const items = spendBudgets.map((b, index) => {
            const cat = categories.find(c => c.id === b.category_id);
            // 해당 카테고리의 하위 카테고리 찾기
            const subs = allSubCategories.filter(s => s.category_id === b.category_id).map(s => s.name);
            
            // 실제 지출액 계산
            const actualSpend = (transactions || [])
                .filter(t => t.category_id === b.category_id)
                .reduce((sum, t) => sum + t.cost, 0);

            return {
                categoryId: b.category_id,
                name: cat ? (cat.display_name || cat.name) : 'Unknown',
                amount: b.budget_amount,
                actualSpend: actualSpend,
                percentage: (b.budget_amount / totalSpend) * 100,
                color: getCategoryColor(index),
                subCategories: subs
            };
        }).sort((a, b) => b.amount - a.amount); // 금액 큰 순서대로 정렬

        return { 
            total: totalSpend, 
            items 
        };
    });

    function getCategoryColor(index) {
        const colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD',
            '#D4A5A5', '#9B59B6', '#3498DB', '#E67E22', '#2ECC71',
            '#F1C40F', '#E74C3C', '#1ABC9C', '#9B59B6', '#34495E'
        ];
        return colors[index % colors.length];
    }

    onMount(async () => {
        await loadData();
    });

    // year, month가 바뀌면 거래 데이터 다시 로드 (필요한 경우)
    $effect(() => {
        if (year && month) {
            loadBudgets();
            if (!transactions || transactions.length === 0) {
                loadTransactions();
            }
        }
    });

    async function loadData() {
        loading = true;
        try {
            const [catData, budgetData, subCatData] = await Promise.all([
                getCategories(),
                getBudgets(year, month),
                getSubCategories()
            ]);
            
            categories = catData;
            budgets = budgetData;
            allSubCategories = subCatData;

            // transactions가 비어있으면 직접 로드
            if (year && month && (!transactions || transactions.length === 0)) {
                await loadTransactions();
            }
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

    async function loadTransactions() {
        try {
            const startDate = new Date(year, month - 1, 1);
            const endDate = new Date(year, month, 0);
            
            const formatDate = (date) => {
                const y = date.getFullYear();
                const m = String(date.getMonth() + 1).padStart(2, '0');
                const d = String(date.getDate()).padStart(2, '0');
                return `${y}-${m}-${d}`;
            };

            transactions = await getTransactions({
                start_date: formatDate(startDate),
                end_date: formatDate(endDate),
                limit: 10000
            });
        } catch (err) {
            console.error('Failed to load transactions:', err);
        }
    }

    function formatCurrency(value) {
        return new Intl.NumberFormat('ko-KR').format(value) + '원';
    }
</script>

<div class="budget-manager">
    <!-- 예산 분포 바 -->
    {#if budgetDistribution.total > 0}
        <div class="budget-distribution">
            <div class="distribution-header">
                <span class="label">예산별 분석</span>
                <div class="amount-info">
                    <span class="total-amount">{formatCurrency(budgetDistribution.total)}</span>
                </div>
            </div>
            <div class="progress-bar">
                {#each budgetDistribution.items as item}
                    <div 
                        class="progress-segment" 
                        style="width: {item.percentage}%; background-color: color-mix(in srgb, {item.color}, #e0e0e0 60%);"
                    >
                        {#if item.percentage > 5}
                            <span class="segment-label">{item.name} {item.percentage.toFixed(0)}%</span>
                        {/if}
                        
                        <!-- Custom Tooltip -->
                        <div class="custom-tooltip">
                            <div class="tooltip-header">
                                <span class="tooltip-name">{item.name}</span>
                                <span class="tooltip-amount">{formatCurrency(item.amount)}</span>
                            </div>
                            <div class="tooltip-percent">
                                전체의 {item.percentage.toFixed(1)}%
                            </div>
                            {#if item.subCategories && item.subCategories.length > 0}
                                <div class="tooltip-subs">
                                    <div class="subs-label">하위 항목:</div>
                                    <div class="subs-list">
                                        {item.subCategories.join(', ')}
                                    </div>
                                </div>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>

            <!-- 실제 지출 분포 바 -->
            <div class="progress-bar" style="margin-top: 8px;">
                {#each budgetDistribution.items as item}
                    <div 
                        class="progress-segment" 
                        style="width: {item.percentage}%; background-color: transparent; overflow: hidden; justify-content: flex-start;"
                        onclick={() => openTransactionDropdown(item.name, item.categoryId)}
                        role="button"
                        tabindex="0"
                        onkeydown={(e) => e.key === 'Enter' && openTransactionDropdown(item.name, item.categoryId)}
                    >
                        <div 
                            style="
                                width: {Math.min((item.actualSpend / item.amount) * 100, 100)}%; 
                                height: 100%; 
                                background-color: {item.color};
                            "
                        ></div>

                        {#if item.percentage > 5}
                            <span class="segment-label" style="position: absolute; left: 50%; transform: translateX(-50%); z-index: 1;">
                                {(item.actualSpend / budgetDistribution.total * 100).toFixed(1)}%
                            </span>
                        {/if}

                        <!-- Custom Tooltip -->
                        <div class="custom-tooltip">
                            <div class="tooltip-header">
                                <span class="tooltip-name">{item.name} (실제 지출)</span>
                                <span class="tooltip-amount">{formatCurrency(item.actualSpend)}</span>
                            </div>
                            <div class="tooltip-percent">
                                예산 대비 {(item.actualSpend / item.amount * 100).toFixed(1)}%
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    {/if}
</div>

<TransactionDropdown 
    bind:visible={showTransactionDropdown}
    mode="list"
    title={transactionDropdownTitle}
    transactions={transactionDropdownList}
/>

<style>
    .budget-manager {
        margin-top: 12px;
        border-top: 1px solid var(--border-color);
        padding-top: 4px;
    }

    /* Budget Distribution Bar */
    .budget-distribution {
        margin-bottom: 4px;
        padding: 12px;
    }

    .distribution-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .distribution-header .label {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .distribution-header .total-amount {
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .progress-bar {
        display: flex;
        height: 24px;
        background: #e0e0e0;
        border-radius: 4px;
        overflow: hidden;
    }

    .progress-segment {
        height: 100%;
        transition: width 0.3s ease;
    }

    .progress-segment:first-child {
        border-top-left-radius: 4px;
        border-bottom-left-radius: 4px;
    }

    .progress-segment:last-child {
        border-top-right-radius: 4px;
        border-bottom-right-radius: 4px;
    }

    /* Progress Bar & Tooltip Styles */
    .progress-bar {
        overflow: visible; /* 툴팁이 밖으로 나올 수 있게 */
        position: relative;
    }

    .progress-segment {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }

    .segment-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: rgba(0, 0, 0, 0.6);
        white-space: nowrap;
        pointer-events: none;
    }

    /* Custom Tooltip */
    .custom-tooltip {
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%) translateY(-8px);
        background: rgba(0, 0, 0, 0.85);
        color: white;
        padding: 12px;
        border-radius: 8px;
        font-size: 0.85rem;
        width: max-content;
        max-width: 250px;
        z-index: 100;
        opacity: 0;
        visibility: hidden;
        transition: all 0.2s ease;
        pointer-events: none;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    /* Tooltip Arrow */
    .custom-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border-width: 6px;
        border-style: solid;
        border-color: rgba(0, 0, 0, 0.85) transparent transparent transparent;
    }

    .progress-segment:hover .custom-tooltip {
        opacity: 1;
        visibility: visible;
        transform: translateX(-50%) translateY(-12px);
    }

    .tooltip-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        padding-bottom: 4px;
    }

    .tooltip-name {
        font-weight: 600;
        color: #fff;
    }

    .tooltip-amount {
        font-weight: 500;
        color: #4ECDC4;
    }

    .tooltip-percent {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 8px;
    }

    .tooltip-subs {
        font-size: 0.8rem;
    }

    .subs-label {
        color: rgba(255, 255, 255, 0.6);
        margin-bottom: 2px;
    }

    .subs-list {
        color: rgba(255, 255, 255, 0.9);
        line-height: 1.4;
        word-break: keep-all;
    }

    .amount-info {
        display: flex;
        align-items: center;
        gap: 8px;
    }

</style>