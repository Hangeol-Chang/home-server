import { buildUrl, ENDPOINTS, apiGet } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.scheduleManager);

export async function getGoogleEvents(year, month) {
    return apiGet(`${API_BASE}/google-events`, { year, month });
}

export async function getGoogleEventsForWeek(startDate, endDate) {
    return apiGet(`${API_BASE}/google-events/week`, { start_date: startDate, end_date: endDate });
}
