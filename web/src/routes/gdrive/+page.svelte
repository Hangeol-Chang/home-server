<script>
	import { listFiles, getFileMeta, getFileContentUrl, getBreadcrumb } from '$lib/api/gdrive.js';
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
	import '$lib/styles/module.css';
	import '$lib/styles/module-common.css';

	let items = $state([]);
	let breadcrumb = $state([{ id: null, name: '홈' }]);
	let currentFolderId = $state(null);
	let nextPageToken = $state(null);
	let loading = $state(false);
	let error = $state('');

	// 미리보기 상태
	let previewFile = $state(null); // { id, name, mimeType }
	let previewUrl = $state('');

	const ICON_MAP = {
		'application/vnd.google-apps.folder': '📁',
		'application/vnd.google-apps.document': '📄',
		'application/vnd.google-apps.spreadsheet': '📊',
		'application/vnd.google-apps.presentation': '📑',
		'application/pdf': '📕',
		'image/jpeg': '🖼️',
		'image/png': '🖼️',
		'image/gif': '🖼️',
		'image/webp': '🖼️',
		'video/mp4': '🎬',
		'video/quicktime': '🎬',
		'audio/mpeg': '🎵',
		'audio/wav': '🎵',
		'text/plain': '📃',
		'application/zip': '🗜️',
	};

	function getIcon(mimeType) {
		return ICON_MAP[mimeType] ?? '📎';
	}

	function formatSize(bytes) {
		if (!bytes) return '-';
		const n = parseInt(bytes);
		if (n < 1024) return `${n} B`;
		if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
		if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
		return `${(n / 1024 ** 3).toFixed(1)} GB`;
	}

	function formatDate(iso) {
		if (!iso) return '-';
		return new Date(iso).toLocaleDateString('ko-KR', {
			year: 'numeric', month: '2-digit', day: '2-digit'
		});
	}

	async function loadFolder(folderId, resetBreadcrumb = false) {
		loading = true;
		error = '';
		items = [];
		nextPageToken = null;
		currentFolderId = folderId;

		try {
			const res = await listFiles(folderId);
			items = res.items;
			nextPageToken = res.nextPageToken ?? null;

			if (resetBreadcrumb) {
				breadcrumb = [{ id: null, name: '홈' }];
			}
		} catch (e) {
			error = e.message ?? '파일 목록을 불러오는 데 실패했습니다.';
		} finally {
			loading = false;
		}
	}

	async function openFolder(folder) {
		// breadcrumb에 추가
		breadcrumb = [...breadcrumb, { id: folder.id, name: folder.name }];
		await loadFolder(folder.id);
	}

	async function navigateTo(index) {
		const crumb = breadcrumb[index];
		breadcrumb = breadcrumb.slice(0, index + 1);
		await loadFolder(crumb.id);
	}

	async function loadMore() {
		if (!nextPageToken) return;
		loading = true;
		try {
			const res = await listFiles(currentFolderId, nextPageToken);
			items = [...items, ...res.items];
			nextPageToken = res.nextPageToken ?? null;
		} catch (e) {
			error = e.message ?? '추가 로드 실패';
		} finally {
			loading = false;
		}
	}

	function openPreview(file) {
		previewFile = file;
		previewUrl = getFileContentUrl(file.id);
	}

	function closePreview() {
		previewFile = null;
		previewUrl = '';
	}

	function isPreviewable(mimeType) {
		return (
			mimeType?.startsWith('image/') ||
			mimeType === 'application/pdf' ||
			mimeType?.startsWith('text/')
		);
	}

	onMount(() => loadFolder(null, true));
</script>

<svelte:head>
	<title>Google Drive - Home Server</title>
</svelte:head>

<div class="module-page" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
	<div class="module-header">
		<h1 class="module-title">
			<span class="module-icon">☁️</span> Google Drive
		</h1>
	</div>

	<!-- Breadcrumb -->
	<nav class="breadcrumb">
		{#each breadcrumb as crumb, i}
			{#if i < breadcrumb.length - 1}
				<button class="crumb-btn" onclick={() => navigateTo(i)}>{crumb.name}</button>
				<span class="crumb-sep">/</span>
			{:else}
				<span class="crumb-current">{crumb.name}</span>
			{/if}
		{/each}
	</nav>

	<!-- Error -->
	{#if error}
		<div class="error-banner">{error}</div>
	{/if}

	<!-- File list -->
	<div class="file-list module-container">
		{#if loading && items.length === 0}
			<div class="loading-state">불러오는 중...</div>
		{:else if items.length === 0 && !loading}
			<div class="empty-state">파일이 없습니다.</div>
		{:else}
			<table class="file-table">
				<thead>
					<tr>
						<th class="col-name">이름</th>
						<th class="col-date">수정일</th>
						<th class="col-size">크기</th>
						<th class="col-action"></th>
					</tr>
				</thead>
				<tbody>
					{#each items as item (item.id)}
						<tr class="file-row" class:folder={item.isFolder}>
							<td class="col-name">
								{#if item.isFolder}
									<button class="item-btn folder-btn" onclick={() => openFolder(item)}>
										<span class="item-icon">{getIcon(item.mimeType)}</span>
										<span class="item-name">{item.name}</span>
									</button>
								{:else}
									<button
										class="item-btn file-btn"
										onclick={() => openPreview(item)}
										disabled={!isPreviewable(item.mimeType)}
									>
										<span class="item-icon">{getIcon(item.mimeType)}</span>
										<span class="item-name">{item.name}</span>
									</button>
								{/if}
							</td>
							<td class="col-date">{formatDate(item.modifiedTime)}</td>
							<td class="col-size">{formatSize(item.size)}</td>
							<td class="col-action">
								{#if !item.isFolder}
									<a
										href={getFileContentUrl(item.id)}
										download={item.name}
										class="download-btn"
										title="다운로드"
									>⬇</a>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>

			{#if nextPageToken}
				<div class="load-more">
					<button class="load-more-btn" onclick={loadMore} disabled={loading}>
						{loading ? '로딩 중...' : '더 보기'}
					</button>
				</div>
			{/if}
		{/if}
	</div>
</div>

<!-- Preview Modal -->
{#if previewFile}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div role="none" class="preview-overlay" onclick={closePreview}>
		<div class="preview-modal" onclick={(e) => e.stopPropagation()}>
			<div class="preview-header">
				<span class="preview-title">{previewFile.name}</span>
				<div class="preview-actions">
					<a href={previewUrl} download={previewFile.name} class="preview-download-btn">⬇ 다운로드</a>
					<button class="preview-close-btn" onclick={closePreview}>✕</button>
				</div>
			</div>
			<div class="preview-body">
				{#if previewFile.mimeType?.startsWith('image/')}
					<img src={previewUrl} alt={previewFile.name} class="preview-image" />
				{:else if previewFile.mimeType === 'application/pdf' || previewFile.mimeType?.startsWith('application/vnd.google-apps.')}
					<iframe src={previewUrl} title={previewFile.name} class="preview-iframe"></iframe>
				{:else}
					<div class="preview-unsupported">미리보기를 지원하지 않는 형식입니다.</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.module-page {
		padding: 24px;
		max-width: 1200px;
		margin: 0 auto;
	}

	.module-header {
		margin-bottom: 16px;
	}

	.module-title {
		font-size: 1.5rem;
		font-weight: 700;
		display: flex;
		align-items: center;
		gap: 8px;
		margin: 0;
	}

	.module-icon {
		font-size: 1.4rem;
	}

	/* Breadcrumb */
	.breadcrumb {
		display: flex;
		align-items: center;
		gap: 4px;
		font-size: 0.9rem;
		margin-bottom: 16px;
		flex-wrap: wrap;
	}

	.crumb-btn {
		background: none;
		border: none;
		color: var(--primary-color, #6366f1);
		cursor: pointer;
		padding: 2px 4px;
		border-radius: 4px;
		font-size: inherit;
	}
	.crumb-btn:hover { text-decoration: underline; }

	.crumb-sep { color: var(--text-muted, #888); }
	.crumb-current { color: var(--text-color, #222); font-weight: 500; }

	/* Error */
	.error-banner {
		background: #fee;
		border: 1px solid #f99;
		border-radius: 6px;
		padding: 12px 16px;
		color: #c00;
		margin-bottom: 16px;
		font-size: 0.9rem;
	}

	/* File table */
	.file-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.92rem;
	}

	.file-table th {
		text-align: left;
		padding: 10px 12px;
		border-bottom: 2px solid var(--border-color, #e5e7eb);
		color: var(--text-muted, #888);
		font-weight: 600;
		white-space: nowrap;
	}

	.file-row td {
		padding: 8px 12px;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
		vertical-align: middle;
	}

	.file-row:hover td { background: var(--hover-bg, rgba(99, 102, 241, 0.04)); }

	.col-name { width: 100%; }
	.col-date { white-space: nowrap; color: var(--text-muted, #888); min-width: 90px; }
	.col-size { white-space: nowrap; color: var(--text-muted, #888); min-width: 70px; text-align: right; }
	.col-action { min-width: 40px; text-align: center; }

	.item-btn {
		background: none;
		border: none;
		display: flex;
		align-items: center;
		gap: 8px;
		cursor: pointer;
		padding: 2px 0;
		font-size: inherit;
		text-align: left;
		width: 100%;
	}

	.folder-btn { color: var(--primary-color, #6366f1); font-weight: 500; }
	.folder-btn:hover .item-name { text-decoration: underline; }

	.file-btn { color: var(--text-color, #222); }
	.file-btn:not([disabled]):hover .item-name { text-decoration: underline; }
	.file-btn[disabled] { cursor: default; opacity: 0.85; }

	.item-icon { font-size: 1.1rem; flex-shrink: 0; }

	.download-btn {
		color: var(--text-muted, #888);
		text-decoration: none;
		font-size: 1rem;
		padding: 2px 6px;
		border-radius: 4px;
	}
	.download-btn:hover { background: var(--hover-bg, rgba(99,102,241,0.08)); }

	/* Load more */
	.load-more { display: flex; justify-content: center; padding: 16px 0 0; }
	.load-more-btn {
		padding: 8px 24px;
		border: 1px solid var(--border-color, #e5e7eb);
		border-radius: 6px;
		background: none;
		cursor: pointer;
		font-size: 0.9rem;
	}
	.load-more-btn:hover:not([disabled]) { background: var(--hover-bg, rgba(99,102,241,0.06)); }
	.load-more-btn[disabled] { opacity: 0.5; cursor: not-allowed; }

	.loading-state, .empty-state {
		padding: 40px;
		text-align: center;
		color: var(--text-muted, #888);
	}

	/* Preview Modal */
	.preview-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0,0,0,0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.preview-modal {
		background: var(--card-bg, #fff);
		border-radius: 10px;
		width: 90vw;
		max-width: 1000px;
		height: 85vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 0 20px 60px rgba(0,0,0,0.3);
	}

	.preview-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 14px 20px;
		border-bottom: 1px solid var(--border-color, #e5e7eb);
		gap: 12px;
	}

	.preview-title {
		font-weight: 600;
		font-size: 0.95rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.preview-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

	.preview-download-btn {
		padding: 6px 14px;
		background: var(--primary-color, #6366f1);
		color: #fff;
		border-radius: 6px;
		text-decoration: none;
		font-size: 0.85rem;
	}

	.preview-close-btn {
		background: none;
		border: none;
		font-size: 1.1rem;
		cursor: pointer;
		color: var(--text-muted, #888);
		padding: 4px 8px;
		border-radius: 4px;
	}
	.preview-close-btn:hover { background: var(--hover-bg, rgba(0,0,0,0.06)); }

	.preview-body { flex: 1; overflow: auto; }
	.preview-image { max-width: 100%; max-height: 100%; object-fit: contain; display: block; margin: auto; }
	.preview-iframe { width: 100%; height: 100%; border: none; }
	.preview-unsupported { padding: 40px; text-align: center; color: var(--text-muted, #888); }

	/* Mobile */
	.module-page.mobile { padding: 16px; }
	.module-page.mobile .file-table th.col-date,
	.module-page.mobile .file-row td.col-date,
	.module-page.mobile .file-table th.col-size,
	.module-page.mobile .file-row td.col-size { display: none; }
</style>
