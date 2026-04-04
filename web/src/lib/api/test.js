import { buildUrl, ENDPOINTS, apiPost } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.test);

/**
 * 디스코드 웹훅 헬스 체크용 API
 * @returns {Promise<{message: string, status: string}>}
 */
export async function checkDiscordWebhook() {
	return apiPost(`${API_BASE}/discord-webhook`, {});
}
