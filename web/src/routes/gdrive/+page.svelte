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
	let previewAspectRatio = $state(16 / 9);
	let videoEl = $state(null);
	let bufferedRanges = $state([]);
	let bufferedPercent = $state(0);
	let playedPercent = $state(0);
	let downloadSpeedText = $state('-');
	let bufferedText = $state('0% 로드');
	let lastBufferSample = $state(null); // { t, bytes }

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

	function formatBytes(bytes) {
		if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
		if (bytes < 1024) return `${bytes.toFixed(0)} B`;
		if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
		if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(2)} MB`;
		return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
	}

	function getFileSizeBytes(file) {
		const n = Number.parseInt(file?.size ?? '', 10);
		return Number.isFinite(n) ? Math.max(0, n) : 0;
	}

	function getMergedBufferedRanges(video) {
		const ranges = [];
		for (let i = 0; i < video.buffered.length; i++) {
			ranges.push({ start: video.buffered.start(i), end: video.buffered.end(i) });
		}
		ranges.sort((a, b) => a.start - b.start);

		const merged = [];
		for (const r of ranges) {
			const last = merged[merged.length - 1];
			if (!last || r.start > last.end + 0.01) merged.push({ ...r });
			else last.end = Math.max(last.end, r.end);
		}
		return merged;
	}

	function updateVideoBufferState() {
		if (!videoEl || !Number.isFinite(videoEl.duration) || videoEl.duration <= 0) {
			bufferedRanges = [];
			bufferedPercent = 0;
			playedPercent = 0;
			bufferedText = '0% 로드';
			downloadSpeedText = '-';
			lastBufferSample = null;
			return;
		}

		const duration = videoEl.duration;
		const merged = getMergedBufferedRanges(videoEl);
		let totalBufferedSeconds = 0;

		bufferedRanges = merged.map((r) => {
			totalBufferedSeconds += Math.max(0, r.end - r.start);
			return {
				left: (Math.max(0, r.start) / duration) * 100,
				width: (Math.max(0, r.end - r.start) / duration) * 100
			};
		});

		bufferedPercent = Math.min(100, (totalBufferedSeconds / duration) * 100);
		playedPercent = Math.min(100, (Math.max(0, videoEl.currentTime) / duration) * 100);
		bufferedText = `${bufferedPercent.toFixed(1)}% 로드`;

		const totalSize = getFileSizeBytes(previewFile);
		if (totalSize <= 0) {
			downloadSpeedText = '크기 정보 없음';
			lastBufferSample = null;
			return;
		}

		const estimatedLoadedBytes = Math.min(totalSize, (totalBufferedSeconds / duration) * totalSize);
		const now = performance.now();
		if (!lastBufferSample) {
			lastBufferSample = { t: now, bytes: estimatedLoadedBytes };
			downloadSpeedText = '측정 중...';
			return;
		}

		const dt = (now - lastBufferSample.t) / 1000;
		if (dt < 0.25) return;

		const db = Math.max(0, estimatedLoadedBytes - lastBufferSample.bytes);
		const bps = db / dt;
		downloadSpeedText = bps > 0 ? `${formatBytes(bps)}/s` : '대기 중';
		lastBufferSample = { t: now, bytes: estimatedLoadedBytes };
	}

	function updateImageAspectRatio(url) {
		const img = new Image();
		img.onload = () => {
			if (img.naturalWidth > 0 && img.naturalHeight > 0) {
				previewAspectRatio = img.naturalWidth / img.naturalHeight;
			}
		};
		img.src = url;
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

	async function openPreview(file) {
		previewFile = file;
		previewUrl = getFileContentUrl(file.id);
		previewAspectRatio = 16 / 9;
		videoEl = null;
		bufferedRanges = [];
		bufferedPercent = 0;
		playedPercent = 0;
		downloadSpeedText = '측정 중...';
		bufferedText = '0% 로드';
		lastBufferSample = null;

		if (file?.mimeType?.startsWith('image/')) {
			updateImageAspectRatio(previewUrl);
		}

		if (!file?.size) {
			try {
				const meta = await getFileMeta(file.id);
				if (meta?.size) previewFile = { ...previewFile, size: meta.size };
			} catch {
				// Keep preview open even when metadata fetch fails.
			}
		}
	}

	function closePreview() {
		previewFile = null;
		previewUrl = '';
		videoEl = null;
		bufferedRanges = [];
		bufferedPercent = 0;
		playedPercent = 0;
		downloadSpeedText = '-';
		bufferedText = '0% 로드';
		lastBufferSample = null;
	}

	function handleVideoLoadedMetadata() {
		if (videoEl?.videoWidth > 0 && videoEl?.videoHeight > 0) {
			previewAspectRatio = videoEl.videoWidth / videoEl.videoHeight;
		}
		updateVideoBufferState();
	}

	function isImage(mimeType) {
		return mimeType?.startsWith('image/');
	}

	function isVideo(mimeType) {
		return mimeType?.startsWith('video/');
	}

	function isMediaWithAspect(mimeType) {
		return isImage(mimeType) || isVideo(mimeType);
	}

	function isPreviewable(mimeType) {
		return (
			isImage(mimeType) ||
			isVideo(mimeType) ||
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
		<div
			role="none"
			class="preview-modal"
			class:media-preview={isMediaWithAspect(previewFile?.mimeType)}
			style={`--preview-aspect-ratio: ${previewAspectRatio};`}
			onclick={(e) => e.stopPropagation()}
		>
			<div class="preview-header">
				<span class="preview-title">{previewFile.name}</span>
				<div class="preview-actions">
					<a href={previewUrl} download={previewFile.name} class="preview-download-btn">⬇ 다운로드</a>
					<button class="preview-close-btn" onclick={closePreview}>✕</button>
				</div>
			</div>
			<div class="preview-body">
				{#if isImage(previewFile.mimeType)}
					<img src={previewUrl} alt={previewFile.name} class="preview-image" />
				{:else if isVideo(previewFile.mimeType)}
					<div class="preview-video-wrap">
						<video
							src={previewUrl}
							controls
							autoplay
							class="preview-video"
							bind:this={videoEl}
							onloadedmetadata={handleVideoLoadedMetadata}
							onprogress={updateVideoBufferState}
							onseeking={updateVideoBufferState}
							onseeked={updateVideoBufferState}
							ontimeupdate={updateVideoBufferState}
						>
							<track kind="captions">
							브라우저가 비디오 태그를 지원하지 않습니다.
						</video>
						<div class="buffer-panel">
							<div class="buffer-bar" role="img" aria-label={`비디오 버퍼 상태: ${bufferedText}`}>
								{#each bufferedRanges as range, idx (idx)}
									<span
										class="buffer-range"
										style={`left: ${range.left}%; width: ${range.width}%;`}
									></span>
								{/each}
								<span class="buffer-playhead" style={`left: ${playedPercent}%;`}></span>
							</div>
							<div class="buffer-meta">
								<span>{bufferedText}</span>
								<span>다운로드 속도: {downloadSpeedText}</span>
							</div>
						</div>
					</div>
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
		color: var(--primary-color);
		cursor: pointer;
		padding: 2px 4px;
		border-radius: 2px;
		font-size: inherit;
	}
	.crumb-btn:hover { text-decoration: underline; }

	.crumb-sep { color: var(--text-tertiary); }
	.crumb-current { color: var(--text-primary); font-weight: 500; }

	/* Error */
	.error-banner {
		background: var(--bg-danger);
		border: 1px solid color-mix(in srgb, var(--text-danger), white 65%);
		border-radius: 4px;
		padding: 12px 16px;
		color: var(--text-danger);
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
		border-bottom: 2px solid var(--border-color);
		color: var(--text-secondary);
		font-weight: 600;
		white-space: nowrap;
	}

	.file-row td {
		padding: 8px 12px;
		border-bottom: 1px solid var(--border-color);
		vertical-align: middle;
	}

	.file-row:hover td { background: var(--bg-tertiary); }

	.col-name { width: 100%; }
	.col-date { white-space: nowrap; color: var(--text-tertiary); min-width: 90px; }
	.col-size { white-space: nowrap; color: var(--text-tertiary); min-width: 70px; text-align: right; }
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

	.folder-btn { color: var(--text-info); font-weight: 500; }
	.folder-btn:hover .item-name { text-decoration: underline; }

	.file-btn { color: var(--text-primary); }
	.file-btn:not([disabled]):hover .item-name { text-decoration: underline; }
	.file-btn[disabled] { cursor: default; opacity: 0.85; }

	.item-icon { font-size: 1.1rem; flex-shrink: 0; }

	.download-btn {
		color: var(--text-secondary);
		text-decoration: none;
		font-size: 1rem;
		padding: 2px 6px;
		border-radius: 2px;
	}
	.download-btn:hover { background: var(--bg-tertiary); }

	/* Load more */
	.load-more { display: flex; justify-content: center; padding: 16px 0 0; }
	.load-more-btn {
		padding: 8px 24px;
		border: 1px solid var(--border-color);
		border-radius: 2px;
		background: var(--bg-white);
		color: var(--text-primary);
		cursor: pointer;
		font-size: 0.9rem;
	}
	.load-more-btn:hover:not([disabled]) { background: var(--bg-tertiary); }
	.load-more-btn[disabled] { opacity: 0.5; cursor: not-allowed; }

	.loading-state, .empty-state {
		padding: 40px;
		text-align: center;
		color: var(--text-tertiary);
	}

	/* Preview Modal */
	.preview-overlay {
		position: fixed;
		inset: 0;
		background: color-mix(in srgb, var(--color-main-1), transparent 40%);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.preview-modal {
		background: var(--bg-white);
		border-radius: 4px;
		width: 90vw;
		max-width: 1000px;
		height: 85vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: var(--shadow-lg);
	}

	.preview-modal.media-preview {
		width: min(90vw, calc(85vh * var(--preview-aspect-ratio)));
		height: min(85vh, calc(90vw / var(--preview-aspect-ratio)));
	}

	.preview-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 14px 20px;
		border-bottom: 1px solid var(--border-color);
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
		background: var(--button-bg);
		color: var(--button-text);
		border-radius: 2px;
		text-decoration: none;
		font-size: 0.85rem;
	}

	.preview-close-btn {
		background: none;
		border: none;
		font-size: 1.1rem;
		cursor: pointer;
		color: var(--text-secondary);
		padding: 4px 8px;
		border-radius: 2px;
	}
	.preview-close-btn:hover { background: var(--bg-tertiary); }

	.preview-body {
		flex: 1;
		overflow: auto;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.preview-image { width: 100%; height: 100%; object-fit: contain; }

	.preview-video-wrap {
		width: 100%;
		height: 100%;
		display: grid;
		grid-template-rows: minmax(0, 1fr) auto;
	}

	.preview-video {
		width: 100%;
		height: 100%;
		max-height: 100%;
		background: var(--color-main-1);
		object-fit: contain;
	}

	.buffer-panel {
		padding: 10px 14px 12px;
		border-top: 1px solid var(--border-color);
		background: var(--bg-primary);
	}

	.buffer-bar {
		position: relative;
		height: 8px;
		border-radius: 4px;
		background: var(--bg-tertiary-dark);
		overflow: hidden;
	}

	.buffer-range {
		position: absolute;
		top: 0;
		height: 100%;
		background: var(--bg-info);
	}

	.buffer-playhead {
		position: absolute;
		top: -2px;
		bottom: -2px;
		width: 2px;
		background: var(--text-primary);
		transform: translateX(-50%);
	}

	.buffer-meta {
		margin-top: 8px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		font-size: 0.8rem;
		color: var(--text-secondary);
	}
	.preview-iframe { width: 100%; height: 100%; border: none; }
	.preview-unsupported { padding: 40px; text-align: center; color: var(--text-tertiary); }

	/* Mobile */
	.module-page.mobile { padding: 16px; }
	.module-page.mobile .file-table th.col-date,
	.module-page.mobile .file-row td.col-date,
	.module-page.mobile .file-table th.col-size,
	.module-page.mobile .file-row td.col-size { display: none; }

	@media (max-width: 767px) {
		.preview-modal.media-preview {
			width: 95vw;
			height: min(80vh, calc(95vw / var(--preview-aspect-ratio)));
		}

		.buffer-meta {
			flex-direction: column;
			align-items: flex-start;
			gap: 4px;
		}
	}
</style>
