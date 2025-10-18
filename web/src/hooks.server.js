import { SvelteKitAuth } from '@auth/sveltekit';
import Google from '@auth/core/providers/google';
import { GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, AUTH_SECRET } from '$env/static/private';
import { isEmailAllowed } from '$lib/auth-utils';
import { redirect } from '@sveltejs/kit';
import { dev } from '$app/environment';
import { sequence } from '@sveltejs/kit/hooks';

const secret = AUTH_SECRET;
if (!secret) {
	throw new Error('AUTH_SECRET 환경 변수가 설정되지 않았습니다. 프로덕션 환경에서는 필수입니다.');
}

const { handle: authHandle } = SvelteKitAuth({
	providers: [
		Google({
			clientId: GOOGLE_CLIENT_ID,
			clientSecret: GOOGLE_CLIENT_SECRET
		})
	],
	secret,
	trustHost: true,
	callbacks: {
		async signIn({ user, account, profile }) {
			// 이메일이 허용된 목록에 있는지 확인
			if (user?.email && isEmailAllowed(user.email)) {
				return true;
			}
			// 허용되지 않은 이메일은 로그인 거부
			console.log(`로그인 거부: ${user?.email}`);
			return false;
		},
		async session({ session, token }) {
			// 세션에 사용자 정보 추가
			if (session?.user) {
				session.user.id = token.sub;
			}
			return session;
		}
	},
	pages: {
		signIn: '/login',
		error: '/login'
	}
});

// 인증 확인 핸들러
async function authorizationHandle({ event, resolve }) {
	// 인증이 필요한 페이지 목록 (로그인 페이지와 auth 콜백은 제외)
	const publicPaths = ['/login', '/auth'];
	const isPublicPath = publicPaths.some((path) => event.url.pathname.startsWith(path));

	if (!isPublicPath) {
		const session = await event.locals.auth();

		// 로그인되지 않았거나 허용되지 않은 이메일이면 로그인 페이지로 리다이렉트
		if (!session?.user?.email || !isEmailAllowed(session.user.email)) {
			throw redirect(303, '/login');
		}
	}

	return resolve(event);
}

// sequence를 사용하여 핸들러들을 올바른 순서로 실행
export const handle = sequence(authHandle, authorizationHandle);
