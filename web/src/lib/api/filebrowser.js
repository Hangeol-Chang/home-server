// File Browser (oracle_mirror) API — 백엔드 프록시 경유, 자격증명은 서버에만 존재
import { buildUrl, ENDPOINTS, apiGet, apiRequest } from './config.js';

const API_BASE = buildUrl(ENDPOINTS.filebrowser);

export const listFbFiles = (path = '/') => apiGet(`${API_BASE}/files`, { path });

export const getFbContentUrl = (path, download = false) =>
	`${API_BASE}/content?path=${encodeURIComponent(path)}${download ? '&download=true' : ''}`;

/** 업로드 + 진행률. fetch는 업로드 진행률을 못 줘서 XHR 사용. */
export function uploadFbFile(path, file, onProgress, override = false) {
	return new Promise((resolve, reject) => {
		const xhr = new XMLHttpRequest();
		xhr.open('POST', `${API_BASE}/upload?path=${encodeURIComponent(path)}&override=${override}`);
		xhr.upload.onprogress = (e) => e.lengthComputable && onProgress?.(e.loaded / e.total);
		xhr.onload = () => {
			if (xhr.status < 300) return resolve();
			let msg = `업로드 실패 (${xhr.status})`;
			try { msg = JSON.parse(xhr.responseText).detail || msg; } catch { /* 본문이 JSON 아님 */ }
			reject(new Error(msg));
		};
		xhr.onerror = () => reject(new Error('네트워크 오류'));
		xhr.send(file);
	});
}

export const mkdirFb = (path) =>
	apiRequest(`${API_BASE}/mkdir?path=${encodeURIComponent(path)}`, { method: 'POST' });

export const deleteFb = (path) =>
	apiRequest(`${API_BASE}/files?path=${encodeURIComponent(path)}`, { method: 'DELETE' });
