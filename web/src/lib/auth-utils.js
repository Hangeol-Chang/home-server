import { ALLOWED_EMAILS } from '$env/static/private';

/**
 * 허용된 이메일 목록을 가져옵니다.
 * @returns {string[]} 허용된 이메일 배열
 */
export function getAllowedEmails() {
	if (!ALLOWED_EMAILS) {
		console.warn('ALLOWED_EMAILS 환경 변수가 설정되지 않았습니다.');
		return [];
	}
	
	// 콤마로 구분된 이메일을 배열로 변환하고 공백 제거
	return ALLOWED_EMAILS.split(',')
		.map(email => email.trim().toLowerCase())
		.filter(email => email.length > 0);
}

/**
 * 이메일이 허용된 목록에 있는지 확인합니다.
 * @param {string} email - 확인할 이메일
 * @returns {boolean} 허용 여부
 */
export function isEmailAllowed(email) {
	if (!email) return false;
	const allowedEmails = getAllowedEmails();
	return allowedEmails.includes(email.toLowerCase());
}
