import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	// .env 파일을 불러와서 환경변수 사용
	const env = loadEnv(mode, process.cwd(), '');

	return {
		plugins: [sveltekit()],
		server: {
			host: '0.0.0.0',
			port: 5173,
			allowedHosts: env.VITE_NGROK_HOST ? [env.VITE_NGROK_HOST] : [],
			hmr: {
			host: 'hgchang1.iptime.org',
			port: 5173
		},
			 proxy: {
				 '/api': {
					 target: 'http://localhost:5005',
					 changeOrigin: true,
					 rewrite: (path) => path.replace(/^\/api/, '')
				 }
			 }
		 }
	 };
 });
