import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		host: '0.0.0.0', // 외부 접근 허용
		port: 5173,
		hmr: {
			host: 'hgchang1.iptime.org',
			port: 5173
		}
	}
});
