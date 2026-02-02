<script>
    import { createWeeklySchedule, updateWeeklySchedule, deleteWeeklySchedule } from '$lib/api/schedule-manager.js';
    import { CHART_COLORS } from '$lib/constants.js';
    import '$lib/styles/module.css';

    let { 
        visible = $bindable(false), 
        schedule = null,  // null이면 생성 모드, 객체면 수정 모드
        initialDayOfWeek = 0,  // 0: 일요일, 6: 토요일
        initialStartTime = '09:00',
        onSuccess = () => {},
        onDelete = () => {}
    } = $props();

    let title = $state('');
    let description = $state('');
    let dayOfWeek = $state(0);
    let startTime = $state('09:00');
    let endTime = $state('10:00');
    let color = $state(CHART_COLORS[4]);
    let loading = $state(false);
    let error = $state(null);

    const weekDays = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
    const colorOptions = CHART_COLORS.slice(0, 12).map((c, i) => ({ value: c, name: `Color ${i + 1}` }));

    // 모달이 열릴 때 폼 초기화
    $effect(() => {
        if (visible) {
            if (schedule) {
                // 수정 모드
                title = schedule.title || '';
                description = schedule.description || '';
                dayOfWeek = schedule.day_of_week ?? 0;
                startTime = schedule.start_time || '09:00';
                endTime = schedule.end_time || '10:00';
                color = schedule.color || CHART_COLORS[4];
            } else {
                // 생성 모드
                title = '';
                description = '';
                dayOfWeek = initialDayOfWeek;
                startTime = initialStartTime;
                // 기본 1시간 뒤로 종료시간 설정
                const [h, m] = initialStartTime.split(':').map(Number);
                const endH = (h + 1) % 24;
                endTime = `${String(endH).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
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

        if (startTime >= endTime) {
            error = '종료 시간은 시작 시간보다 늦어야 합니다.';
            return;
        }

        loading = true;
        error = null;

        try {
            const scheduleData = {
                title: title.trim(),
                description: description.trim() || null,
                day_of_week: dayOfWeek,
                start_time: startTime,
                end_time: endTime,
                color: color
            };

            if (schedule) {
                await updateWeeklySchedule(schedule.id, scheduleData);
            } else {
                await createWeeklySchedule(scheduleData);
            }

            onSuccess();
            close();
        } catch (err) {
            console.error('Failed to save weekly schedule:', err);
            error = '저장에 실패했습니다.';
        } finally {
            loading = false;
        }
    }

    async function handleDelete() {
        if (!schedule) return;
        
        if (!confirm('이 일정을 삭제하시겠습니까?')) return;

        loading = true;
        error = null;

        try {
            await deleteWeeklySchedule(schedule.id);
            onDelete();
            close();
        } catch (err) {
            console.error('Failed to delete weekly schedule:', err);
            error = '삭제에 실패했습니다.';
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
                <h3 class="modal-title">{schedule ? '일정 수정' : '새 일정'}</h3>
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
                        placeholder="일정 제목"
                        disabled={loading}
                    />
                </div>

                <div class="form-group">
                    <label for="dayOfWeek">요일</label>
                    <select id="dayOfWeek" bind:value={dayOfWeek} disabled={loading}>
                        {#each weekDays as day, index}
                            <option value={index}>{day}</option>
                        {/each}
                    </select>
                </div>

                <div class="form-group">
                    <!-- svelte-ignore a11y_label_has_associated_control -->
                    <label>시간</label>
                    <div class="time-range-row">
                        <input 
                            type="time" 
                            id="startTime" 
                            bind:value={startTime}
                            disabled={loading}
                        />
                        <span class="time-separator">~</span>
                        <input 
                            type="time" 
                            id="endTime" 
                            bind:value={endTime}
                            disabled={loading}
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
                    {#if schedule}
                        <button type="button" class="btn-danger" onclick={handleDelete} disabled={loading}>
                            삭제
                        </button>
                    {/if}
                    <div class="action-spacer"></div>
                    <button type="button" class="btn-secondary" onclick={close} disabled={loading}>
                        취소
                    </button>
                    <button type="submit" class="btn-primary" disabled={loading}>
                        {#if loading}
                            저장 중...
                        {:else}
                            {schedule ? '수정' : '추가'}
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
    .form-group textarea,
    .form-group select {
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
    .form-group textarea:focus,
    .form-group select:focus {
        outline: none;
        border-color: var(--accent);
    }

    .form-group input:disabled,
    .form-group textarea:disabled,
    .form-group select:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .time-range-row {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .time-range-row input[type="time"] {
        flex: 1;
        min-width: 0;
        cursor: pointer;
    }

    .time-separator {
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
        align-items: center;
        gap: 12px;
        margin-top: 20px;
        padding-top: 8px;
        border-top: 1px solid var(--border-color);
    }

    .action-spacer {
        flex: 1;
    }

    .btn-danger {
        padding: 8px 16px;
        border: 1px solid var(--text-danger);
        border-radius: 6px;
        background: transparent;
        color: var(--text-danger);
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.2s;
    }

    .btn-danger:hover:not(:disabled) {
        background: var(--text-danger);
        color: white;
    }

    .btn-danger:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
</style>
