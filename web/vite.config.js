import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	// .env 파일을 불러와서 환경변수 사용
	const env = loadEnv(mode, process.cwd(), '');

	const proxy = {
		'/api': {
			target: 'http://localhost:5005',
			changeOrigin: true,
			rewrite: (path) => path.replace(/^\/api/, '')
		}
	};
	const allowedHosts = env.VITE_ALLOWED_HOSTS ? env.VITE_ALLOWED_HOSTS.split(',') : [];

	return {
		plugins: [sveltekit()],
		// 프로덕션(vite preview): HMR 없음 -> 소켓 재연결 리로드 없음
		preview: { host: '0.0.0.0', port: 5173, allowedHosts, proxy },
		server: {
			host: '0.0.0.0',
			port: 5173,
			allowedHosts,
			hmr: env.VITE_HMR_HOST ? {
				host: env.VITE_HMR_HOST,
				port: 5173
			} : true,
			proxy
		 }
	 };
 });
