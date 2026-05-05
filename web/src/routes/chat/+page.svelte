<script>
	import { sendChatMessage, agentStart, agentStop, agentStatus, agentClearLogs,
		listSessions, getSession, resumeSession, deleteSession } from '$lib/api/chat.js';
	import { onMount, onDestroy, tick } from 'svelte';

	// ===== Tab state =====
	let activeTab = $state('agent');

	// ===== Context size stepper =====
	const CTX_SIZES = [8192, 16384, 32768, 65536];
	let ctxIdx = $state(0);
	let ctxSize = $derived(CTX_SIZES[ctxIdx]);

	function ctxLabel(n) {
		return `${n / 1024}K`;
	}
	function ctxUp() { if (ctxIdx < CTX_SIZES.length - 1) ctxIdx++; }
	function ctxDown() { if (ctxIdx > 0) ctxIdx--; }

	// ===== Chat state =====
	/** @type {Array<{role: 'user'|'assistant', content: string, timestamp: string}>} */
	let messages = $state([]);
	let inputText = $state('');
	let chatLoading = $state(false);
	let chatError = $state('');
	let messagesEndEl = $state(null);
	let inputEl = $state(null);

	// ===== Agent state =====
	let agentObjective = $state('');
	let agentSystemPrompt = $state('');
	let agentModel = $state('');
	let agentData = $state(null); // AgentStatusResponse
	let agentPolling = $state(false);
	let agentError = $state('');
	let logContainerEl = $state(null);
	let showSystemPrompt = $state(false);
	let sidebarOpen = $state(true);

	let pollInterval = null;

	// ===== Session state =====
	let sessionList = $state([]);
	let selectedSessionId = $state(null);   // null = 새 에이전트 뷰
	let selectedSessionDetail = $state(null); // 선택된 세션의 전체 데이터
	let sessionError = $state('');

	// ===== Helpers =====
	function now() {
		return new Date().toISOString();
	}

	async function scrollToBottom() {
		await tick();
		messagesEndEl?.scrollIntoView({ behavior: 'smooth' });
	}

	function scrollLogsToBottom() {
		tick().then(() => {
			if (logContainerEl) logContainerEl.scrollTop = logContainerEl.scrollHeight;
		});
	}

	function formatTime(isoString) {
		if (!isoString) return '';
		return new Date(isoString).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
	}

	function statusColor(s) {
		if (s === 'running') return 'green';
		if (s === 'stopping') return 'orange';
		if (s === 'error') return 'red';
		return 'gray';
	}

	function logLevelClass(level) {
		if (level === 'ERROR') return 'log-error';
		if (level === 'WARN') return 'log-warn';
		if (level === 'TOOL') return 'log-tool';
		if (level === 'RESULT') return 'log-result';
		if (level === 'THINK') return 'log-think';
		if (level === 'MODEL') return 'log-model';
		if (level === 'SUMMARY') return 'log-summary';
		return 'log-info';
	}

	// ===== Chat actions =====
	async function handleSubmit() {
		const text = inputText.trim();
		if (!text || chatLoading) return;

		messages = [...messages, { role: 'user', content: text, timestamp: now() }];
		inputText = '';
		chatLoading = true;
		chatError = '';
		await scrollToBottom();

		try {
			const history = messages.slice(0, -1).map((m) => ({ role: m.role, content: m.content }));
			const response = await sendChatMessage(text, history, null, ctxSize);
			messages = [...messages, { role: 'assistant', content: response.message, timestamp: response.timestamp ?? now() }];
		} catch (err) {
			chatError = err.message ?? '알 수 없는 오류가 발생했습니다.';
		} finally {
			chatLoading = false;
			await scrollToBottom();
			await tick();
			inputEl?.focus();
		}
	}

	function handleKeydown(e) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	}

	function clearChat() {
		messages = [];
		chatError = '';
	}

	// ===== Agent actions =====
	async function fetchAgentStatus() {
		try {
			agentData = await agentStatus(50);
			agentError = '';
		} catch (err) {
			agentError = err.message;
		}
	}

	function startPolling() {
		if (pollInterval) return;
		agentPolling = true;
		pollInterval = setInterval(async () => {
			await fetchAgentStatus();
			scrollLogsToBottom();
			if (agentData?.status === 'idle' || agentData?.status === 'error') {
				stopPolling();
				fetchSessions();
			}
		}, 2000);
	}

	function stopPolling() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
		agentPolling = false;
	}

	async function handleAgentStart() {
		const obj = agentObjective.trim();
		if (!obj) return;
		agentError = '';
		try {
			agentData = await agentStart(
				obj,
				agentSystemPrompt.trim() || null,
				agentModel.trim() || null
			);
			startPolling();
			scrollLogsToBottom();
		} catch (err) {
			agentError = err.message;
		}
	}

	async function handleAgentStop() {
		try {
			agentData = await agentStop();
		} catch (err) {
			agentError = err.message;
		}
	}

	async function handleClearLogs() {
		try {
			await agentClearLogs();
			await fetchAgentStatus();
		} catch (err) {
			agentError = err.message;
		}
	}

	// ===== Session actions =====
	async function fetchSessions() {
		try {
			sessionList = await listSessions();
			sessionError = '';
		} catch (err) {
			sessionError = err.message;
		}
	}

	async function handleSelectSession(session) {
		selectedSessionId = session.id;
		try {
			selectedSessionDetail = await getSession(session.id);
			sessionError = '';
		} catch (err) {
			sessionError = err.message;
		}
	}

	function handleNewAgent() {
		selectedSessionId = null;
		selectedSessionDetail = null;
	}

	async function handleResumeSession(session) {
		try {
			agentData = await resumeSession(session.id);
			selectedSessionId = null;
			selectedSessionDetail = null;
			startPolling();
		} catch (err) {
			sessionError = err.message;
		}
	}

	async function handleDeleteSession(session) {
		try {
			await deleteSession(session.id);
			if (selectedSessionId === session.id) {
				selectedSessionId = null;
				selectedSessionDetail = null;
			}
			await fetchSessions();
		} catch (err) {
			sessionError = err.message;
		}
	}

	function sessionStatusColor(s) {
		if (s === 'running') return 'green';
		if (s === 'stopping') return 'orange';
		if (s === 'error') return 'red';
		return 'gray';
	}

	function formatDate(iso) {
		if (!iso) return '';
		return new Date(iso).toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
	}

	// ===== Lifecycle =====
	onMount(() => {
		const storedCtx = localStorage.getItem('chat_ctx_idx');
		if (storedCtx !== null) ctxIdx = Math.min(parseInt(storedCtx) || 0, CTX_SIZES.length - 1);

		const stored = localStorage.getItem('chat_history');
		if (stored) {
			try { messages = JSON.parse(stored); scrollToBottom(); } catch {}
		}
		inputEl?.focus();
		fetchAgentStatus();
		fetchSessions();
	});

	onDestroy(() => stopPolling());

	$effect(() => {
		localStorage.setItem('chat_history', JSON.stringify(messages));
	});

	$effect(() => {
		localStorage.setItem('chat_ctx_idx', ctxIdx.toString());
	});

	$effect(() => {
		if (agentData?.status === 'running' && !pollInterval) startPolling();
	});
</script>

<div class="page">
	<!-- Tab bar -->
	<div class="tab-bar">
		<button class="tab-btn" class:active={activeTab === 'chat'} onclick={() => (activeTab = 'chat')}>
			💬 채팅
		</button>
		<button class="tab-btn" class:active={activeTab === 'agent'} onclick={() => (activeTab = 'agent')}>
			🤖 에이전트
			{#if agentData?.status === 'running'}
				<span class="pulse-dot"></span>
			{/if}
		</button>
	</div>

	<!-- ===== CHAT TAB ===== -->
	{#if activeTab === 'chat'}
		<div class="chat-page">
			<div class="chat-header">
				<h1>💬 Chat</h1>
				<p class="subtitle">qwen3.6 AI와 대화하세요</p>
				<div class="ctx-stepper">
					<button class="ctx-btn" onclick={ctxDown} disabled={ctxIdx === 0}>‹</button>
					<span class="ctx-label">{ctxLabel(ctxSize)}</span>
					<button class="ctx-btn" onclick={ctxUp} disabled={ctxIdx === CTX_SIZES.length - 1}>›</button>
				</div>
				{#if messages.length > 0}
					<button class="clear-btn" onclick={clearChat}>대화 초기화</button>
				{/if}
			</div>

			<div class="chat-messages">
				{#if messages.length === 0}
					<div class="empty-state">
						<span class="empty-icon">🤖</span>
						<p>메시지를 입력해 대화를 시작하세요.</p>
					</div>
				{:else}
					{#each messages as msg (msg.timestamp + msg.role)}
						<div class="message {msg.role}">
							<div class="bubble">
								<p class="content">{msg.content}</p>
								<span class="timestamp">{formatTime(msg.timestamp)}</span>
							</div>
						</div>
					{/each}
					{#if chatLoading}
						<div class="message assistant">
							<div class="bubble loading">
								<span class="dot"></span><span class="dot"></span><span class="dot"></span>
							</div>
						</div>
					{/if}
				{/if}
				{#if chatError}
					<div class="error-message">⚠️ {chatError}</div>
				{/if}
				<div bind:this={messagesEndEl}></div>
			</div>

			<div class="chat-input-area">
				<textarea
					class="chat-input"
					placeholder="메시지를 입력하세요... (Enter: 전송, Shift+Enter: 줄바꿈)"
					bind:value={inputText}
					bind:this={inputEl}
					onkeydown={handleKeydown}
					disabled={chatLoading}
					rows="1"
				></textarea>
				<button class="send-btn" onclick={handleSubmit} disabled={chatLoading || !inputText.trim()}>
					{#if chatLoading}
						<span class="spinner"></span>
					{:else}
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="22" y1="2" x2="11" y2="13"></line>
							<polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
						</svg>
					{/if}
				</button>
			</div>
		</div>
	{/if}

	<!-- ===== AGENT TAB ===== -->
	{#if activeTab === 'agent'}
		<div class="agent-page">

			<!-- ── 왼쪽 세션 사이드바 ── -->
			<div class="session-sidebar" class:collapsed={!sidebarOpen}>
				<button
					class="new-agent-btn"
					class:active={selectedSessionId === null}
					onclick={handleNewAgent}
				>
					＋ 새 에이전트
				</button>

				{#if agentData?.status === 'running'}
					<div
						class="sidebar-item live"
						class:active={selectedSessionId === null}
						onclick={handleNewAgent}
					>
						<span class="pulse-dot"></span>
						<div class="sidebar-item-body">
							<div class="sidebar-obj">{agentData.current_objective?.slice(0, 45) || '실행 중...'}</div>
							<div class="sidebar-meta">iter {agentData.iteration} · 실행 중</div>
						</div>
					</div>
				{/if}

				<div class="sidebar-list">
					{#if sessionError}
						<div class="sidebar-error">⚠️ {sessionError}</div>
					{/if}
					{#if sessionList.length === 0}
						<div class="sidebar-empty">저장된 세션이 없습니다.</div>
					{:else}
						{#each sessionList as s}
							<div
								class="sidebar-item"
								class:active={selectedSessionId === s.id}
								onclick={() => handleSelectSession(s)}
							>
								<span class="sidebar-dot" style="background:{sessionStatusColor(s.status)}"></span>
								<div class="sidebar-item-body">
									<div class="sidebar-obj">{s.objective.slice(0, 45)}{s.objective.length > 45 ? '…' : ''}</div>
									<div class="sidebar-meta">{formatDate(s.started_at)} · iter {s.iteration}</div>
								</div>
								<button
									class="sidebar-del-btn"
									onclick={(e) => { e.stopPropagation(); handleDeleteSession(s); }}
									title="삭제"
								>×</button>
							</div>
						{/each}
					{/if}
				</div>
			</div>

			<!-- ── 오른쪽 메인 패널 ── -->
			<div class="agent-main">

				{#if selectedSessionId === null}
					<!-- 새 에이전트 / 실시간 뷰 -->
					<div class="main-header">
						<button class="hamburger-btn" onclick={() => (sidebarOpen = !sidebarOpen)} title={sidebarOpen ? '사이드바 닫기' : '사이드바 열기'}>
							<span></span><span></span><span></span>
						</button>
						<h1>🤖 에이전트</h1>
						<div class="ctx-stepper">
							<button class="ctx-btn" onclick={ctxDown} disabled={ctxIdx === 0}>‹</button>
							<span class="ctx-label">{ctxLabel(ctxSize)}</span>
							<button class="ctx-btn" onclick={ctxUp} disabled={ctxIdx === CTX_SIZES.length - 1}>›</button>
						</div>
					</div>

					{#if agentData?.status === 'running'}
						<div class="running-bar">
							<span class="status-badge" style="--badge-color: green">running</span>
							<span class="iter-badge">iter {agentData.iteration}</span>
							{#if agentPolling}<span class="polling-indicator">⟳</span>{/if}
							<span class="running-obj">{agentData.current_objective?.slice(0, 120)}</span>
							<button class="action-btn stop-btn" onclick={handleAgentStop}>■ 중지</button>
						</div>
					{:else}
						<div class="agent-controls">
							<textarea
								class="objective-input"
								placeholder="에이전트 목표를 입력하세요 (예: workspace 내 Python 파일 목록을 조사하고 요약해줘)"
								bind:value={agentObjective}
								rows="3"
							></textarea>

							<button class="toggle-btn" onclick={() => (showSystemPrompt = !showSystemPrompt)}>
								{showSystemPrompt ? '▲' : '▼'} 시스템 프롬프트
							</button>

							{#if showSystemPrompt}
								<textarea
									class="system-input"
									placeholder="시스템 프롬프트 (비워두면 기본값 사용)"
									bind:value={agentSystemPrompt}
									rows="3"
								></textarea>
							{/if}

							<div class="btn-row">
								<button class="action-btn start-btn" onclick={handleAgentStart} disabled={!agentObjective.trim()}>
									▶ 시작
								</button>
								<button class="action-btn refresh-btn" onclick={fetchAgentStatus}>⟳</button>
								<button class="action-btn clear-btn-sm" onclick={handleClearLogs}>🗑 로그 초기화</button>
							</div>

							{#if agentError}
								<div class="error-message">⚠️ {agentError}</div>
							{/if}
							{#if agentData?.error}
								<div class="error-message">🔴 {agentData.error}</div>
							{/if}
						</div>
					{/if}

					{#if agentData?.summary}
						<div class="summary-panel">
							<div class="summary-header">📋 결과 요약</div>
							<p class="summary-body">{agentData.summary}</p>
						</div>
					{/if}

					<div class="log-panel">
						<div class="log-header">
							<span>실시간 로그</span>
							{#if agentData}
								<span class="log-count">{agentData.total_logs}개 중 최근 {agentData.logs?.length ?? 0}개</span>
							{/if}
						</div>
						<div class="log-container" bind:this={logContainerEl}>
							{#if !agentData?.logs?.length}
								<div class="log-empty">에이전트를 시작하면 로그가 여기에 표시됩니다.</div>
							{:else}
								{#each agentData.logs as entry}
									<div class="log-entry {logLevelClass(entry.level)}">
										<span class="log-time">{formatTime(entry.timestamp)}</span>
										<span class="log-iter">#{entry.iteration}</span>
										<span class="log-level">{entry.level}</span>
										<span class="log-msg">{entry.message}</span>
									</div>
								{/each}
							{/if}
						</div>
					</div>

				{:else}
					<!-- 과거 세션 상세 뷰 -->
					{#if selectedSessionDetail}
						<div class="detail-header">
							<button class="hamburger-btn" onclick={() => (sidebarOpen = !sidebarOpen)} title={sidebarOpen ? '사이드바 닫기' : '사이드바 열기'}>
								<span></span><span></span><span></span>
							</button>
							<div class="detail-header-body">
								<div class="detail-objective">{selectedSessionDetail.objective}</div>
								<div class="detail-meta">
									{formatDate(selectedSessionDetail.started_at)}
									· iter {selectedSessionDetail.iteration}
									<span class="status-badge" style="--badge-color:{sessionStatusColor(selectedSessionDetail.status)}">{selectedSessionDetail.status}</span>
								</div>
							</div>
							<button
								class="action-btn start-btn"
								onclick={() => handleResumeSession(selectedSessionDetail)}
								disabled={agentData?.status === 'running'}
							>▶ 이어서 시작</button>
						</div>

						{#if selectedSessionDetail.summary}
							<div class="summary-panel">
								<div class="summary-header">📋 결과 요약</div>
								<p class="summary-body">{selectedSessionDetail.summary}</p>
							</div>
						{/if}

						<div class="log-panel">
							<div class="log-header">
								<span>세션 로그</span>
								<span class="log-count">{selectedSessionDetail.logs.length}개</span>
							</div>
							<div class="log-container">
								{#each selectedSessionDetail.logs as entry}
									<div class="log-entry {logLevelClass(entry.level)}">
										<span class="log-time">{formatTime(entry.timestamp)}</span>
										<span class="log-iter">#{entry.iteration}</span>
										<span class="log-level">{entry.level}</span>
										<span class="log-msg">{entry.message}</span>
									</div>
								{/each}
								{#if selectedSessionDetail.logs.length === 0}
									<div class="log-empty">로그가 없습니다.</div>
								{/if}
							</div>
						</div>
					{:else}
						<div class="log-empty" style="padding:2rem">세션을 불러오는 중...</div>
					{/if}
				{/if}

			</div>
		</div>
	{/if}
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		height: calc(100vh - 64px);
		max-width: 960px;
		margin: 0 auto;
		padding: 0.75rem 1rem 1rem;
		gap: 0;
		overflow: hidden;
	}

	/* Tab bar */
	.tab-bar {
		display: flex;
		gap: 0.25rem;
		border-bottom: 1px solid var(--color-border, #ddd);
		margin-bottom: 0.75rem;
		flex-shrink: 0;
	}

	.tab-btn {
		padding: 0.5rem 1.2rem;
		border: none;
		background: transparent;
		cursor: pointer;
		font-size: 0.9rem;
		color: var(--color-text-secondary, #888);
		border-bottom: 2px solid transparent;
		margin-bottom: -1px;
		transition: color 0.15s, border-color 0.15s;
		display: flex;
		align-items: center;
		gap: 0.4rem;
		position: relative;
	}

	.tab-btn.active {
		color: var(--color-primary, #6366f1);
		border-bottom-color: var(--color-primary, #6366f1);
		font-weight: 600;
	}

	.pulse-dot {
		width: 8px;
		height: 8px;
		background: #22c55e;
		border-radius: 50%;
		animation: pulse 1.5s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.5; transform: scale(0.85); }
	}

	/* ===== CHAT ===== */
	.chat-page {
		display: flex;
		flex-direction: column;
		flex: 1;
		gap: 0.75rem;
		min-height: 0;
	}

	.chat-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-shrink: 0;
	}

	.chat-header h1 { font-size: 1.4rem; font-weight: 700; margin: 0; }

	.subtitle { margin: 0; color: var(--color-text-secondary, #888); font-size: 0.85rem; }

	.ctx-stepper {
		display: flex;
		align-items: center;
		gap: 0.15rem;
		margin-left: auto;
		background: var(--color-surface, #f5f5f5);
		border: 1px solid var(--color-border, #ddd);
		border-radius: 8px;
		padding: 0.1rem 0.2rem;
	}

	.ctx-btn {
		width: 22px;
		height: 22px;
		border: none;
		background: transparent;
		cursor: pointer;
		font-size: 1rem;
		color: var(--color-text-secondary, #888);
		border-radius: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		line-height: 1;
	}

	.ctx-btn:hover:not(:disabled) { background: var(--color-hover, #e5e7eb); color: var(--color-text, #222); }
	.ctx-btn:disabled { opacity: 0.3; cursor: not-allowed; }

	.ctx-label {
		font-size: 0.78rem;
		font-weight: 600;
		color: var(--color-primary, #6366f1);
		min-width: 2.8rem;
		text-align: center;
		font-variant-numeric: tabular-nums;
	}

	.clear-btn {
		padding: 0.3rem 0.8rem;
		border: 1px solid var(--color-border, #ddd);
		border-radius: 8px;
		background: transparent;
		cursor: pointer;
		font-size: 0.8rem;
		color: var(--color-text-secondary, #888);
	}

	.clear-btn:hover { background: var(--color-hover, #f0f0f0); }

	.chat-messages {
		flex: 1;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		padding: 0.25rem 0;
		min-height: 0;
	}

	.empty-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		color: var(--color-text-secondary, #aaa);
	}

	.empty-icon { font-size: 2.5rem; }

	.message { display: flex; }
	.message.user { justify-content: flex-end; }
	.message.assistant { justify-content: flex-start; }

	.bubble {
		max-width: 72%;
		padding: 0.65rem 0.9rem;
		border-radius: 14px;
		position: relative;
	}

	.message.user .bubble {
		background: var(--color-primary, #6366f1);
		color: white;
		border-bottom-right-radius: 4px;
	}

	.message.assistant .bubble {
		background: var(--color-surface, #f5f5f5);
		color: var(--color-text, #222);
		border-bottom-left-radius: 4px;
	}

	.content { margin: 0; white-space: pre-wrap; word-break: break-word; line-height: 1.5; font-size: 0.9rem; }
	.timestamp { display: block; font-size: 0.68rem; margin-top: 0.25rem; opacity: 0.6; text-align: right; }

	.bubble.loading { display: flex; gap: 0.3rem; align-items: center; padding: 0.8rem 1rem; }

	.dot {
		width: 7px; height: 7px;
		border-radius: 50%;
		background: var(--color-text-secondary, #999);
		animation: bounce 1.2s infinite;
	}

	.dot:nth-child(2) { animation-delay: 0.2s; }
	.dot:nth-child(3) { animation-delay: 0.4s; }

	@keyframes bounce {
		0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
		40% { transform: scale(1.2); opacity: 1; }
	}

	.error-message {
		padding: 0.6rem 0.9rem;
		background: #fee2e2;
		color: #b91c1c;
		border-radius: 8px;
		font-size: 0.85rem;
	}

	.chat-input-area { display: flex; gap: 0.5rem; align-items: flex-end; flex-shrink: 0; }

	.chat-input {
		flex: 1;
		padding: 0.7rem 0.9rem;
		border: 1px solid var(--color-border, #ddd);
		border-radius: 12px;
		resize: none;
		font-size: 0.9rem;
		font-family: inherit;
		background: var(--color-surface, #fff);
		color: var(--color-text, #222);
		outline: none;
		max-height: 140px;
		overflow-y: auto;
		transition: border-color 0.15s;
		field-sizing: content;
	}

	.chat-input:focus { border-color: var(--color-primary, #6366f1); }
	.chat-input:disabled { opacity: 0.6; }

	.send-btn {
		width: 42px; height: 42px;
		border-radius: 12px;
		border: none;
		background: var(--color-primary, #6366f1);
		color: white;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: background 0.15s, opacity 0.15s;
		flex-shrink: 0;
	}

	.send-btn:hover:not(:disabled) { background: var(--color-primary-hover, #4f46e5); }
	.send-btn:disabled { opacity: 0.45; cursor: not-allowed; }

	.spinner {
		width: 16px; height: 16px;
		border: 2px solid rgba(255,255,255,0.4);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}

	@keyframes spin { to { transform: rotate(360deg); } }

	/* ===== AGENT — 2-column layout ===== */
	.agent-page {
		display: flex;
		flex: 1;
		min-height: 0;
		overflow: hidden;
		gap: 0;
		margin: 0 -1rem -1rem;
		border-top: 1px solid var(--color-border, #ddd);
	}

	/* ── 왼쪽 사이드바 ── */
	.session-sidebar {
		width: 240px;
		flex-shrink: 0;
		display: flex;
		flex-direction: column;
		border-right: 1px solid var(--color-border, #ddd);
		background: var(--color-surface, #f9f9f9);
		overflow: hidden;
		transition: width 0.2s ease, border-width 0.2s ease;
	}

	.session-sidebar.collapsed {
		width: 0;
		border-right-width: 0;
	}

	.new-agent-btn {
		margin: 0.6rem;
		padding: 0.5rem 0.75rem;
		border-radius: 8px;
		border: 1.5px dashed var(--color-border, #ccc);
		background: transparent;
		cursor: pointer;
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--color-primary, #6366f1);
		text-align: left;
		transition: background 0.15s, border-color 0.15s;
		flex-shrink: 0;
	}

	.new-agent-btn:hover, .new-agent-btn.active {
		background: #eef2ff;
		border-color: var(--color-primary, #6366f1);
	}

	.sidebar-list {
		flex: 1;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
	}

	.sidebar-item {
		display: flex;
		align-items: flex-start;
		gap: 0.5rem;
		padding: 0.55rem 0.7rem;
		cursor: pointer;
		border-bottom: 1px solid var(--color-border, #eee);
		position: relative;
		transition: background 0.12s;
	}

	.sidebar-item:hover { background: var(--color-hover, rgba(0,0,0,0.04)); }

	.sidebar-item.active {
		background: #eef2ff;
		border-left: 3px solid var(--color-primary, #6366f1);
	}

	.sidebar-item.live { border-left: 3px solid #22c55e; background: #f0fdf4; }
	.sidebar-item.live.active { background: #dcfce7; }

	.sidebar-dot {
		width: 7px; height: 7px;
		border-radius: 50%;
		flex-shrink: 0;
		margin-top: 0.3rem;
	}

	.sidebar-item-body { flex: 1; min-width: 0; }

	.sidebar-obj {
		font-size: 0.82rem;
		font-weight: 500;
		color: var(--color-text, #222);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.sidebar-meta {
		font-size: 0.72rem;
		color: var(--color-text-secondary, #888);
		margin-top: 0.1rem;
	}

	.sidebar-del-btn {
		flex-shrink: 0;
		width: 18px; height: 18px;
		border: none;
		background: transparent;
		color: var(--color-text-secondary, #aaa);
		cursor: pointer;
		font-size: 1rem;
		line-height: 1;
		border-radius: 4px;
		opacity: 0;
		transition: opacity 0.15s, color 0.15s;
		padding: 0;
		display: flex; align-items: center; justify-content: center;
	}

	.sidebar-item:hover .sidebar-del-btn { opacity: 1; }
	.sidebar-del-btn:hover { color: #ef4444; background: #fee2e2; }

	.sidebar-empty {
		padding: 1rem 0.75rem;
		font-size: 0.82rem;
		color: var(--color-text-secondary, #aaa);
		text-align: center;
	}

	.sidebar-error {
		padding: 0.5rem 0.75rem;
		font-size: 0.78rem;
		color: #b91c1c;
	}

	/* ── 오른쪽 메인 ── */
	.agent-main {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
		min-height: 0;
		padding: 0.75rem 1rem;
		gap: 0.65rem;
		overflow: hidden;
	}

	.main-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-shrink: 0;
	}

	.main-header h1 { font-size: 1.3rem; font-weight: 700; margin: 0; }

	/* 햄버거 버튼 */
	.hamburger-btn {
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 4px;
		width: 32px;
		height: 32px;
		padding: 5px;
		border: none;
		background: transparent;
		cursor: pointer;
		border-radius: 6px;
		flex-shrink: 0;
	}

	.hamburger-btn span {
		display: block;
		height: 2px;
		background: var(--color-text-secondary, #666);
		border-radius: 2px;
		transition: background 0.15s;
	}

	.hamburger-btn:hover { background: var(--color-hover, #f0f0f0); }
	.hamburger-btn:hover span { background: var(--color-text, #222); }

	.running-bar {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 0.5rem 0.75rem;
		background: #f0fdf4;
		border: 1px solid #bbf7d0;
		border-radius: 10px;
		font-size: 0.85rem;
		flex-shrink: 0;
		flex-wrap: wrap;
	}

	.running-obj {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--color-text-secondary, #555);
		font-size: 0.82rem;
	}

	.status-badge {
		padding: 0.15rem 0.6rem;
		border-radius: 99px;
		font-weight: 700;
		font-size: 0.72rem;
		background: color-mix(in srgb, var(--badge-color) 15%, transparent);
		color: var(--badge-color);
		border: 1px solid color-mix(in srgb, var(--badge-color) 40%, transparent);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		flex-shrink: 0;
	}

	.iter-badge {
		padding: 0.15rem 0.5rem;
		background: #e0e7ff;
		color: #4338ca;
		border-radius: 6px;
		font-size: 0.78rem;
		font-weight: 600;
		flex-shrink: 0;
	}

	.polling-indicator { color: #22c55e; font-size: 0.82rem; flex-shrink: 0; animation: pulse 1.5s infinite; }

	.agent-controls { display: flex; flex-direction: column; gap: 0.45rem; flex-shrink: 0; }

	.objective-input, .system-input {
		width: 100%;
		padding: 0.65rem 0.85rem;
		border: 1px solid var(--color-border, #ddd);
		border-radius: 10px;
		resize: vertical;
		font-size: 0.88rem;
		font-family: inherit;
		background: var(--color-surface, #fff);
		color: var(--color-text, #222);
		outline: none;
		transition: border-color 0.15s;
		box-sizing: border-box;
	}

	.objective-input:focus, .system-input:focus { border-color: var(--color-primary, #6366f1); }

	.toggle-btn {
		background: none;
		border: none;
		color: var(--color-text-secondary, #888);
		font-size: 0.82rem;
		cursor: pointer;
		padding: 0.1rem 0;
		text-align: left;
	}

	.toggle-btn:hover { color: var(--color-text, #222); }

	.btn-row { display: flex; gap: 0.5rem; flex-wrap: wrap; }

	.action-btn {
		padding: 0.45rem 1rem;
		border-radius: 8px;
		border: none;
		cursor: pointer;
		font-size: 0.85rem;
		font-weight: 600;
		transition: opacity 0.15s, background 0.15s;
	}

	.action-btn:disabled { opacity: 0.4; cursor: not-allowed; }
	.start-btn { background: #22c55e; color: white; }
	.start-btn:hover:not(:disabled) { background: #16a34a; }
	.stop-btn { background: #ef4444; color: white; }
	.stop-btn:hover:not(:disabled) { background: #dc2626; }
	.refresh-btn { background: var(--color-surface, #f0f0f0); color: var(--color-text, #333); border: 1px solid var(--color-border, #ddd); }
	.refresh-btn:hover { background: var(--color-hover, #e5e7eb); }
	.clear-btn-sm { background: var(--color-surface, #f0f0f0); color: var(--color-text-secondary, #666); border: 1px solid var(--color-border, #ddd); }
	.clear-btn-sm:hover { background: #fee2e2; color: #b91c1c; }

	/* 세션 상세 헤더 */
	.detail-header {
		flex-shrink: 0;
		display: flex;
		flex-direction: row;
		align-items: flex-start;
		gap: 0.6rem;
		padding-bottom: 0.65rem;
		border-bottom: 1px solid var(--color-border, #eee);
	}

	.detail-header-body {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.detail-objective {
		font-size: 1rem;
		font-weight: 700;
		color: var(--color-text, #111);
		line-height: 1.4;
	}

	.detail-meta {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8rem;
		color: var(--color-text-secondary, #888);
	}

	/* 요약 패널 */
	.summary-panel {
		flex-shrink: 0;
		max-height: 180px;
		overflow-y: auto;
		border: 1px solid #a5b4fc;
		border-radius: 10px;
		background: #eef2ff;
		padding: 0.6rem 0.9rem;
	}

	.summary-header {
		font-size: 0.8rem;
		font-weight: 700;
		color: #4f46e5;
		margin-bottom: 0.3rem;
	}

	.summary-body {
		font-size: 0.86rem;
		line-height: 1.6;
		color: #1e1b4b;
		white-space: pre-wrap;
		margin: 0;
	}

	/* 로그 패널 */
	.log-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		border: 1px solid var(--color-border, #ddd);
		border-radius: 10px;
		overflow: hidden;
		min-height: 0;
	}

	.log-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.4rem 0.75rem;
		background: var(--color-surface, #f5f5f5);
		border-bottom: 1px solid var(--color-border, #ddd);
		font-size: 0.82rem;
		font-weight: 600;
		flex-shrink: 0;
	}

	.log-count { color: var(--color-text-secondary, #888); font-weight: 400; }

	.log-container {
		flex: 1;
		overflow-y: auto;
		padding: 0.4rem 0;
		font-family: 'Menlo', 'Consolas', monospace;
		font-size: 0.78rem;
		line-height: 1.45;
	}

	.log-empty { padding: 1rem; color: var(--color-text-secondary, #aaa); text-align: center; font-family: inherit; }

	.log-entry {
		display: flex;
		gap: 0.5rem;
		padding: 0.15rem 0.75rem;
		border-bottom: 1px solid transparent;
		align-items: baseline;
	}

	.log-entry:hover { background: var(--color-hover, rgba(0,0,0,0.03)); }

	.log-time { color: #94a3b8; flex-shrink: 0; font-size: 0.72rem; }
	.log-iter { color: #94a3b8; flex-shrink: 0; min-width: 2rem; }

	.log-level {
		flex-shrink: 0;
		min-width: 4.5rem;
		font-weight: 700;
		font-size: 0.72rem;
		padding: 0.05rem 0.35rem;
		border-radius: 4px;
		text-align: center;
	}

	.log-msg { color: var(--color-text, #222); word-break: break-all; }

	.log-info .log-level { background: #f1f5f9; color: #475569; }
	.log-model .log-level { background: #ede9fe; color: #7c3aed; }
	.log-tool .log-level { background: #fef3c7; color: #d97706; }
	.log-result .log-level { background: #dcfce7; color: #15803d; }
	.log-think .log-level { background: #e0f2fe; color: #0369a1; }
	.log-warn .log-level { background: #fef9c3; color: #a16207; }
	.log-error .log-level { background: #fee2e2; color: #b91c1c; }

	.log-model .log-msg { color: #7c3aed; }
	.log-tool .log-msg { color: #d97706; }
	.log-result .log-msg { color: #15803d; }
	.log-think .log-msg { color: #0369a1; font-style: italic; }
	.log-error .log-msg { color: #b91c1c; }
	.log-summary .log-level { background: #e0e7ff; color: #4338ca; }
	.log-summary .log-msg { color: #4338ca; font-weight: 600; }
</style>
