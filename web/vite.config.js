import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		host: '0.0.0.0',
		port: 5173,
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
});
