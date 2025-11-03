// Notebook API 호출 함수들
import { buildUrl, ENDPOINTS, apiGet } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.notebook);

// ===== Directory Tree =====
export async function getDirectoryTree(path = '') {
	return apiGet(`${API_BASE}/tree`, path ? { path } : {});
}

// ===== Folders =====
export async function getFolders(path = '') {
	return apiGet(`${API_BASE}/folders`, path ? { path } : {});
}

// ===== Files =====
export async function getFiles(path = '') {
	return apiGet(`${API_BASE}/files`, path ? { path } : {});
}

// ===== File Content =====
export async function getFileContent(path) {
	return apiGet(`${API_BASE}/content`, { path });
}

// ===== Search =====
export async function searchNotes(query, path = '', inContent = false) {
	const params = { query };
	if (path) params.path = path;
	if (inContent) params.in_content = true;
	return apiGet(`${API_BASE}/search`, params);
}

// ===== Stats =====
export async function getVaultStats() {
	return apiGet(`${API_BASE}/stats`);
}
