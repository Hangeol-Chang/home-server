// Chat API 호출 함수들
import { buildUrl, ENDPOINTS, apiPost, apiGet } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.chat);

/**
 * Gemini에 메시지 전송
 * @param {string} message - 사용자 메시지
 * @param {Array<{role: string, content: string}>} history - 이전 대화 히스토리
 * @param {string|null} systemPrompt - 시스템 프롬프트 (선택)
 * @returns {Promise<{message: string, role: string, timestamp: string, model: string}>}
 */
export async function sendChatMessage(message, history = [], systemPrompt = null) {
	const body = { message, history };
	if (systemPrompt) body.system_prompt = systemPrompt;
	return apiPost(`${API_BASE}/message`, body);
}

/**
 * Chat 모듈 헬스 체크
 */
export async function getChatHealth() {
	return apiGet(`${API_BASE}/health`);
}
