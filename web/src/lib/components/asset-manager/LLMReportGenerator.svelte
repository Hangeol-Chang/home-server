<script>
	import { generateMonthlyReport, generateWeeklyReport } from '$lib/api/test.js';

	// 모드: 'monthly' | 'weekly'
	let mode = $state('monthly');

	// ── 월간 상태 ──
	const today = new Date();
	let reportYear  = $state(today.getFullYear());
	let reportMonth = $state(today.getMonth() + 1);

	function changeMonth(delta) {
		let m = reportMonth + delta;
		if (m > 12) { m = 1; reportYear += 1; }
		else if (m < 1) { m = 12; reportYear -= 1; }
		reportMonth = m;
		clearResult();
	}

	// ── 주간 상태 ──
	let weekOffset = $state(0); // 0 = 이번 주, -1 = 지난 주, …

	function getWeekRange(offsetWeeks = 0) {
		const d = new Date();
		d.setDate(d.getDate() + offsetWeeks * 7);
		const day  = d.getDay();
		const diff = day === 0 ? -6 : 1 - day; // 월요일 기준
		const mon  = new Date(d);
		mon.setDate(d.getDate() + diff);
		const sun  = new Date(mon);
		sun.setDate(mon.getDate() + 6);
		return { start: mon, end: sun };
	}

	const weekRange = $derived(getWeekRange(weekOffset));

	function fmt(d) {
		return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
	}

	function weekLabel(range) {
		const s = range.start, e = range.end;
		return `${s.getMonth() + 1}/${s.getDate()} ~ ${e.getMonth() + 1}/${e.getDate()}`;
	}

	function changeWeek(delta) {
		weekOffset += delta;
		clearResult();
	}

	// ── 리포트 결과 ──
	let loading = $state(false);
	let reportContent = $state('');
	let reportError   = $state('');

	function clearResult() {
		reportContent = '';
		reportError   = '';
	}

	function setMode(m) {
		mode = m;
		clearResult();
	}

	async function generate() {
		loading = true;
		clearResult();
		try {
			let result;
			if (mode === 'monthly') {
				result = await generateMonthlyReport(reportYear, reportMonth, true);
			} else {
				result = await generateWeeklyReport(fmt(weekRange.start), fmt(weekRange.end), true);
			}
			reportContent = result.content || '';
		} catch (e) {
			reportError = e.message || '리포트 생성에 실패했습니다.';
		} finally {
			loading = false;
		}
	}

	// 마크다운 → 간단한 HTML 변환 (Discord 스타일)
	function renderMarkdown(text) {
		return text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			// **bold**
			.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
			// # heading
			.replace(/^### (.+)$/gm, '<h4>$1</h4>')
			.replace(/^## (.+)$/gm,  '<h3>$1</h3>')
			.replace(/^# (.+)$/gm,   '<h2>$1</h2>')
			// 줄바꿈
			.replace(/\n/g, '<br>');
	}
</script>

<div class="llm-report">
	<!-- 헤더 -->
	<div class="report-header">
		<h3 class="report-title">🤖 AI 재무 리포트</h3>

		<!-- 모드 탭 -->
		<div class="mode-tabs">
			<button
				class="mode-tab"
				class:active={mode === 'weekly'}
				onclick={() => setMode('weekly')}
			>
				📅 주간
			</button>
			<button
				class="mode-tab"
				class:active={mode === 'monthly'}
				onclick={() => setMode('monthly')}
			>
				📊 월간
			</button>
		</div>
	</div>

	<!-- 기간 네비게이션 + 생성 버튼 -->
	<div class="period-row">
		{#if mode === 'monthly'}
			<button class="nav-btn" onclick={() => changeMonth(-1)} aria-label="이전 달">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="15 18 9 12 15 6"/>
				</svg>
			</button>
			<span class="period-label">{reportYear}년 {reportMonth}월</span>
			<button class="nav-btn" onclick={() => changeMonth(1)} aria-label="다음 달">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="9 18 15 12 9 6"/>
				</svg>
			</button>
		{:else}
			<button class="nav-btn" onclick={() => changeWeek(-1)} aria-label="이전 주">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="15 18 9 12 15 6"/>
				</svg>
			</button>
			<span class="period-label">{weekLabel(weekRange)}</span>
			<button class="nav-btn" onclick={() => changeWeek(1)} aria-label="다음 주">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="9 18 15 12 9 6"/>
				</svg>
			</button>
		{/if}

		<button
			class="generate-btn"
			onclick={generate}
			disabled={loading}
		>
			{#if loading}
				<span class="spinner"></span>
				생성 중…
			{:else}
				✨ 리포트 생성
			{/if}
		</button>
	</div>

	<!-- 결과 영역 -->
	{#if loading}
		<div class="result-loading">
			<div class="loading-spinner"></div>
			<p>AI가 리포트를 작성 중입니다…<br><small>모델 로딩 시 최대 2분 소요될 수 있습니다.</small></p>
		</div>
	{:else if reportError}
		<div class="result-error">
			<p>⚠️ {reportError}</p>
		</div>
	{:else if reportContent}
		<div class="result-content">
			<div class="report-text">
				<!-- eslint-disable-next-line svelte/no-at-html-tags -->
				{@html renderMarkdown(reportContent)}
			</div>
			<p class="discord-hint">💬 Discord에도 동시 전송되었습니다.</p>
		</div>
	{/if}
</div>

<style>
	.llm-report {
		border: 1px solid var(--border-color);
		border-radius: 8px;
		padding: 20px 24px;
		margin-bottom: 32px;
		background-color: var(--bg-primary);
	}

	.report-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 16px;
		gap: 12px;
		flex-wrap: wrap;
	}

	.report-title {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-primary);
	}

	/* 모드 탭 */
	.mode-tabs {
		display: flex;
		gap: 4px;
		background: var(--bg-secondary);
		border-radius: 6px;
		padding: 3px;
	}

	.mode-tab {
		padding: 5px 14px;
		border: none;
		border-radius: 4px;
		background: transparent;
		color: var(--text-secondary);
		font-size: 0.85rem;
		cursor: pointer;
		transition: all 0.15s;
	}

	.mode-tab.active {
		background: var(--bg-primary);
		color: var(--text-primary);
		font-weight: 600;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
	}

	/* 기간 네비게이션 */
	.period-row {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-wrap: wrap;
	}

	.nav-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 30px;
		height: 30px;
		border: 1px solid var(--border-color);
		border-radius: 6px;
		background: var(--bg-secondary);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all 0.15s;
	}

	.nav-btn:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
	}

	.period-label {
		font-size: 0.95rem;
		font-weight: 600;
		color: var(--text-primary);
		min-width: 140px;
		text-align: center;
	}

	.generate-btn {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-left: auto;
		padding: 7px 18px;
		background: var(--accent-color, #6366f1);
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 0.88rem;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.15s;
	}

	.generate-btn:hover:not(:disabled) {
		opacity: 0.85;
	}

	.generate-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.spinner {
		display: inline-block;
		width: 14px;
		height: 14px;
		border: 2px solid rgba(255, 255, 255, 0.4);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* 결과 */
	.result-loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 32px 16px;
		gap: 12px;
		color: var(--text-secondary);
		text-align: center;
	}

	.loading-spinner {
		width: 36px;
		height: 36px;
		border: 3px solid var(--border-color);
		border-top-color: var(--accent-color, #6366f1);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.result-loading p {
		margin: 0;
		font-size: 0.9rem;
	}

	.result-loading small {
		color: var(--text-tertiary, var(--text-secondary));
		font-size: 0.8rem;
	}

	.result-error {
		margin-top: 16px;
		padding: 12px 16px;
		background: rgba(244, 67, 54, 0.08);
		border: 1px solid rgba(244, 67, 54, 0.2);
		border-radius: 6px;
		color: var(--text-danger, #f44336);
		font-size: 0.88rem;
	}

	.result-error p { margin: 0; }

	.result-content {
		margin-top: 16px;
		padding: 16px;
		background: var(--bg-secondary);
		border-radius: 6px;
		border: 1px solid var(--border-color);
	}

	.report-text {
		font-size: 0.9rem;
		line-height: 1.7;
		color: var(--text-primary);
		white-space: pre-wrap;
		word-break: break-word;
	}

	.report-text :global(h2),
	.report-text :global(h3),
	.report-text :global(h4) {
		margin: 12px 0 4px;
		font-weight: 700;
	}

	.report-text :global(strong) {
		font-weight: 700;
	}

	.discord-hint {
		margin: 10px 0 0;
		font-size: 0.78rem;
		color: var(--text-secondary);
		text-align: right;
	}

	@media (max-width: 480px) {
		.report-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.period-label {
			min-width: 110px;
		}

		.generate-btn {
			margin-left: 0;
			width: 100%;
			justify-content: center;
		}
	}
</style>
