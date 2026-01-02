<script>
    import '$lib/styles/module.css';
    let { visible = $bindable(false), schedule = null } = $props();

    function close() {
        visible = false;
    }

    function handleKeydown(e) {
        if (e.key === 'Escape') close();
    }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if visible && schedule}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
    <div class="modal-overlay" onclick={close} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && close()}>
        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
        <div class="modal-container" onclick={(e) => e.stopPropagation()} role="document" tabindex="0" onkeydown={(e) => e.key === 'Enter' && e.stopPropagation()}>
            <div class="modal-header">
                <h3 class="modal-title">{schedule.title}</h3>
                <button class="icon-btn" onclick={close} aria-label="닫기">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="modal-body">
                <div class="info-row">
                    <span class="label">기간</span>
                    <span class="value">
                        {schedule.start_date} 
                        {#if schedule.start_date !== schedule.end_date}
                            ~ {schedule.end_date}
                        {/if}
                    </span>
                </div>
                {#if schedule.location}
                    <div class="info-row">
                        <span class="label">장소</span>
                        <span class="value">{schedule.location}</span>
                    </div>
                {/if}
                {#if schedule.description}
                    <div class="info-row">
                        <span class="label">설명</span>
                        <div class="value description">
                            {@html schedule.description.replace(/\n/g, '<br>')}
                        </div>
                    </div>
                {/if}
                <div class="info-row">
                    <span class="label">캘린더</span>
                    <span class="value badge" style="background-color: {schedule.color}">{schedule.type}</span>
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    .modal-container {
        max-width: 500px;
        padding: 0; /* Reset padding for this specific modal layout if needed, or adjust header/body */
        overflow: hidden; /* For rounded corners with header */
    }

    .modal-header {
        padding: 20px;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }

    .modal-title {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.4;
    }

    .modal-body {
        padding: 20px;
    }

    .info-row {
        margin-bottom: 16px;
    }

    .info-row:last-child {
        margin-bottom: 0;
    }

    .label {
        display: block;
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-bottom: 4px;
        font-weight: 500;
    }

    .value {
        font-size: 1rem;
        color: var(--text-primary);
    }

    .description {
        font-size: 0.95rem;
        line-height: 1.5;
        color: var(--text-primary);
        background: var(--bg-secondary);
        padding: 12px;
        border-radius: 8px;
    }

    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        color: white;
        font-size: 0.85rem;
        font-weight: 500;
    }
</style>
