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
			allowedHosts: env.VITE_ALLOWED_HOSTS ? env.VITE_ALLOWED_HOSTS.split(',') : [],
			hmr: env.VITE_HMR_HOST ? {
				host: env.VITE_HMR_HOST,
				port: 5173
			} : true,
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
