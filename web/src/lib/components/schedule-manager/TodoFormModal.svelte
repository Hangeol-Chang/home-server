<script>
    import { createTodo, updateTodo } from '$lib/api/schedule-manager.js';
    import { CHART_COLORS } from '$lib/constants.js';
    import '$lib/styles/module.css';

    let { 
        visible = $bindable(false), 
        todo = null,  // null이면 생성 모드, 객체면 수정 모드
        initialDate = null,  // 새 할일 생성 시 기본 날짜
        onSuccess = () => {} 
    } = $props();

    let title = $state('');
    let description = $state('');
    let startDate = $state('');
    let endDate = $state('');
    let color = $state(CHART_COLORS[4]); // 기본색: 민트
    let loading = $state(false);
    let error = $state(null);

    // CHART_COLORS에서 색상 옵션 생성
    const colorOptions = CHART_COLORS.slice(0, 12).map((c, i) => ({ value: c, name: `Color ${i + 1}` }));

    // 모달이 열릴 때 폼 초기화
    $effect(() => {
        if (visible) {
            if (todo) {
                // 수정 모드
                title = todo.title || '';
                description = todo.description || '';
                startDate = todo.start_date || '';
                endDate = todo.end_date || '';
                color = todo.color || CHART_COLORS[4];
            } else {
                // 생성 모드
                title = '';
                description = '';
                startDate = initialDate || new Date().toISOString().split('T')[0];
                endDate = initialDate || new Date().toISOString().split('T')[0];
                color = CHART_COLORS[4];
            }
            error = null;
        }
    });

    function close() {
        visible = false;
    }

    function handleKeydown(e) {
        if (e.key === 'Escape') close();
    }

    async function handleSubmit(e) {
        e.preventDefault();
        
        if (!title.trim()) {
            error = '제목을 입력해주세요.';
            return;
        }

        if (startDate > endDate) {
            error = '종료일은 시작일보다 같거나 이후여야 합니다.';
            return;
        }

        loading = true;
        error = null;

        try {
            const todoData = {
                title: title.trim(),
                description: description.trim() || null,
                start_date: startDate,
                end_date: endDate,
                color: color
            };

            if (todo) {
                await updateTodo(todo.id, todoData);
            } else {
                await createTodo(todoData);
            }

            onSuccess();
            close();
        } catch (err) {
            console.error('Failed to save todo:', err);
            error = '저장에 실패했습니다.';
        } finally {
            loading = false;
        }
    }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if visible}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
    <div class="modal-overlay" onclick={close} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && close()}>
        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
        <div class="modal-container" onclick={(e) => e.stopPropagation()} role="document" tabindex="0" onkeydown={(e) => e.key === 'Enter' && e.stopPropagation()}>
            <div class="modal-header">
                <h3 class="modal-title">{todo ? '할일 수정' : '새 할일'}</h3>
                <button class="icon-btn" onclick={close} aria-label="닫기">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <form class="modal-body" onsubmit={handleSubmit}>
                {#if error}
                    <div class="error-message">{error}</div>
                {/if}

                <div class="form-group">
                    <label for="title">제목 <span class="required">*</span></label>
                    <input 
                        type="text" 
                        id="title" 
                        bind:value={title} 
                        placeholder="할일 제목"
                        disabled={loading}
                    />
                </div>

                <div class="form-group">
                    <!-- svelte-ignore a11y_label_has_associated_control -->
                    <label>기간</label>
                    <div class="date-range-row">
                        <input 
                            type="date" 
                            id="startDate" 
                            bind:value={startDate}
                            disabled={loading}
                            onclick={(e) => e.currentTarget.showPicker()}
                        />
                        <span class="date-separator">~</span>
                        <input 
                            type="date" 
                            id="endDate" 
                            bind:value={endDate}
                            disabled={loading}
                            onclick={(e) => e.currentTarget.showPicker()}
                        />
                    </div>
                </div>

                <div class="form-group">
                    <!-- svelte-ignore a11y_label_has_associated_control -->
                    <label>색상</label>
                    <div class="color-picker">
                        {#each colorOptions as option}
                            <button 
                                type="button"
                                class="color-option" 
                                class:selected={color === option.value}
                                style="background-color: {option.value};"
                                onclick={() => color = option.value}
                                aria-label={option.name}
                                disabled={loading}
                            ></button>
                        {/each}
                    </div>
                </div>

                <div class="form-group">
                    <label for="description">설명</label>
                    <textarea 
                        id="description" 
                        bind:value={description} 
                        placeholder="상세 설명 (선택)"
                        rows="3"
                        disabled={loading}
                    ></textarea>
                </div>

                <div class="modal-actions">
                    <button type="button" class="btn-secondary" onclick={close} disabled={loading}>
                        취소
                    </button>
                    <button type="submit" class="btn-primary" disabled={loading}>
                        {#if loading}
                            저장 중...
                        {:else}
                            {todo ? '수정' : '추가'}
                        {/if}
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<style>
    .modal-container {
        max-width: 480px;
        padding: 0;
        overflow: hidden;
    }

    .modal-header {
        padding: 16px;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .modal-title {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 400;
        color: var(--text-primary);
    }

    .modal-body {
        padding: 16px;
    }

    .error-message {
        color: var(--text-danger);
        background: rgba(239, 68, 68, 0.1);
        padding: 16px;
        border-radius: 6px;
        margin-bottom: 16px;
        font-size: 0.9rem;
    }

    .form-group {
        margin-bottom: 16px;
    }

    .form-group label {
        display: block;
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin-bottom: 6px;
        font-weight: 300;
    }

    .required {
        color: var(--text-danger);
    }

    .form-group input,
    .form-group textarea {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        background: var(--bg-primary);
        color: var(--text-primary);
        font-size: 1rem;
        transition: border-color 0.2s;
    }

    .form-group input:focus,
    .form-group textarea:focus {
        outline: none;
        border-color: var(--accent);
    }

    .form-group input:disabled,
    .form-group textarea:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .date-range-row {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .date-range-row input[type="date"] {
        flex: 1;
        min-width: 0;
        cursor: pointer;
    }

    .date-separator {
        color: var(--text-tertiary);
        font-size: 0.9rem;
        flex-shrink: 0;
    }

    .color-picker {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }

    .color-option {
        width: 24px;
        height: 24px;
        border-radius: 4px;
        border: 2px solid transparent;
        cursor: pointer;
        transition: all 0.2s;
    }

    .color-option:hover {
        transform: scale(1.1);
    }

    .color-option.selected {
        border-color: var(--text-primary);
        box-shadow: 0 0 0 2px var(--bg-primary), 0 0 0 4px var(--text-primary);
    }

    .color-option:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .modal-actions {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        margin-top: 20px;
        padding-top: 8px;
        border-top: 1px solid var(--border-color);
    }
</style>
