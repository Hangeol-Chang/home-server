import { buildUrl, ENDPOINTS, apiPost } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.test);

export async function checkDiscordWebhook() {
	return apiPost(`${API_BASE}/discord-webhook`, {});
}

/**
 * @param {number} year
 * @param {number} month
 * @param {boolean} sendDiscord
 * @returns {Promise<{content: string, year: number, month: number, status: string}>}
 */
export async function generateMonthlyReport(year, month, sendDiscord = true) {
	return apiPost(`${API_BASE}/monthly-report`, { year, month, send_discord: sendDiscord });
}

/**
 * @param {string} weekStart  YYYY-MM-DD
 * @param {string} weekEnd    YYYY-MM-DD
 * @param {boolean} sendDiscord
 * @returns {Promise<{content: string, week_start: string, week_end: string, status: string}>}
 */
export async function generateWeeklyReport(weekStart, weekEnd, sendDiscord = true) {
	return apiPost(`${API_BASE}/weekly-report`, {
		week_start: weekStart,
		week_end: weekEnd,
		send_discord: sendDiscord
	});
}
