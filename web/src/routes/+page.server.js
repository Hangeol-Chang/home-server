import { redirect } from '@sveltejs/kit'

export const load = async (event) => {
	const session = await event.locals.getSession?.()
	
	// 로그인하지 않은 사용자는 로그인 페이지로 리디렉션
	if (!session?.user) {
		throw redirect(302, '/auth/signin')
	}
	
	// 세션 만료 체크 (추가 보안)
	if (session.expires && new Date(session.expires) < new Date()) {
		console.log('Session expired, redirecting to login');
		throw redirect(302, '/auth/signin')
	}
	
	return {
		user: session.user,
		sessionExpires: session.expires
	}
}