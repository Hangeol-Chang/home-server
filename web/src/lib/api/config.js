/**
 * API 공통 설정
 */

import { dev } from '$app/environment';
import { env } from '$env/dynamic/public';

// 환경별 API 베이스 URL
export const API_CONFIG = {
	baseUrl: dev ? '/api' : (env.PUBLIC_API_URL || 'http://localhost:5005'),
	timeout: 30000
};

// 현재 환경의 설정
export const currentConfig = API_CONFIG;

// API 베이스 URL
export const BASE_URL = currentConfig.baseUrl;

// 모듈별 엔드포인트
export const ENDPOINTS = {
	assetManager: '/asset-manager',
	scheduleManager: '/schedule-manager',
	notebook: '/notebook',
	// 추가 모듈들...
};

// 공통 헤더
export const DEFAULT_HEADERS = {
	'Content-Type': 'application/json',
	'Accept': 'application/json'
};

// 공통 Fetch 옵션
export const DEFAULT_FETCH_OPTIONS = {
	headers: DEFAULT_HEADERS,
	credentials: 'include' // 쿠키 포함 (인증용)
};

/**
 * API 요청 래퍼 함수
 * 공통 에러 처리 및 로깅 포함
 */
export async function apiRequest(url, options = {}) {
	const config = {
		...DEFAULT_FETCH_OPTIONS,
		...options,
		headers: {
			...DEFAULT_HEADERS,
			...options.headers
		}
	};

	try {
		const response = await fetch(url, config);
		
		if (!response.ok) {
			// 에러 응답 처리
			let errorMessage = `Request failed: ${response.status} ${response.statusText}`;
			try {
				const errorData = await response.json();
				errorMessage = errorData.detail || errorData.message || errorMessage;
			} catch {
				// JSON 파싱 실패 시 기본 메시지 사용
			}
			throw new Error(errorMessage);
		}

		// 204 No Content 처리
		if (response.status === 204) {
			return null;
		}

		return await response.json();
	} catch (error) {
		console.error(`API Request Error [${options.method || 'GET'} ${url}]:`, error);
		throw error;
	}
}

/**
 * GET 요청 헬퍼
 */
export async function apiGet(url, params = {}) {
	const urlParams = new URLSearchParams();
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined && value !== '') {
			urlParams.append(key, value);
		}
	});
	
	const queryString = urlParams.toString();
	const fullUrl = queryString ? `${url}?${queryString}` : url;
	
	return apiRequest(fullUrl, { method: 'GET' });
}

/**
 * POST 요청 헬퍼
 */
export async function apiPost(url, data) {
	return apiRequest(url, {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

/**
 * PUT 요청 헬퍼
 */
export async function apiPut(url, data) {
	return apiRequest(url, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

/**
 * DELETE 요청 헬퍼
 */
export async function apiDelete(url) {
	return apiRequest(url, { method: 'DELETE' });
}

/**
 * PATCH 요청 헬퍼
 */
export async function apiPatch(url, data = null, params = {}) {
	const urlParams = new URLSearchParams();
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined && value !== '') {
			urlParams.append(key, value);
		}
	});
	
	const queryString = urlParams.toString();
	const fullUrl = queryString ? `${url}?${queryString}` : url;
	
	return apiRequest(fullUrl, {
		method: 'PATCH',
		body: data ? JSON.stringify(data) : undefined
	});
}

/**
 * 전체 URL 생성 헬퍼
 */
export function buildUrl(endpoint, path = '') {
	return `${BASE_URL}${endpoint}${path}`;
}
