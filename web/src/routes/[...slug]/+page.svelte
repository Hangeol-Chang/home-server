<script>
    import { page } from '$app/stores';

    let Component = null;
    let error = null;
    let loading = true;
    let debugInfo = [];

    // 상대 경로를 사용해서 모듈 컴포넌트들을 가져오기
    const moduleComponents = import.meta.glob('../../../../../modules/*/web/src/routes/**/+page.svelte');

    async function loadComponent(slug) {
        loading = true;
        error = null;
        Component = null;
        
        // 디버그 정보 수집
        debugInfo = Object.keys(moduleComponents);

        if (!slug || slug.length === 0) {
        loading = false;
        return;
        }

        const [moduleName, ...routeParts] = slug;

        let possiblePaths = [];
        
        if (routeParts.length > 0) {
        // 하위 경로가 있는 경우: /asset-manager/analytics
        possiblePaths.push(`../../../../../modules/${moduleName}/web/src/routes/${routeParts.join('/')}/+page.svelte`);
        }
        
        // 모듈의 메인 페이지: /asset-manager
        possiblePaths.push(`../../../../../modules/${moduleName}/web/src/routes/+page.svelte`);

        console.log('Trying paths:', possiblePaths);
        console.log('Available paths:', debugInfo);

        for (const path of possiblePaths) {
        console.log('Checking path:', path);
        if (moduleComponents[path]) {
            console.log('Found path:', path);
            try {
            const module = await moduleComponents[path]();
            Component = module.default;
            console.log('Successfully loaded component:', Component);
            break;
            } catch (e) {
            console.error('Load error:', e);
            error = `로드 실패: ${path} - ${e.message}`;
            }
        }
        }

        if (!Component && !error) {
        error = `페이지 없음: /${slug.join('/')}`;
        }

        loading = false;
    }

    $: loadComponent($page.params.slug ? $page.params.slug.split('/') : []);
</script>

{#if loading}
    <p>로딩 중...</p>
    {:else if error}
    <div>
        <p style="color: red;">{error}</p>
        <h3>디버그 정보:</h3>
        <p>현재 경로: /{$page.params.slug || ''}</p>
        <p>사용 가능한 모듈 경로들:</p>
        <ul>
        {#each debugInfo as path}
            <li><code>{path}</code></li>
        {/each}
        </ul>
    </div>
    {:else if Component}
    <svelte:component this={Component} />
    {:else}
    <div>
        <h2>홈 페이지</h2>
        <p>사용 가능한 모듈 경로들:</p>
        <ul>
        {#each debugInfo as path}
            <li><code>{path}</code></li>
        {/each}
        </ul>
    </div>
{/if}
