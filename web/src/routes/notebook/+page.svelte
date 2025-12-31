<script>
	import { getFolders, getFiles, getFileContent, searchNotes, getVaultStats, saveNote, createFolder } from '$lib/api/notebook.js';
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
	import FileTreeNode from './FileTreeNode.svelte';

	let currentPath = $state('');
	let rootItems = $state([]); // Root level items
	let selectedFile = $state(null);
	let fileContent = $state('');
	let stats = $state(null);
	let searchQuery = $state('');
	let searchResults = $state([]);
	let isSearching = $state(false);
	
	let loading = $state(false);
	let error = $state('');
	let viewMode = $state('browse'); // 'browse' or 'search'

	// Editor State
	let isEditing = $state(false);
	let isCreating = $state(false);
	let editContent = $state('');
	let newFileName = $state('');
	let isSaving = $state(false);

	// 경로 히스토리
	let pathHistory = $state([]);

	onMount(async () => {
		await loadStats();
		await loadRoot();
	});

	async function loadStats() {
		try {
			stats = await getVaultStats();
		} catch (err) {
			console.error('통계 로드 실패:', err);
		}
	}

	async function loadRoot() {
		loading = true;
		error = '';
		
		try {
			const [folders, files] = await Promise.all([
				getFolders(''),
				getFiles('')
			]);
			
			rootItems = [
				...folders.map(f => ({ ...f, type: 'folder' })),
				...files.map(f => ({ ...f, type: 'file' }))
			];
			
			viewMode = 'browse';
		} catch (err) {
			error = '폴더를 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	// 트리에서 폴더 선택 시 호출
	function handleFolderSelect(path) {
		currentPath = path;
	}

	// 트리에서 파일 선택 시 호출
	async function handleFileSelect(file) {
		loading = true;
		error = '';
		isEditing = false;
		isCreating = false;
		
		try {
			const result = await getFileContent(file.path);
			selectedFile = file;
			fileContent = result.content;
			// 파일 선택 시 currentPath는 해당 파일의 부모 폴더로 설정 (선택적)
			// currentPath = file.folder_path; 
		} catch (err) {
			error = '파일을 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	// 기존 navigateToFolder, navigateBack 등은 트리 구조에서는 사용하지 않거나 다르게 동작해야 함
	// 하지만 "새 파일/폴더" 기능을 위해 currentPath 관리는 필요함
	
	async function navigateHome() {
		currentPath = '';
		// 트리를 접거나 초기화하는 로직이 필요할 수 있음
	}

	// selectFile 함수 대체
	async function selectFile(file) {
		await handleFileSelect(file);
	}

	function handleEdit() {
		editContent = fileContent;
		isEditing = true;
	}

	function handleNewFile() {
		selectedFile = null;
		fileContent = '';
		editContent = '';
		newFileName = '';
		isCreating = true;
		isEditing = true;
	}

	function handleCancel() {
		if (isCreating) {
			isCreating = false;
			isEditing = false;
			selectedFile = null;
		} else {
			isEditing = false;
			editContent = '';
		}
	}

	async function handleNewFolder() {
		const folderName = prompt('새 폴더 이름을 입력하세요:');
		if (!folderName || !folderName.trim()) return;

		const path = currentPath ? `${currentPath}/${folderName}` : folderName;
		
		loading = true;
		try {
			await createFolder(path);
			// 전체 리로드 대신 최적화 가능하지만, 일단 루트 리로드로 단순화 (트리 상태 유지 안됨)
			// 트리 상태 유지를 위해서는 복잡한 로직 필요
			await loadRoot(); 
			await loadStats();
		} catch (err) {
			alert('폴더 생성 실패: ' + err.message);
		} finally {
			loading = false;
		}
	}

	async function handleSave() {
		if (isCreating && !newFileName.trim()) {
			alert('파일명을 입력해주세요.');
			return;
		}

		isSaving = true;
		try {
			const fileName = isCreating ? newFileName : selectedFile.name;
			// 확장자가 없으면 .md 추가
			const fullFileName = fileName.toLowerCase().endsWith('.md') ? fileName : `${fileName}.md`;
			const path = isCreating 
				? (currentPath ? `${currentPath}/${fullFileName}` : fullFileName)
				: selectedFile.path;
			
			const commitMessage = isCreating 
				? `Create ${fullFileName}` 
				: `Update ${selectedFile.name}`;

			await saveNote(path, editContent, commitMessage);
			
			// 저장 후 처리
			if (isCreating) {
				await loadRoot(); // 파일 목록 갱신
				// 새로 생성된 파일 선택 로직은 트리 구조에서 복잡하므로 생략하거나 개선 필요
			} else {
				// Update content
				fileContent = editContent;
				isEditing = false;
			}
			
			isCreating = false;
			isEditing = false;
			await loadStats(); // 통계 업데이트

		} catch (err) {
			alert('저장 실패: ' + err.message);
		} finally {
			isSaving = false;
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

<div class="notebook-page" class:mobile={$device.isMobile} class:tablet={$device.isTablet}>
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
				<div class="nav-actions">
					<button class="nav-btn primary" onclick={handleNewFile}>
						➕ 새 파일
					</button>
					<button class="nav-btn secondary" onclick={handleNewFolder}>
						📁 새 폴더
					</button>
				</div>
			</div>

			{#if viewMode === 'browse'}
				<div class="explorer-list">
					{#each rootItems as item}
						<FileTreeNode 
							{item} 
							onSelectFile={handleFileSelect}
							onSelectFolder={handleFolderSelect}
							{currentPath}
							selectedFilePath={selectedFile?.path}
						/>
					{/each}
				</div>

				{#if rootItems.length === 0 && !loading}
					<div class="empty-state">
						<p>비어있음</p>
					</div>
				{/if}
			{:else}
				<!-- 검색 결과 -->
				<div class="search-results">
					<div class="explorer-list">
						{#each searchResults as file}
							<button
								class="explorer-item file"
								class:active={selectedFile?.path === file.path}
								onclick={() => selectFile(file)}
							>
								<span class="icon">📄</span>
								<div class="search-item-info">
									<span class="name">{file.name}</span>
									<span class="path-hint">{file.folder_path || 'root'}</span>
								</div>
							</button>
						{/each}
					</div>
					{#if searchResults.length === 0}
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
			{:else if isEditing}
				<div class="editor-container">
					<div class="editor-header">
						{#if isCreating}
							<input 
								type="text" 
								class="filename-input" 
								bind:value={newFileName} 
								placeholder="파일명을 입력하세요 (예: new-note)"
							/>
							<span class="extension">.md</span>
						{:else}
							<h2>{selectedFile.name} (편집)</h2>
						{/if}
						<div class="editor-actions">
							<button class="cancel-btn" onclick={handleCancel} disabled={isSaving}>취소</button>
							<button class="save-btn" onclick={handleSave} disabled={isSaving}>
								{isSaving ? '저장 중...' : '💾 저장'}
							</button>
						</div>
					</div>
					<textarea 
						class="markdown-editor" 
						bind:value={editContent}
						placeholder="내용을 입력하세요..."
					></textarea>
				</div>
			{:else if selectedFile}
				<div class="file-viewer">
					<div class="file-header">
						<h2>{selectedFile.name}</h2>
						<div class="file-actions">
							<button class="edit-btn" onclick={handleEdit}>✏️ 편집</button>
						</div>
					</div>
					<div class="file-details">
						<span>📁 {selectedFile.folder_path || 'root'}</span>
						<span>💾 {formatFileSize(selectedFile.size)}</span>
						<span>🕐 {formatDate(selectedFile.modified_at)}</span>
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

	.explorer-list {
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	.explorer-item {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 4px 8px;
		background: none;
		border: 1px solid transparent;
		border-radius: 4px;
		cursor: pointer;
		text-align: left;
		width: 100%;
		color: var(--text-secondary);
		font-size: 0.9rem;
		transition: all 0.1s;
	}

	.explorer-item:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
	}

	.explorer-item.active {
		background: var(--bg-tertiary);
		color: var(--primary-color);
		font-weight: 500;
	}

	.explorer-item .icon {
		font-size: 1rem;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 16px;
		flex-shrink: 0;
	}

	.explorer-item .name {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		flex: 1;
	}

	.search-item-info {
		display: flex;
		flex-direction: column;
		min-width: 0;
		flex: 1;
	}

	.path-hint {
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
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.file-actions {
		float: right;
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

	/* Editor Styles */
	.editor-container {
		display: flex;
		flex-direction: column;
		height: 100%;
		gap: 16px;
	}

	.editor-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-bottom: 16px;
		border-bottom: 1px solid var(--border-color);
	}

	.editor-header h2 {
		margin: 0;
		font-size: 1.2rem;
		color: var(--text-primary);
	}

	.filename-input {
		flex: 1;
		max-width: 300px;
		padding: 8px 12px;
		border: 1px solid var(--border-color);
		border-radius: 6px;
		background: var(--bg-primary);
		color: var(--text-primary);
		font-size: 1rem;
	}

	.extension {
		margin-left: 8px;
		color: var(--text-tertiary);
	}

	.editor-actions {
		display: flex;
		gap: 8px;
	}

	.markdown-editor {
		flex: 1;
		width: 100%;
		padding: 16px;
		border: 1px solid var(--border-color);
		border-radius: 8px;
		background: var(--bg-primary);
		color: var(--text-primary);
		font-family: 'Consolas', 'Monaco', monospace;
		font-size: 0.95rem;
		line-height: 1.6;
		resize: none;
	}

	.markdown-editor:focus {
		outline: none;
		border-color: var(--primary-color);
	}

	/* Button Styles */
	.nav-actions {
		display: flex;
		gap: 8px;
		margin-top: 8px;
	}

	.nav-btn.primary {
		background: var(--primary-color);
		color: white;
		border: none;
	}

	.nav-btn.primary:hover {
		background: var(--primary-dark);
	}

	.nav-btn.secondary {
		background: var(--bg-tertiary);
		color: var(--text-primary);
		border: 1px solid var(--border-color);
	}

	.nav-btn.secondary:hover {
		background: var(--bg-secondary);
	}

	.edit-btn, .save-btn, .cancel-btn {
		padding: 8px 16px;
		border-radius: 6px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
		border: 1px solid transparent;
	}

	.edit-btn {
		background: var(--bg-tertiary);
		color: var(--text-primary);
		border-color: var(--border-color);
	}

	.edit-btn:hover {
		background: var(--bg-secondary);
	}

	.save-btn {
		background: var(--primary-color);
		color: white;
	}

	.save-btn:hover:not(:disabled) {
		background: var(--primary-dark);
	}

	.save-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.cancel-btn {
		background: transparent;
		color: var(--text-secondary);
	}

	.cancel-btn:hover {
		background: var(--bg-tertiary);
		color: var(--text-primary);
	}

	/* Tablet/Mobile (< 768px) */
	.notebook-page {
		&.tablet {
			.notebook-container {
				grid-template-columns: 1fr;
			}

			.sidebar {
				max-height: 400px;
			}
		}

		/* Mobile (< 320px) */
		&.mobile {
			.notebook-container {
				grid-template-columns: 1fr;
			}

			.sidebar {
				max-height: 300px;
			}
		}
	}
</style>
