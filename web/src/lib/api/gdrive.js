// Google Drive API 호출 함수들
import { buildUrl, ENDPOINTS, apiGet } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.gdrive);

/**
 * 폴더의 파일 목록 반환
 * @param {string|null} folderId - 폴더 ID (null이면 루트)
 * @param {string|null} pageToken - 페이지네이션 토큰
 */
export async function listFiles(folderId = null, pageToken = null) {
	const params = {};
	if (folderId) params.folder_id = folderId;
	if (pageToken) params.page_token = pageToken;
	return apiGet(`${API_BASE}/files`, params);
}

/**
 * 파일/폴더 메타데이터 반환
 * @param {string} fileId
 */
export async function getFileMeta(fileId) {
	return apiGet(`${API_BASE}/files/${fileId}/meta`);
}

/**
 * 파일 다운로드 URL 생성 (백엔드 경유)
 * @param {string} fileId
 */
export function getFileContentUrl(fileId) {
	return `${API_BASE}/files/${fileId}/content`;
}

/**
 * 폴더 breadcrumb 경로 반환
 * @param {string} folderId
 */
export async function getBreadcrumb(folderId) {
	return apiGet(`${API_BASE}/breadcrumb`, { folder_id: folderId });
}
