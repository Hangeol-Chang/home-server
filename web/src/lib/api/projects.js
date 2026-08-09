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

// ===== Node content (frontmatter 포함 원문 전체) =====
export async function getNodeContent(path) {
	return apiGet(`${API_BASE}/node-content`, { path });
}

export async function saveNode({ path, content }) {
	return apiPost(`${API_BASE}/node`, { path, content });
}

// ===== Folder (project) meta =====
export async function saveFolderMeta({ path, status, start_date, end_date, hide }) {
	return apiPost(`${API_BASE}/folder-meta`, { path, status, start_date, end_date, hide });
}

// ===== 새 파일/폴더 노드 생성 (parent_path 폴더 노드 아래, link_from 있으면 그 노드와 수동 연결) =====
export async function createNode({ parent_path, name, type, link_from }) {
	return apiPost(`${API_BASE}/create-node`, { parent_path, name, type, link_from });
}
