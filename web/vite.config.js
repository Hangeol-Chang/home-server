import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'path';

// Dynamically import all route files from modules
import.meta.glob('../../module/*/web/routes.js')

export default defineConfig({
	plugins: [sveltekit()],
	resolve: {
		alias: {
			'@asset-manager': path.resolve('../../modules/asset-manager/web/src'),
			'@schedule-manager': path.resolve('../../modules/schedule-manager/web/src'),
		}
	}
});
