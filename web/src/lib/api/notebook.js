// Notebook API 호출 함수들
import { buildUrl, ENDPOINTS, apiGet, apiPost, apiDelete } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.notebook);

// ===== Git =====
export async function pullRepository() {
	return apiPost(`${API_BASE}/git-pull`);
}

// ===== Directory Tree =====
export async function getDirectoryTree(path = '') {
	return apiGet(`${API_BASE}/tree`, path ? { path } : {});
}

// ===== Folders =====
export async function getFolders(path = '', showHidden = false) {
	const params = {};
	if (path) params.path = path;
	if (showHidden) params.show_hidden = true;
	return apiGet(`${API_BASE}/folders`, params);
}

// ===== Files =====
export async function getFiles(path = '', showHidden = false) {
	const params = {};
	if (path) params.path = path;
	if (showHidden) params.show_hidden = true;
	return apiGet(`${API_BASE}/files`, params);
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

// ===== Save Note =====
export async function saveNote(path, content, commitMessage = '') {
	return apiPost(`${API_BASE}/save`, {
		path,
		content,
		commit_message: commitMessage
	});
}

// ===== Create Folder =====
export async function createFolder(path, commitMessage = '') {
	return apiPost(`${API_BASE}/folder`, {
		path,
		commit_message: commitMessage
	});
}

// ===== Move =====
export async function moveItem(srcPath, destFolder) {
	return apiPost(`${API_BASE}/move`, { src_path: srcPath, dest_folder: destFolder });
}

// ===== Rename =====
export async function renameItem(srcPath, newName) {
	return apiPost(`${API_BASE}/rename`, { src_path: srcPath, new_name: newName });
}

// ===== Delete File =====
export async function deleteFile(path) {
	return apiDelete(`${API_BASE}/file?path=${encodeURIComponent(path)}`);
}

// ===== Delete Folder =====
export async function deleteFolder(path) {
	return apiDelete(`${API_BASE}/folder?path=${encodeURIComponent(path)}`);
}

// ===== Stats =====
export async function getVaultStats() {
	return apiGet(`${API_BASE}/stats`);
}
