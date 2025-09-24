// main/src/lib/routes.js

// Vite의 import.meta.glob을 사용해서 모든 submodule의 routes.js를 가져옴
const modules = import.meta.glob('../../../../modules/*/web/src/routes.js', { eager: true });

let allRoutes = [];
for (const path in modules) {
    const mod = modules[path];
    if (mod.default) {
        allRoutes = allRoutes.concat(mod.default);
    }
}

export const routes = allRoutes;