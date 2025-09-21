#!/usr/bin/env node

import { spawn } from 'child_process';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class SubmoduleManager {
    constructor() {
        this.processes = [];
        this.submodules = [
            {
                name: 'asset-manager',
                path: join(__dirname, '../../modules/asset-manager/web'),
                port: 5174,
                color: '\x1b[36m' // cyan
            },
            {
                name: 'schedule-manager', 
                path: join(__dirname, '../../modules/schedule-manager/web'),
                port: 5175,
                color: '\x1b[35m' // magenta
            }
        ];
    }

    log(message, color = '\x1b[37m') {
        console.log(`${color}[SubmoduleManager]${'\x1b[0m'} ${message}`);
    }

    async checkSubmoduleExists(submodule) {
        const fs = await import('fs');
        return fs.existsSync(submodule.path);
    }

    async ensureSubmoduleSetup(submodule) {
        const fs = await import('fs');
        const packageJsonPath = join(submodule.path, 'package.json');
        
        if (!fs.existsSync(packageJsonPath)) {
            this.log(`Setting up ${submodule.name}...`, submodule.color);
            
            // 기본 package.json 생성
            const packageJson = {
                name: `${submodule.name}-web`,
                version: "1.0.0",
                type: "module", 
                scripts: {
                    dev: `vite --port ${submodule.port}`,
                    build: "vite build",
                    preview: "vite preview"
                },
                devDependencies: {
                    "@sveltejs/vite-plugin-svelte": "^3.0.0",
                    "svelte": "^4.2.0",
                    "vite": "^5.0.0"
                },
                dependencies: {
                    "axios": "^1.6.0"
                }
            };
            
            fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
            
            // 기본 vite.config.js 생성
            const viteConfig = `import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: ${submodule.port},
    proxy: {
      '/api': 'http://localhost:5000'
    }
  }
})`;
            
            fs.writeFileSync(join(submodule.path, 'vite.config.js'), viteConfig);
            
            // 기본 index.html 생성
            const indexHtml = `<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${submodule.name}</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>`;
            
            fs.writeFileSync(join(submodule.path, 'index.html'), indexHtml);
            
            // src 디렉터리와 기본 파일들 생성
            const srcDir = join(submodule.path, 'src');
            if (!fs.existsSync(srcDir)) {
                fs.mkdirSync(srcDir, { recursive: true });
            }
            
            // 기본 main.js
            const mainJs = `import './app.css'
import App from './App.svelte'

const app = new App({
  target: document.getElementById('app'),
})

export default app`;
            
            fs.writeFileSync(join(srcDir, 'main.js'), mainJs);
            
            // 기본 App.svelte
            const appSvelte = `<script>
  import axios from 'axios';
  
  let data = [];
  let loading = false;
  
  const moduleName = '${submodule.name}';
  const apiBase = '/api/${submodule.name}';
  
  async function loadData() {
    loading = true;
    try {
      // API 엔드포인트에 따라 조정
      const response = await axios.get(apiBase + '/');
      data = response.data;
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      loading = false;
    }
  }
  
  loadData();
</script>

<main>
  <h1>${submodule.name} Module</h1>
  
  <div class="info">
    <p>🎯 Module: <strong>{moduleName}</strong></p>
    <p>🌐 Port: <strong>${submodule.port}</strong></p>
    <p>🔗 API: <strong>{apiBase}</strong></p>
  </div>
  
  {#if loading}
    <p>Loading...</p>
  {:else}
    <div class="data-section">
      <h2>Data</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  {/if}
</main>

<style>
  main {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  
  h1 {
    color: #333;
    text-transform: capitalize;
  }
  
  .info {
    background: #f5f5f5;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
  }
  
  .data-section {
    margin-top: 2rem;
  }
  
  pre {
    background: #2d2d2d;
    color: #fff;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
  }
</style>`;
            
            fs.writeFileSync(join(srcDir, 'App.svelte'), appSvelte);
            
            // 기본 CSS
            const appCss = `body {
  margin: 0;
  padding: 0;
  background-color: #f9f9f9;
}`;
            
            fs.writeFileSync(join(srcDir, 'app.css'), appCss);
        }
    }

    async startSubmodule(submodule) {
        if (!await this.checkSubmoduleExists(submodule)) {
            this.log(`❌ ${submodule.name} directory not found at ${submodule.path}`, '\x1b[31m');
            return false;
        }

        await this.ensureSubmoduleSetup(submodule);
        
        this.log(`🚀 Starting ${submodule.name} on port ${submodule.port}...`, submodule.color);
        
        const process = spawn('npm', ['run', 'dev'], {
            cwd: submodule.path,
            stdio: ['ignore', 'pipe', 'pipe'],
            shell: true
        });

        process.stdout.on('data', (data) => {
            const output = data.toString().trim();
            if (output) {
                console.log(`${submodule.color}[${submodule.name}]${'\x1b[0m'} ${output}`);
            }
        });

        process.stderr.on('data', (data) => {
            const output = data.toString().trim();
            if (output && !output.includes('ENOTDIR')) {
                console.log(`${submodule.color}[${submodule.name}]${'\x1b[0m'} ${output}`);
            }
        });

        process.on('close', (code) => {
            if (code !== null) {
                this.log(`${submodule.name} exited with code ${code}`, '\x1b[33m');
            }
        });

        this.processes.push({ name: submodule.name, process });
        return true;
    }

    async startAll() {
        this.log('🏠 Home Server - Starting all submodules...', '\x1b[32m');
        
        for (const submodule of this.submodules) {
            await this.startSubmodule(submodule);
            // 서버 시작 간격
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        this.log('✅ All submodules started!', '\x1b[32m');
        this.log('📋 Running services:', '\x1b[37m');
        this.log('   • Main Web: http://localhost:5173', '\x1b[37m');
        this.submodules.forEach(sub => {
            this.log(`   • ${sub.name}: http://localhost:${sub.port}`, sub.color);
        });
        this.log('   • API Backend: http://localhost:5000', '\x1b[37m');
    }

    cleanup() {
        this.log('🛑 Shutting down submodules...', '\x1b[33m');
        this.processes.forEach(({ name, process }) => {
            this.log(`Stopping ${name}...`, '\x1b[33m');
            process.kill('SIGTERM');
        });
    }
}

const manager = new SubmoduleManager();

// 프로세스 종료 시 정리
process.on('SIGINT', () => {
    manager.cleanup();
    process.exit(0);
});

process.on('SIGTERM', () => {
    manager.cleanup();
    process.exit(0);
});

// 서브모듈들 시작
manager.startAll().catch(console.error);