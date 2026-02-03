<script>
    import { deleteTodo, toggleTodoCompletion } from '$lib/api/schedule-manager.js';
    import '$lib/styles/module.css';

    let { 
        visible = $bindable(false), 
        date = null,  // 선택된 날짜 (YYYY-MM-DD)
        schedules = [],  // 해당 날짜의 구글 캘린더 일정
        todos = [],  // 해당 날짜의 할일
        onAddTodo = () => {},
        onEditTodo = (todo) => {},
        onTodoChange = () => {}  // Todo 변경 후 호출될 콜백
    } = $props();

    let loading = $state({});  // todoId -> loading state

    function close() {
        visible = false;
    }

    function handleKeydown(e) {
        if (e.key === 'Escape') close();
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        const weekDays = ['일', '월', '화', '수', '목', '금', '토'];
        return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일 (${weekDays[d.getDay()]})`;
    }

    async function handleToggleTodo(todo) {
        loading = { ...loading, [todo.id]: true };
        try {
            await toggleTodoCompletion(todo.id);
            onTodoChange();
        } catch (err) {
            console.error('Failed to toggle todo:', err);
        } finally {
            loading = { ...loading, [todo.id]: false };
        }
    }

    async function handleDeleteTodo(todo) {
        if (!confirm(`"${todo.title}" 할일을 삭제하시겠습니까?`)) return;
        
        loading = { ...loading, [todo.id]: true };
        try {
            await deleteTodo(todo.id);
            onTodoChange();
        } catch (err) {
            console.error('Failed to delete todo:', err);
        } finally {
            loading = { ...loading, [todo.id]: false };
        }
    }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if visible && date}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
    <div class="modal-overlay" onclick={close} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && close()}>
        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
        <div class="modal-container" onclick={(e) => e.stopPropagation()} role="document" tabindex="0" onkeydown={(e) => e.key === 'Enter' && e.stopPropagation()}>
            <div class="modal-header">
                <h3 class="modal-title">{formatDate(date)}</h3>
                <button class="icon-btn" onclick={close} aria-label="닫기">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="modal-body">
                <!-- 구글 캘린더 일정 -->
                {#if schedules.length > 0}
                    <div style="margin-bottom: 24px;">
                        <div class="section-header">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                <line x1="3" y1="10" x2="21" y2="10"></line>
                            </svg>
                            <span>일정</span>
                        </div>
                        <ul class="item-list">
                            {#each schedules as schedule}
                                <li class="item schedule-item">
                                    <span class="color-dot" style="background-color: {schedule.color || '#4285F4'};"></span>
                                    <span class="item-title">{schedule.title}</span>
                                    {#if schedule.start_date !== schedule.end_date}
                                        <span class="item-date">{schedule.start_date} ~ {schedule.end_date}</span>
                                    {/if}
                                </li>
                            {/each}
                        </ul>
                    </div>
                {/if}

                <!-- 할일 -->
                <div style="margin-bottom: 24px;">
                    <div class="section-header">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 11l3 3L22 4"></path>
                            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                        </svg>
                        <span>할일</span>
                        <button class="add-btn-small" onclick={() => onAddTodo(date)} aria-label="할일 추가">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="12" y1="5" x2="12" y2="19"></line>
                                <line x1="5" y1="12" x2="19" y2="12"></line>
                            </svg>
                        </button>
                    </div>
                    {#if todos.length > 0}
                        <ul class="item-list">
                            {#each todos as todo}
                                <li class="item todo-item" class:completed={todo.is_completed}>
                                    <button 
                                        class="checkbox" 
                                        class:checked={todo.is_completed}
                                        onclick={() => handleToggleTodo(todo)}
                                        disabled={loading[todo.id]}
                                        aria-label={todo.is_completed ? '완료 취소' : '완료 처리'}
                                    >
                                        {#if todo.is_completed}
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                                                <polyline points="20 6 9 17 4 12"></polyline>
                                            </svg>
                                        {/if}
                                    </button>
                                    <span class="color-dot" style="background-color: {todo.color || '#10B981'};"></span>
                                    <span class="item-title" class:strikethrough={todo.is_completed}>{todo.title}</span>
                                    {#if todo.start_date !== todo.end_date}
                                        <span class="item-date">{todo.start_date} ~ {todo.end_date}</span>
                                    {/if}
                                    <div class="item-actions">
                                        <button class="action-btn" onclick={() => onEditTodo(todo)} aria-label="수정" disabled={loading[todo.id]}>
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                            </svg>
                                        </button>
                                        <button class="action-btn danger" onclick={() => handleDeleteTodo(todo)} aria-label="삭제" disabled={loading[todo.id]}>
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <polyline points="3 6 5 6 21 6"></polyline>
                                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                            </svg>
                                        </button>
                                    </div>
                                </li>
                            {/each}
                        </ul>
                    {:else}
                        <p class="empty-message">등록된 할일이 없습니다.</p>
                    {/if}
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    .modal-container {
        max-width: 520px;
        padding: 0;
        overflow: hidden;
        max-height: 80vh;
        display: flex;
        flex-direction: column;
    }

    .modal-header {
        padding: 20px;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-shrink: 0;
    }

    .modal-title {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 400;
        color: var(--text-primary);
    }

    .modal-body {
        padding: 20px;
        overflow-y: auto;
        flex: 1;
    }
    
    .section-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9rem;
        font-weight: 400;
        color: var(--text-secondary);
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-color);
    }

    .add-btn-small {
        margin-left: auto;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        cursor: pointer;
        color: var(--text-secondary);
        transition: all 0.2s;
    }

    .add-btn-small:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .item-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        background: var(--bg-secondary);
        border-radius: 8px;
        margin-bottom: 8px;
    }

    .item:last-child {
        margin-bottom: 0;
    }

    .color-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .item-title {
        flex: 1;
        font-size: 0.95rem;
        color: var(--text-primary);
    }

    .item-title.strikethrough {
        text-decoration: line-through;
        color: var(--text-tertiary);
    }

    .item-date {
        font-size: 0.8rem;
        color: var(--text-tertiary);
    }

    .todo-item.completed {
        opacity: 0.7;
    }

    .checkbox {
        width: 20px;
        height: 20px;
        border: 2px solid var(--border-color);
        border-radius: 4px;
        background: var(--bg-primary);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        transition: all 0.2s;
    }

    .checkbox:hover:not(:disabled) {
        border-color: var(--accent);
    }

    .checkbox.checked {
        background: var(--accent);
        border-color: var(--accent);
        color: white;
    }

    .checkbox:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .item-actions {
        display: flex;
        gap: 4px;
        opacity: 0;
        transition: opacity 0.2s;
    }

    .item:hover .item-actions {
        opacity: 1;
    }

    .action-btn {
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        cursor: pointer;
        color: var(--text-secondary);
        transition: all 0.2s;
    }

    .action-btn:hover:not(:disabled) {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .action-btn.danger:hover:not(:disabled) {
        background: rgba(239, 68, 68, 0.1);
        border-color: var(--text-danger);
        color: var(--text-danger);
    }

    .action-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .empty-message {
        text-align: center;
        color: var(--text-tertiary);
        font-size: 0.9rem;
        padding: 20px;
    }
</style>
