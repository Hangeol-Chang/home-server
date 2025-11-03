<script>
	import { getFolders, getFiles, getFileContent, searchNotes, getVaultStats } from '$lib/api/notebook.js';
	import { onMount } from 'svelte';

	let currentPath = $state('');
	let folders = $state([]);
	let files = $state([]);
	let selectedFile = $state(null);
	let fileContent = $state('');
	let stats = $state(null);
	let searchQuery = $state('');
	let searchResults = $state([]);
	let isSearching = $state(false);
	
	let loading = $state(false);
	let error = $state('');
	let viewMode = $state('browse'); // 'browse' or 'search'

	// 경로 히스토리
	let pathHistory = $state([]);

	onMount(async () => {
		await loadStats();
		await loadDirectory('');
	});

	async function loadStats() {
		try {
			stats = await getVaultStats();
		} catch (err) {
			console.error('통계 로드 실패:', err);
		}
	}

	async function loadDirectory(path) {
		loading = true;
		error = '';
		selectedFile = null;
		fileContent = '';
		
		try {
			[folders, files] = await Promise.all([
				getFolders(path),
				getFiles(path)
			]);
			currentPath = path;
			viewMode = 'browse';
		} catch (err) {
			error = '폴더를 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	async function navigateToFolder(folderPath) {
		pathHistory = [...pathHistory, currentPath];
		await loadDirectory(folderPath);
	}

	async function navigateBack() {
		if (pathHistory.length > 0) {
			const previousPath = pathHistory[pathHistory.length - 1];
			pathHistory = pathHistory.slice(0, -1);
			await loadDirectory(previousPath);
		}
	}

	async function navigateHome() {
		pathHistory = [];
		await loadDirectory('');
	}

	async function selectFile(file) {
		loading = true;
		error = '';
		
		try {
			const result = await getFileContent(file.path);
			selectedFile = file;
			fileContent = result.content;
		} catch (err) {
			error = '파일을 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	async function handleSearch() {
		if (!searchQuery.trim()) return;
		
		isSearching = true;
		error = '';
		
		try {
			const result = await searchNotes(searchQuery, currentPath, false);
			searchResults = result.files;
			viewMode = 'search';
		} catch (err) {
			error = '검색 실패: ' + err.message;
		} finally {
			isSearching = false;
		}
	}

	function handleSearchKeydown(e) {
		if (e.key === 'Enter') {
			handleSearch();
		}
	}

	function clearSearch() {
		searchQuery = '';
		searchResults = [];
		viewMode = 'browse';
	}

	function formatFileSize(bytes) {
		if (bytes < 1024) return bytes + ' B';
		if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
		return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
	}

	function formatDate(dateString) {
		const date = new Date(dateString);
		return date.toLocaleDateString('ko-KR', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getBreadcrumbs() {
		if (!currentPath) return [{ name: 'Home', path: '' }];
		const parts = currentPath.split('/');
		const breadcrumbs = [{ name: 'Home', path: '' }];
		let accumulatedPath = '';
		
		for (const part of parts) {
			accumulatedPath += (accumulatedPath ? '/' : '') + part;
			breadcrumbs.push({ name: part, path: accumulatedPath });
		}
		
		return breadcrumbs;
	}
</script>

<svelte:head>
	<title>Notebook - Obsidian Vault</title>
</svelte:head>

<div class="notebook-page">
	<header class="page-header">
		<div class="header-content">
			<h1>📓 Notebook</h1>
			{#if stats}
				<div class="stats-chips">
					<span class="chip">📄 {stats.total_files} files</span>
					<span class="chip">📁 {stats.total_folders} folders</span>
					<span class="chip">💾 {formatFileSize(stats.total_size)}</span>
				</div>
			{/if}
		</div>

		<!-- 검색 바 -->
		<div class="search-bar">
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="파일명 검색..."
				onkeydown={handleSearchKeydown}
			/>
			<button class="search-btn" onclick={handleSearch} disabled={isSearching || !searchQuery.trim()}>
				{isSearching ? '검색중...' : '🔍 검색'}
			</button>
			{#if viewMode === 'search'}
				<button class="clear-btn" onclick={clearSearch}>×</button>
			{/if}
		</div>
	</header>

	<div class="notebook-container">
		<!-- 사이드바 -->
		<aside class="sidebar">
			<!-- 네비게이션 -->
			<div class="navigation">
				<div class="breadcrumbs">
					{#each getBreadcrumbs() as crumb, i}
						{#if i > 0}
							<span class="separator">/</span>
						{/if}
						<button
							class="breadcrumb"
							class:active={crumb.path === currentPath}
							onclick={() => loadDirectory(crumb.path)}
						>
							{crumb.name}
						</button>
					{/each}
				</div>
				
				{#if pathHistory.length > 0}
					<button class="nav-btn" onclick={navigateBack}>
						← 뒤로
					</button>
				{/if}
				{#if currentPath}
					<button class="nav-btn" onclick={navigateHome}>
						🏠 홈
					</button>
				{/if}
			</div>

			{#if viewMode === 'browse'}
				<!-- 폴더 목록 -->
				{#if folders.length > 0}
					<div class="folder-section">
						<h3>📁 Folders</h3>
						<div class="folder-list">
							{#each folders as folder}
								<button class="folder-item" onclick={() => navigateToFolder(folder.path)}>
									<span class="folder-icon">📁</span>
									<div class="folder-info">
										<span class="folder-name">{folder.name}</span>
										<span class="folder-meta">
											{folder.file_count} files, {folder.folder_count} folders
										</span>
									</div>
								</button>
							{/each}
						</div>
					</div>
				{/if}

				<!-- 파일 목록 -->
				{#if files.length > 0}
					<div class="file-section">
						<h3>📄 Files ({files.length})</h3>
						<div class="file-list">
							{#each files as file}
								<button
									class="file-item"
									class:active={selectedFile?.path === file.path}
									onclick={() => selectFile(file)}
								>
									<span class="file-icon">📝</span>
									<div class="file-info">
										<span class="file-name">{file.name}</span>
										<span class="file-meta">
											{formatFileSize(file.size)} • {formatDate(file.modified_at)}
										</span>
									</div>
								</button>
							{/each}
						</div>
					</div>
				{/if}

				{#if folders.length === 0 && files.length === 0 && !loading}
					<div class="empty-state">
						<p>이 폴더는 비어있습니다</p>
					</div>
				{/if}
			{:else}
				<!-- 검색 결과 -->
				<div class="search-results">
					<h3>🔍 검색 결과 ({searchResults.length})</h3>
					{#if searchResults.length > 0}
						<div class="file-list">
							{#each searchResults as file}
								<button
									class="file-item"
									class:active={selectedFile?.path === file.path}
									onclick={() => selectFile(file)}
								>
									<span class="file-icon">📝</span>
									<div class="file-info">
										<span class="file-name">{file.name}</span>
										<span class="file-path">{file.folder_path || 'root'}</span>
										<span class="file-meta">
											{formatFileSize(file.size)} • {formatDate(file.modified_at)}
										</span>
									</div>
								</button>
							{/each}
						</div>
					{:else}
						<div class="empty-state">
							<p>검색 결과가 없습니다</p>
						</div>
					{/if}
				</div>
			{/if}
		</aside>

		<!-- 메인 컨텐츠 영역 -->
		<main class="content-area">
			{#if loading}
				<div class="loading">
					<div class="spinner"></div>
					<p>불러오는 중...</p>
				</div>
			{:else if error}
				<div class="error-message">
					<p>⚠️ {error}</p>
				</div>
			{:else if selectedFile}
				<div class="file-viewer">
					<div class="file-header">
						<h2>{selectedFile.name}</h2>
						<div class="file-details">
							<span>📁 {selectedFile.folder_path || 'root'}</span>
							<span>💾 {formatFileSize(selectedFile.size)}</span>
							<span>🕐 {formatDate(selectedFile.modified_at)}</span>
						</div>
					</div>
					<div class="markdown-content">
						<pre>{fileContent}</pre>
					</div>
				</div>
			{:else}
				<div class="welcome-message">
					<h2>📓 Obsidian Vault</h2>
					<p>왼쪽에서 파일을 선택하여 내용을 확인하세요</p>
					<div class="quick-tips">
						<h3>💡 Quick Tips</h3>
						<ul>
							<li>폴더를 클릭하여 탐색하세요</li>
							<li>파일을 클릭하여 내용을 확인하세요</li>
							<li>검색 기능으로 빠르게 파일을 찾으세요</li>
						</ul>
					</div>
				</div>
			{/if}
		</main>
	</div>
</div>

<style>
	.notebook-page {
		min-height: 100vh;
		background: var(--bg-primary);
		padding: 20px;
	}

	.page-header {
		max-width: 1400px;
		margin: 0 auto 24px;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;
	}

	.header-content h1 {
		margin: 0;
		color: var(--text-primary);
	}

	.stats-chips {
		display: flex;
		gap: 8px;
	}

	.chip {
		padding: 6px 12px;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 16px;
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.search-bar {
		display: flex;
		gap: 8px;
		max-width: 600px;
	}

	.search-bar input {
		flex: 1;
		padding: 10px 16px;
		border: 1px solid var(--border-color);
		border-radius: 8px;
		background: var(--bg-secondary);
		color: var(--text-primary);
		font-size: 1rem;
	}

	.search-btn, .clear-btn {
		padding: 10px 20px;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.2s;
	}

	.search-btn {
		background: var(--primary-color);
		color: white;
	}

	.search-btn:hover:not(:disabled) {
		background: var(--primary-dark);
	}

	.search-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.clear-btn {
		background: var(--bg-tertiary);
		color: var(--text-secondary);
	}

	.notebook-container {
		max-width: 1400px;
		margin: 0 auto;
		display: grid;
		grid-template-columns: 350px 1fr;
		gap: 24px;
		min-height: calc(100vh - 200px);
	}

	.sidebar {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 12px;
		padding: 20px;
		overflow-y: auto;
		max-height: calc(100vh - 200px);
	}

	.navigation {
		margin-bottom: 20px;
		padding-bottom: 16px;
		border-bottom: 1px solid var(--border-color);
	}

	.breadcrumbs {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px;
		margin-bottom: 12px;
		font-size: 0.9rem;
	}

	.breadcrumb {
		background: none;
		border: none;
		padding: 4px 8px;
		cursor: pointer;
		color: var(--text-secondary);
		border-radius: 4px;
		transition: all 0.2s;
	}

	.breadcrumb:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
	}

	.breadcrumb.active {
		color: var(--primary-color);
		font-weight: 600;
	}

	.separator {
		color: var(--text-tertiary);
	}

	.nav-btn {
		width: 100%;
		padding: 8px 12px;
		background: var(--bg-tertiary);
		border: 1px solid var(--border-color);
		border-radius: 6px;
		cursor: pointer;
		color: var(--text-primary);
		text-align: left;
		margin-bottom: 8px;
		transition: all 0.2s;
	}

	.nav-btn:hover {
		background: var(--bg-primary);
	}

	.folder-section, .file-section, .search-results {
		margin-bottom: 24px;
	}

	.folder-section h3, .file-section h3, .search-results h3 {
		margin: 0 0 12px 0;
		font-size: 0.95rem;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.folder-list, .file-list {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.folder-item, .file-item {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 10px 12px;
		background: none;
		border: 1px solid transparent;
		border-radius: 8px;
		cursor: pointer;
		text-align: left;
		transition: all 0.2s;
		width: 100%;
	}

	.folder-item:hover, .file-item:hover {
		background: var(--bg-tertiary);
		border-color: var(--border-color);
	}

	.file-item.active {
		background: var(--primary-color);
		color: white;
	}

	.file-item.active .file-meta,
	.file-item.active .file-path {
		color: rgba(255, 255, 255, 0.8);
	}

	.folder-icon, .file-icon {
		font-size: 1.5rem;
		flex-shrink: 0;
	}

	.folder-info, .file-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 4px;
		min-width: 0;
	}

	.folder-name, .file-name {
		font-weight: 500;
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.folder-meta, .file-meta, .file-path {
		font-size: 0.75rem;
		color: var(--text-tertiary);
	}

	.content-area {
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 12px;
		padding: 24px;
		overflow-y: auto;
		max-height: calc(100vh - 200px);
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 60px 20px;
		gap: 16px;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid var(--border-color);
		border-top-color: var(--primary-color);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error-message {
		padding: 20px;
		background: #fee;
		border: 1px solid #fcc;
		border-radius: 8px;
		color: #c33;
	}

	.empty-state {
		padding: 40px 20px;
		text-align: center;
		color: var(--text-tertiary);
	}

	.welcome-message {
		padding: 40px 20px;
		text-align: center;
	}

	.welcome-message h2 {
		margin: 0 0 12px 0;
		color: var(--text-primary);
	}

	.welcome-message p {
		color: var(--text-secondary);
		margin-bottom: 32px;
	}

	.quick-tips {
		max-width: 400px;
		margin: 0 auto;
		text-align: left;
		background: var(--bg-tertiary);
		padding: 20px;
		border-radius: 8px;
	}

	.quick-tips h3 {
		margin: 0 0 12px 0;
		color: var(--text-primary);
	}

	.quick-tips ul {
		margin: 0;
		padding-left: 20px;
		color: var(--text-secondary);
	}

	.quick-tips li {
		margin-bottom: 8px;
	}

	.file-viewer {
		height: 100%;
	}

	.file-header {
		margin-bottom: 24px;
		padding-bottom: 16px;
		border-bottom: 1px solid var(--border-color);
	}

	.file-header h2 {
		margin: 0 0 8px 0;
		color: var(--text-primary);
	}

	.file-details {
		display: flex;
		gap: 16px;
		font-size: 0.85rem;
		color: var(--text-tertiary);
	}

	.markdown-content {
		line-height: 1.6;
		color: var(--text-primary);
	}

	.markdown-content pre {
		margin: 0;
		white-space: pre-wrap;
		word-wrap: break-word;
		font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
		font-size: 0.95rem;
	}

	@media (max-width: 1024px) {
		.notebook-container {
			grid-template-columns: 1fr;
		}

		.sidebar {
			max-height: 400px;
		}
	}
</style>
