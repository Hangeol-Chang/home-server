// Projects API 호출 함수들
import { buildUrl, ENDPOINTS, apiGet, apiPost } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.projects);

// ===== Top Folders =====
export async function getTopFolders() {
	return apiGet(`${API_BASE}/top-folders`);
}

// ===== Subprojects (0_ 폴더 바로 아래 프로젝트 폴더, 표시/숨김 관리용) =====
export async function getSubprojects(folder) {
	return apiGet(`${API_BASE}/subprojects`, { folder });
}

// ===== Graph (nodes + edges + positions) =====
export async function getGraph(folder) {
	return apiGet(`${API_BASE}/graph`, { folder });
}

export async function saveGraph(folder, positions, edges) {
	return apiPost(`${API_BASE}/graph`, { folder, positions, edges });
}

// ===== Node content (frontmatter + body) =====
export async function getNodeContent(path) {
	return apiGet(`${API_BASE}/node-content`, { path });
}

export async function saveNode({ path, status, start_date, end_date, content }) {
	return apiPost(`${API_BASE}/node`, { path, status, start_date, end_date, content });
}

// ===== Folder (project) meta =====
export async function saveFolderMeta({ path, status, start_date, end_date, hide }) {
	return apiPost(`${API_BASE}/folder-meta`, { path, status, start_date, end_date, hide });
}
