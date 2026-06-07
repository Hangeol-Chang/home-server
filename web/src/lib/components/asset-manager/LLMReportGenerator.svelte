<script>
	import { generateMonthlyReport, generateWeeklyReport } from '$lib/api/test.js';

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
		status = '';
	}

	// ── 주간 상태 ──
	let weekOffset = $state(0);

	function getWeekRange(offsetWeeks = 0) {
		const d = new Date();
		d.setDate(d.getDate() + offsetWeeks * 7);
		const day  = d.getDay();
		const diff = day === 0 ? -6 : 1 - day;
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
		status = '';
	}

	function setMode(m) {
		mode = m;
		status = '';
	}

	// ── 전송 상태 ──
	let loading = $state(false);
	let status  = $state(''); // '' | 'success' | 'error'
	let errorMsg = $state('');

	async function generate() {
		loading = true;
		status  = '';
		errorMsg = '';
		try {
			if (mode === 'monthly') {
				await generateMonthlyReport(reportYear, reportMonth, true);
			} else {
				await generateWeeklyReport(fmt(weekRange.start), fmt(weekRange.end), true);
			}
			status = 'success';
		} catch (e) {
			status   = 'error';
			errorMsg = e.message || '전송에 실패했습니다.';
		} finally {
			loading = false;
		}
	}
</script>

<div class="llm-report">
	<div class="report-header">
		<h3 class="report-title">🤖 AI 재무 리포트</h3>
		<div class="mode-tabs">
			<button class="mode-tab" class:active={mode === 'weekly'}  onclick={() => setMode('weekly')}>📅 주간</button>
			<button class="mode-tab" class:active={mode === 'monthly'} onclick={() => setMode('monthly')}>📊 월간</button>
		</div>
	</div>

	<div class="period-row">
		{#if mode === 'monthly'}
			<button class="nav-btn" onclick={() => changeMonth(-1)} aria-label="이전 달">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
			</button>
			<span class="period-label">{reportYear}년 {reportMonth}월</span>
			<button class="nav-btn" onclick={() => changeMonth(1)} aria-label="다음 달">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
			</button>
		{:else}
			<button class="nav-btn" onclick={() => changeWeek(-1)} aria-label="이전 주">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
			</button>
			<span class="period-label">{weekLabel(weekRange)}</span>
			<button class="nav-btn" onclick={() => changeWeek(1)} aria-label="다음 주">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
			</button>
		{/if}

		<button class="generate-btn" onclick={generate} disabled={loading}>
			{#if loading}
				<span class="spinner"></span>생성 중…
			{:else}
				✨ Discord로 전송
			{/if}
		</button>
	</div>

	{#if status === 'success'}
		<p class="status-msg success">✅ Discord로 리포트를 전송했습니다.</p>
	{:else if status === 'error'}
		<p class="status-msg error">⚠️ {errorMsg}</p>
	{/if}
</div>

<style>
	.llm-report {
		border: 1px solid var(--border-color);
		border-radius: 8px;
		padding: 16px 24px;
		margin-bottom: 32px;
		background-color: var(--bg-primary);
	}

	.report-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 14px;
		gap: 12px;
		flex-wrap: wrap;
	}

	.report-title {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-primary);
	}

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

	.generate-btn:hover:not(:disabled) { opacity: 0.85; }
	.generate-btn:disabled { opacity: 0.6; cursor: not-allowed; }

	.spinner {
		display: inline-block;
		width: 14px;
		height: 14px;
		border: 2px solid rgba(255, 255, 255, 0.4);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}

	@keyframes spin { to { transform: rotate(360deg); } }

	.status-msg {
		margin: 10px 0 0;
		font-size: 0.85rem;
		padding: 8px 12px;
		border-radius: 6px;
	}

	.status-msg.success {
		background: rgba(76, 175, 80, 0.1);
		color: var(--text-success, #4caf50);
	}

	.status-msg.error {
		background: rgba(244, 67, 54, 0.08);
		color: var(--text-danger, #f44336);
	}

	@media (max-width: 480px) {
		.report-header { flex-direction: column; align-items: flex-start; }
		.period-label { min-width: 110px; }
		.generate-btn { margin-left: 0; width: 100%; justify-content: center; }
	}
</style>
