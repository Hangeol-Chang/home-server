import { redirect } from '@sveltejs/kit'

export const load = async (event) => {
	const session = await event.locals.getSession?.()
	
	// 로그인하지 않은 사용자는 로그인 페이지로 리디렉션
	if (!session?.user) {
		throw redirect(302, '/auth/signin')
	}
	
	return {
		user: session.user
	}
}