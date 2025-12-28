// Asset Manager API 호출 함수들
import { buildUrl, ENDPOINTS, apiGet, apiPost, apiPut, apiDelete } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.assetManager);

// ===== Classes (거래 분류) =====
export async function getClasses() {
	return apiGet(`${API_BASE}/classes`);
}

// ===== Categories (카테고리) =====
export async function getCategories(classId = null) {
	return apiGet(`${API_BASE}/categories`, classId ? { class_id: classId } : {});
}

export async function createCategory(categoryData) {
	return apiPost(`${API_BASE}/categories`, categoryData);
}

export async function deleteCategory(categoryId) {
	return apiDelete(`${API_BASE}/categories/${categoryId}`);
}

// ===== Sub Categories (하위 카테고리) =====
export async function getSubCategories(categoryId = null) {
	return apiGet(`${API_BASE}/sub-categories`, categoryId ? { category_id: categoryId } : {});
}

export async function createSubCategory(subCategoryData) {
	return apiPost(`${API_BASE}/sub-categories`, subCategoryData);
}

export async function deleteSubCategory(subCategoryId) {
	return apiDelete(`${API_BASE}/sub-categories/${subCategoryId}`);
}

// ===== Tiers (티어) =====
export async function getTiers(classId = null) {
	return apiGet(`${API_BASE}/tiers`, classId ? { class_id: classId } : {});
}

export async function createTier(tierData) {
	return apiPost(`${API_BASE}/tiers`, tierData);
}

export async function deleteTier(tierId) {
	return apiDelete(`${API_BASE}/tiers/${tierId}`);
}

// ===== Budgets (예산) =====
export async function getBudgets(year, month, classId = null) {
    const params = { year, month };
    if (classId) params.class_id = classId;
    return apiGet(`${API_BASE}/budgets`, params);
}

export async function updateBudget(categoryId, year, month, budgetData) {
    return apiPut(`${API_BASE}/budgets/${categoryId}/${year}/${month}`, budgetData);
}

export async function updateCategoryDefaultBudget(categoryId, defaultBudget) {
    return apiPut(`${API_BASE}/categories/${categoryId}/default-budget?default_budget=${defaultBudget}`, {});
}

// ===== Transactions (거래) =====
export async function createTransaction(transactionData) {
	return apiPost(`${API_BASE}/transactions`, transactionData);
}

export async function getTransactions(filters = {}) {
	return apiGet(`${API_BASE}/transactions`, filters);
}

export async function getUnclassifiedTransactions() {
	return apiGet(`${API_BASE}/transactions/unclassified`);
}

export async function getTransaction(transactionId) {
	return apiGet(`${API_BASE}/transactions/${transactionId}`);
}

export async function updateTransaction(transactionId, updateData) {
	return apiPut(`${API_BASE}/transactions/${transactionId}`, updateData);
}

export async function deleteTransaction(transactionId) {
	return apiDelete(`${API_BASE}/transactions/${transactionId}`);
}

// ===== Statistics (통계) =====
export async function getPeriodStatistics(classId, startDate = null, endDate = null) {
	const params = { class_id: classId };
	if (startDate) params.start_date = startDate;
	if (endDate) params.end_date = endDate;
	return apiGet(`${API_BASE}/statistics/period`, params);
}

export async function getMonthlyStatistics(year, month) {
	return apiGet(`${API_BASE}/statistics/monthly`, { year, month });
}

export async function getPeriodComparison(unit = 'week', periods = 4, endDate = null) {
	const params = { unit, periods };
	if (endDate) params.end_date = endDate;
	return apiGet(`${API_BASE}/statistics/period-comparison`, params);
}

export async function searchTransactions(query, classId = null) {
	const params = { query };
	if (classId) params.class_id = classId;
	return apiGet(`${API_BASE}/search`, params);
}

// ===== Tags (태그) =====
export async function getTags(activeOnly = true) {
	return apiGet(`${API_BASE}/tags`, { active_only: activeOnly });
}

export async function createTag(tagData) {
	return apiPost(`${API_BASE}/tags`, tagData);
}

export async function updateTag(tagId, tagData) {
	return apiPut(`${API_BASE}/tags/${tagId}`, tagData);
}

export async function deleteTag(tagId, force = false) {
	return apiDelete(`${API_BASE}/tags/${tagId}`, force ? { force } : {});
}
