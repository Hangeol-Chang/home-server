import { buildUrl, ENDPOINTS, apiPost, apiGet, apiDelete } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.chat);

/**
 * Ollama로 메시지 전송
 * @param {string} message
 * @param {Array<{role: string, content: string}>} history
 * @param {string|null} systemPrompt
 */
export async function sendChatMessage(message, history = [], systemPrompt = null, maxCtx = null) {
	const body = { message, history };
	if (systemPrompt) body.system_prompt = systemPrompt;
	if (maxCtx) body.max_ctx = maxCtx;
	return apiPost(`${API_BASE}/message`, body);
}

/** Chat 모듈 헬스 체크 */
export async function getChatHealth() {
	return apiGet(`${API_BASE}/health`);
}

// ===== Agent loop =====

/**
 * 에이전트 루프 시작
 * @param {string} objective
 * @param {string|null} systemPrompt
 * @param {string|null} model
 */
export async function agentStart(objective, systemPrompt = null, model = null) {
	const body = { objective };
	if (systemPrompt) body.system_prompt = systemPrompt;
	if (model) body.model = model;
	return apiPost(`${API_BASE}/agent/start`, body);
}

/** 에이전트 루프 중지 */
export async function agentStop() {
	return apiPost(`${API_BASE}/agent/stop`, {});
}

/**
 * 에이전트 상태 및 로그 조회
 * @param {number} logTail - 최근 로그 수 (기본 30)
 */
export async function agentStatus(logTail = 30) {
	return apiGet(`${API_BASE}/agent/status?log_tail=${logTail}`);
}

/** 에이전트 로그 초기화 */
export async function agentClearLogs() {
	return apiDelete(`${API_BASE}/agent/logs`);
}
