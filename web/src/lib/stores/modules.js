// src/stores/modules.js
import { writable } from 'svelte/store';

// 전역 store
const modulesStore = writable([]);
let initialized = false;

function initModules() {
    const moduleComponents = import.meta.glob('$modules/*/web/src/routes/+page.svelte');
    // console.log('Discovered module components:', Object.keys(moduleComponents));

    if (initialized) return; // 이미 초기화 했으면 패스
    initialized = true;

    // 모듈 정보 수집 로직
    const modules = [];
    for (const path in moduleComponents) {
        const moduleName = path.split('/')[3];
        const moduleInfo = {
        name: moduleName,
        displayName: moduleName.charAt(0).toUpperCase() + moduleName.slice(1).replace(/-/g, ' '),
        path: `/${moduleName}`,
        routes: []
        };
        modules.push(moduleInfo);
    }
    modulesStore.set(modules);
}

export function useModules() {
    initModules();
    return modulesStore;
}
