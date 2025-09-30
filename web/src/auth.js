import { SvelteKitAuth } from "@auth/sveltekit"
import Google from "@auth/core/providers/google"
import fs from 'fs'
import path from 'path'
import { env } from '$env/dynamic/private'

// 허용된 이메일 목록 로드
const allowedEmailsPath = path.resolve(process.cwd(), '../config/allowed_emails.json');
let allowedEmails = [];
try {
	const data = fs.readFileSync(allowedEmailsPath, 'utf8');
	const config = JSON.parse(data);
	allowedEmails = config.allowed_emails || [];
	console.log('Allowed emails loaded:', allowedEmails);
} catch (error) {
	console.error('Failed to load allowed emails:', error);
}

export const { handle, signIn, signOut } = SvelteKitAuth({
	providers: [
		Google({
			clientId: env.GOOGLE_CLIENT_ID,
			clientSecret: env.GOOGLE_CLIENT_SECRET,
		})
	],
	session: {
		strategy: "jwt",
		maxAge: 24 * 60 * 60, // 24시간 (초 단위)
	},
	jwt: {
		maxAge: 24 * 60 * 60, // 24시간 (초 단위)
	},
	callbacks: {
		async signIn({ user, account, profile }) {
			console.log('SignIn attempt for:', user.email);
			// 허용된 이메일 목록에 있는지 확인
			if (user.email && allowedEmails.includes(user.email)) {
				console.log('Access granted for:', user.email);
				return true;
			}
			console.log('Access denied for email:', user.email);
			// 거부 시 false 반환하면 error 페이지로 리디렉션
			return false;
		},
		async session({ session, token }) {
			// 토큰의 만료 시간을 확인
			if (token.exp && Date.now() >= token.exp * 1000) {
				console.log('Session expired, forcing re-login');
				return null; // 세션 만료 시 null 반환하여 재로그인 유도
			}
			return session;
		},
		async jwt({ token, user, account }) {
			if (user) {
				token.email = user.email;
				// 토큰 발급 시간과 만료 시간 설정
				const now = Math.floor(Date.now() / 1000);
				token.iat = now; // issued at
				token.exp = now + (24 * 60 * 60); // 24시간 후 만료
			}
			return token;
		},
		async redirect({ url, baseUrl }) {
			// 로그인 실패 시 에러 페이지로 리디렉션
			if (url.includes('error=AccessDenied')) {
				return `${baseUrl}/auth/error?error=AccessDenied`
			}
			// 성공 시 홈으로
			if (url.startsWith(baseUrl)) return url
			return baseUrl
		}
	},
	pages: {
		error: '/auth/error'
	},
	trustHost: true,
	basePath: '/auth',
	secret: env.AUTH_SECRET,
	cookies: {
		sessionToken: {
			name: `authjs.session-token`,
			options: {
				httpOnly: true,
				sameSite: 'lax',
				path: '/',
				secure: false, // 개발 환경에서는 false
				maxAge: 24 * 60 * 60 // 24시간 (초 단위)
			}
		},
		pkceCodeVerifier: {
			name: "authjs.pkce.code_verifier",
			options: {
				httpOnly: true,
				sameSite: "lax",
				path: "/",
				secure: false, // 개발 환경에서는 false
				maxAge: 60 * 15 // 15분
			},
		},
	}
});