import { buildUrl, ENDPOINTS, apiGet, apiPost, apiPut, apiDelete, apiPatch } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.scheduleManager);

export async function getGoogleEvents(year, month) {
    return apiGet(`${API_BASE}/google-events`, { year, month });
}

export async function getGoogleEventsForWeek(startDate, endDate) {
    return apiGet(`${API_BASE}/google-events/week`, { start_date: startDate, end_date: endDate });
}

// --- Todo API ---

export async function getTodos(startDate, endDate, includeCompleted = true) {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    params.include_completed = includeCompleted;
    return apiGet(`${API_BASE}/todos`, params);
}

export async function createTodo(todo) {
    return apiPost(`${API_BASE}/todos`, todo);
}

export async function updateTodo(todoId, todo) {
    return apiPut(`${API_BASE}/todos/${todoId}`, todo);
}

export async function deleteTodo(todoId) {
    return apiDelete(`${API_BASE}/todos/${todoId}`);
}

export async function toggleTodoCompletion(todoId) {
    return apiPatch(`${API_BASE}/todos/${todoId}/toggle`);
}

export async function moveTodo(todoId, newStartDate, newEndDate) {
    return apiPatch(`${API_BASE}/todos/${todoId}/move`, null, {
        new_start_date: newStartDate,
        new_end_date: newEndDate
    });
}

// --- Weekly Timetable API ---

export async function getWeeklySchedules() {
    return apiGet(`${API_BASE}/weekly-schedules`);
}

export async function createWeeklySchedule(schedule) {
    return apiPost(`${API_BASE}/weekly-schedules`, schedule);
}

export async function updateWeeklySchedule(scheduleId, schedule) {
    return apiPut(`${API_BASE}/weekly-schedules/${scheduleId}`, schedule);
}

export async function deleteWeeklySchedule(scheduleId) {
    return apiDelete(`${API_BASE}/weekly-schedules/${scheduleId}`);
}
