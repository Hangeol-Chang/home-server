// Asset Manager API 호출 함수들

const API_BASE_URL = 'http://localhost:5005/asset-manager';

// ===== Classes (거래 분류) =====
export async function getClasses() {
	const response = await fetch(`${API_BASE_URL}/classes`);
	if (!response.ok) throw new Error('Failed to fetch classes');
	return response.json();
}

// ===== Categories (카테고리) =====
export async function getCategories(classId = null) {
	const url = classId 
		? `${API_BASE_URL}/categories?class_id=${classId}`
		: `${API_BASE_URL}/categories`;
	const response = await fetch(url);
	if (!response.ok) throw new Error('Failed to fetch categories');
	return response.json();
}

export async function createCategory(categoryData) {
	const response = await fetch(`${API_BASE_URL}/categories`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(categoryData)
	});
	if (!response.ok) throw new Error('Failed to create category');
	return response.json();
}

export async function deleteCategory(categoryId) {
	const response = await fetch(`${API_BASE_URL}/categories/${categoryId}`, {
		method: 'DELETE'
	});
	if (!response.ok) throw new Error('Failed to delete category');
	return response.json();
}

// ===== Tiers (티어) =====
export async function getTiers(classId = null) {
	const url = classId 
		? `${API_BASE_URL}/tiers?class_id=${classId}`
		: `${API_BASE_URL}/tiers`;
	const response = await fetch(url);
	if (!response.ok) throw new Error('Failed to fetch tiers');
	return response.json();
}

export async function createTier(tierData) {
	const response = await fetch(`${API_BASE_URL}/tiers`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(tierData)
	});
	if (!response.ok) throw new Error('Failed to create tier');
	return response.json();
}

export async function deleteTier(tierId) {
	const response = await fetch(`${API_BASE_URL}/tiers/${tierId}`, {
		method: 'DELETE'
	});
	if (!response.ok) throw new Error('Failed to delete tier');
	return response.json();
}

// ===== Transactions (거래) =====
export async function createTransaction(transactionData) {
	const response = await fetch(`${API_BASE_URL}/transactions`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(transactionData)
	});
	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to create transaction');
	}
	return response.json();
}

export async function getTransactions(filters = {}) {
	const params = new URLSearchParams();
	if (filters.class_id) params.append('class_id', filters.class_id);
	if (filters.start_date) params.append('start_date', filters.start_date);
	if (filters.end_date) params.append('end_date', filters.end_date);
	if (filters.category_id) params.append('category_id', filters.category_id);
	if (filters.tier_id) params.append('tier_id', filters.tier_id);
	if (filters.limit) params.append('limit', filters.limit);
	if (filters.offset) params.append('offset', filters.offset);

	const response = await fetch(`${API_BASE_URL}/transactions?${params}`);
	if (!response.ok) throw new Error('Failed to fetch transactions');
	return response.json();
}

export async function getTransaction(transactionId) {
	const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}`);
	if (!response.ok) throw new Error('Failed to fetch transaction');
	return response.json();
}

export async function updateTransaction(transactionId, updateData) {
	const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(updateData)
	});
	if (!response.ok) throw new Error('Failed to update transaction');
	return response.json();
}

export async function deleteTransaction(transactionId) {
	const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}`, {
		method: 'DELETE'
	});
	if (!response.ok) throw new Error('Failed to delete transaction');
	return response.json();
}

// ===== Statistics (통계) =====
export async function getPeriodStatistics(classId, startDate = null, endDate = null) {
	const params = new URLSearchParams({ class_id: classId });
	if (startDate) params.append('start_date', startDate);
	if (endDate) params.append('end_date', endDate);

	const response = await fetch(`${API_BASE_URL}/statistics/period?${params}`);
	if (!response.ok) throw new Error('Failed to fetch period statistics');
	return response.json();
}

export async function getMonthlyStatistics(year, month) {
	const response = await fetch(`${API_BASE_URL}/statistics/monthly?year=${year}&month=${month}`);
	if (!response.ok) throw new Error('Failed to fetch monthly statistics');
	return response.json();
}

export async function searchTransactions(query, classId = null) {
	const params = new URLSearchParams({ query });
	if (classId) params.append('class_id', classId);

	const response = await fetch(`${API_BASE_URL}/search?${params}`);
	if (!response.ok) throw new Error('Failed to search transactions');
	return response.json();
}
