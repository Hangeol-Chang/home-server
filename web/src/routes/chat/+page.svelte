<script>
	import { sendChatMessage } from '$lib/api/chat.js';
	import { onMount, tick } from 'svelte';

	// ===== State =====
	/** @type {Array<{role: 'user'|'assistant', content: string, timestamp: string}>} */
	let messages = $state([]);
	let inputText = $state('');
	let isLoading = $state(false);
	let error = $state('');
	let messagesEndEl = $state(null);
	let inputEl = $state(null);

	// ===== Helpers =====
	function now() {
		return new Date().toISOString();
	}

	async function scrollToBottom() {
		await tick();
		if (messagesEndEl) {
			messagesEndEl.scrollIntoView({ behavior: 'smooth' });
		}
	}

	// ===== Actions =====
	async function handleSubmit() {
		const text = inputText.trim();
		if (!text || isLoading) return;

		// 사용자 메시지 추가
		messages = [...messages, { role: 'user', content: text, timestamp: now() }];
		inputText = '';
		isLoading = true;
		error = '';
		await scrollToBottom();

		try {
			// 히스토리는 마지막 메시지 제외한 전체 (방금 추가한 user 메시지 제외)
			const history = messages.slice(0, -1).map((m) => ({
				role: m.role,
				content: m.content
			}));

			const response = await sendChatMessage(text, history);

			messages = [
				...messages,
				{
					role: 'assistant',
					content: response.message,
					timestamp: response.timestamp ?? now()
				}
			];
		} catch (err) {
			error = err.message ?? '알 수 없는 오류가 발생했습니다.';
		} finally {
			isLoading = false;
			await scrollToBottom();
			await tick();
			inputEl?.focus();
		}
	}

	function handleKeydown(e) {
		// Shift+Enter: 줄바꿈, Enter: 전송
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	}

	function clearChat() {
		messages = [];
		error = '';
	}

	function formatTime(isoString) {
		if (!isoString) return '';
		return new Date(isoString).toLocaleTimeString('ko-KR', {
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	onMount(() => {
		// 처음 마운트 시 입력창 포커스
		inputEl?.focus();
	});
</script>

<div class="chat-page">
	<div class="chat-header">
		<h1>💬 Chat</h1>
		<p class="subtitle">Gemini AI와 대화하세요</p>
		{#if messages.length > 0}
			<button class="clear-btn" onclick={clearChat}>대화 초기화</button>
		{/if}
	</div>

	<!-- 메시지 영역 -->
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

			{#if isLoading}
				<div class="message assistant">
					<div class="bubble loading">
						<span class="dot"></span>
						<span class="dot"></span>
						<span class="dot"></span>
					</div>
				</div>
			{/if}
		{/if}

		{#if error}
			<div class="error-message">⚠️ {error}</div>
		{/if}

		<div bind:this={messagesEndEl}></div>
	</div>

	<!-- 입력 영역 -->
	<div class="chat-input-area">
		<textarea
			class="chat-input"
			placeholder="메시지를 입력하세요... (Enter: 전송, Shift+Enter: 줄바꿈)"
			bind:value={inputText}
			bind:this={inputEl}
			onkeydown={handleKeydown}
			disabled={isLoading}
			rows="1"
		></textarea>
		<button
			class="send-btn"
			onclick={handleSubmit}
			disabled={isLoading || !inputText.trim()}
			aria-label="전송"
		>
			{#if isLoading}
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

<style>
	.chat-page {
		display: flex;
		flex-direction: column;
		height: calc(100vh - 64px);
		max-width: 800px;
		margin: 0 auto;
		padding: 1rem;
		gap: 1rem;
	}

	/* Header */
	.chat-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-shrink: 0;
	}

	.chat-header h1 {
		font-size: 1.5rem;
		font-weight: 700;
		margin: 0;
	}

	.subtitle {
		margin: 0;
		color: var(--color-text-secondary, #888);
		font-size: 0.9rem;
	}

	.clear-btn {
		margin-left: auto;
		padding: 0.35rem 0.9rem;
		border: 1px solid var(--color-border, #ddd);
		border-radius: 8px;
		background: transparent;
		cursor: pointer;
		font-size: 0.85rem;
		color: var(--color-text-secondary, #888);
		transition: background 0.15s;
	}

	.clear-btn:hover {
		background: var(--color-hover, #f0f0f0);
	}

	/* Messages */
	.chat-messages {
		flex: 1;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		padding: 0.5rem 0;
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

	.empty-icon {
		font-size: 3rem;
	}

	.message {
		display: flex;
	}

	.message.user {
		justify-content: flex-end;
	}

	.message.assistant {
		justify-content: flex-start;
	}

	.bubble {
		max-width: 70%;
		padding: 0.75rem 1rem;
		border-radius: 16px;
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

	.content {
		margin: 0;
		white-space: pre-wrap;
		word-break: break-word;
		line-height: 1.5;
		font-size: 0.95rem;
	}

	.timestamp {
		display: block;
		font-size: 0.7rem;
		margin-top: 0.3rem;
		opacity: 0.65;
		text-align: right;
	}

	/* Loading dots */
	.bubble.loading {
		display: flex;
		gap: 0.35rem;
		align-items: center;
		padding: 0.9rem 1.1rem;
	}

	.dot {
		width: 8px;
		height: 8px;
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

	/* Error */
	.error-message {
		padding: 0.75rem 1rem;
		background: #fee2e2;
		color: #b91c1c;
		border-radius: 10px;
		font-size: 0.9rem;
	}

	/* Input area */
	.chat-input-area {
		display: flex;
		gap: 0.5rem;
		align-items: flex-end;
		flex-shrink: 0;
	}

	.chat-input {
		flex: 1;
		padding: 0.75rem 1rem;
		border: 1px solid var(--color-border, #ddd);
		border-radius: 12px;
		resize: none;
		font-size: 0.95rem;
		font-family: inherit;
		background: var(--color-surface, #fff);
		color: var(--color-text, #222);
		outline: none;
		max-height: 160px;
		overflow-y: auto;
		transition: border-color 0.15s;
		field-sizing: content;
	}

	.chat-input:focus {
		border-color: var(--color-primary, #6366f1);
	}

	.chat-input:disabled {
		opacity: 0.6;
	}

	.send-btn {
		width: 44px;
		height: 44px;
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

	.send-btn:hover:not(:disabled) {
		background: var(--color-primary-hover, #4f46e5);
	}

	.send-btn:disabled {
		opacity: 0.45;
		cursor: not-allowed;
	}

	.spinner {
		width: 18px;
		height: 18px;
		border: 2px solid rgba(255, 255, 255, 0.4);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>
