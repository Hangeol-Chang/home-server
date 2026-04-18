<script>
	import { getFolders, getFiles, getFileContent, searchNotes, getVaultStats, saveNote, createFolder, pullRepository, deleteFile, deleteFolder, moveItem, renameItem } from '$lib/api/notebook.js';
	import { onMount } from 'svelte';
	import { device } from '$lib/stores/device';
	import FileTreeNode from '$lib/components/notebook/FileTreeNode.svelte';
	import TuiEditor from '$lib/components/notebook/TuiEditor.svelte';

	function focusOnMount(node) {
		node.focus();
		node.select();
	}

	let currentPath = $state('');
	let rootItems = $state([]);
	let selectedFile = $state(null);
	let fileContent = $state('');
	let stats = $state(null);
	let searchQuery = $state('');
	let searchResults = $state([]);
	let isSearching = $state(false);

	let loading = $state(false);
	let error = $state('');
	let viewMode = $state('browse');

	// Editor State
	let isCreating = $state(false);
	let editContent = $state('');
	let newFileName = $state('');
	let isSaving = $state(false);

	// 숨김 파일 표시
	let showHidden = $state(false);

	// 이름 변경 모달
	let renameModal = $state({ visible: false, item: null, value: '' });

	// 에디터 헤더 제목 인라인 편집
	let titleEditing = $state(false);
	let titleEditValue = $state('');

	// Context Menu
	let contextMenu = $state({ visible: false, x: 0, y: 0, item: null });

	onMount(async () => {
		pullRepository().then(result => {
			console.log('Git pull result:', result);
		}).catch(err => {
			console.error('Git pull failed:', err);
		});

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
				getFolders('', showHidden),
				getFiles('', showHidden)
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

	function handleFolderSelect(path) {
		currentPath = path;
	}

	async function handleFileSelect(file) {
		loading = true;
		error = '';
		isCreating = false;

		try {
			const result = await getFileContent(file.path);
			selectedFile = file;
			fileContent = result.content;
			editContent = result.content;
		} catch (err) {
			error = '파일을 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}

	async function navigateHome() {
		currentPath = '';
	}

	async function selectFile(file) {
		await handleFileSelect(file);
	}

	function handleNewFile(folderPath = null) {
		if (folderPath !== null) currentPath = folderPath;
		selectedFile = { name: 'New File', path: '' };
		fileContent = '';
		editContent = '';
		newFileName = '';
		isCreating = true;
	}

	function handleCancel() {
		if (isCreating) {
			isCreating = false;
			selectedFile = null;
		} else {
			editContent = fileContent;
		}
	}

	async function handleNewFolder(folderPath = null) {
		const basePath = folderPath !== null ? folderPath : currentPath;
		const folderName = prompt('새 폴더 이름을 입력하세요:');
		if (!folderName || !folderName.trim()) return;

		const path = basePath ? `${basePath}/${folderName.trim()}` : folderName.trim();

		loading = true;
		try {
			await createFolder(path);
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
			const path = isCreating
				? (currentPath ? `${currentPath}/${fileName}` : fileName)
				: selectedFile.path;

			const commitMessage = isCreating
				? `Create ${fullFileName}`
				: `Update ${selectedFile.name}`;

			await saveNote(path, editContent, commitMessage);

			if (isCreating) {
				await loadRoot();
			} else {
				fileContent = editContent;
			}

			isCreating = false;
			await loadStats();
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
		if (e.key === 'Enter') handleSearch();
	}

	function clearSearch() {
		searchQuery = '';
		searchResults = [];
		viewMode = 'browse';
	}

	// ===== Drag & Drop =====
	let rootDragOver = $state(false);

	async function handleDrop({ srcPath, destFolder }) {
		loading = true;
		try {
			await moveItem(srcPath, destFolder);
			// 이동된 파일이 현재 열린 파일이면 경로 갱신
			if (selectedFile?.path === srcPath) {
				const srcName = srcPath.split('/').pop();
				selectedFile = { ...selectedFile, path: destFolder ? `${destFolder}/${srcName}` : srcName };
			}
			await loadRoot();
		} catch (err) {
			alert('이동 실패: ' + err.message);
		} finally {
			loading = false;
		}
	}

	function handleRootDragOver(e) {
		if (!e.dataTransfer.types.includes('application/notebook-item')) return;
		e.preventDefault();
		e.dataTransfer.dropEffect = 'move';
		rootDragOver = true;
	}

	function handleRootDragLeave(e) {
		if (e.currentTarget.contains(e.relatedTarget)) return;
		rootDragOver = false;
	}

	function handleRootDrop(e) {
		e.preventDefault();
		rootDragOver = false;
		const raw = e.dataTransfer.getData('application/notebook-item');
		if (!raw) return;
		const src = JSON.parse(raw);
		if (src.path.indexOf('/') === -1) return; // 이미 루트
		handleDrop({ srcPath: src.path, destFolder: '' });
	}

	// ===== Rename =====

	async function submitRename(item, newName) {
		if (!newName.trim() || newName.trim() === item.name) return;
		loading = true;
		try {
			const result = await renameItem(item.path, newName.trim());
			if (selectedFile?.path === item.path) {
				selectedFile = { ...selectedFile, name: result.new_name, path: result.new_path };
				fileContent = editContent; // 내용 유지
			}
			await loadRoot();
		} catch (err) {
			alert('이름 변경 실패: ' + err.message);
		} finally {
			loading = false;
		}
	}

	function openRenameModal(item) {
		renameModal = { visible: true, item, value: item.name };
		closeContextMenu();
	}

	function handleRenameKeydown(e) {
		if (e.key === 'Enter') {
			submitRename(renameModal.item, renameModal.value);
			renameModal = { ...renameModal, visible: false };
		}
		if (e.key === 'Escape') renameModal = { ...renameModal, visible: false };
	}

	function startTitleEdit() {
		if (!selectedFile || isCreating) return;
		titleEditValue = selectedFile.name;
		titleEditing = true;
	}

	async function submitTitleEdit() {
		titleEditing = false;
		if (!titleEditValue.trim() || titleEditValue.trim() === selectedFile.name) return;
		await submitRename(selectedFile, titleEditValue.trim());
	}

	function handleTitleEditKeydown(e) {
		if (e.key === 'Enter') submitTitleEdit();
		if (e.key === 'Escape') titleEditing = false;
	}

	// ===== Context Menu =====

	function handleTreeContextMenu({ event, item }) {
		event.preventDefault();
		contextMenu = { visible: true, x: event.clientX, y: event.clientY, item };
	}

	function closeContextMenu() {
		contextMenu = { ...contextMenu, visible: false };
	}

	async function contextCreateFile() {
		const item = contextMenu.item;
		closeContextMenu();
		const basePath = item.type === 'folder' ? item.path : (item.folder_path || '');
		handleNewFile(basePath);
	}

	async function contextCreateFolder() {
		const item = contextMenu.item;
		closeContextMenu();
		const basePath = item.type === 'folder' ? item.path : (item.folder_path || '');
		await handleNewFolder(basePath);
	}

	async function contextDeleteItem() {
		const item = contextMenu.item;
		closeContextMenu();
		const label = item.type === 'folder' ? `폴더 "${item.name}"` : `파일 "${item.name}"`;
		if (!confirm(`${label}을(를) 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) return;

		loading = true;
		try {
			if (item.type === 'folder') {
				await deleteFolder(item.path);
			} else {
				await deleteFile(item.path);
				if (selectedFile?.path === item.path) {
					selectedFile = null;
					fileContent = '';
					editContent = '';
				}
			}
			await loadRoot();
			await loadStats();
		} catch (err) {
			alert('삭제 실패: ' + err.message);
		} finally {
			loading = false;
		}
	}

	function formatFileSize(bytes) {
		if (bytes < 1024) return bytes + ' B';
		if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
		return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
	}
</script>

<svelte:head>
	<title>Notebook - Obsidian Vault</title>
</svelte:head>

<!-- 컨텍스트 메뉴 닫기 (전역 클릭) -->
<svelte:window onclick={closeContextMenu} oncontextmenu={closeContextMenu} />

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
			<div class="search-bar">
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="파일명 검색..."
					onkeydown={handleSearchKeydown}
				/>
				<button class="btn-primary" onclick={handleSearch} disabled={isSearching || !searchQuery.trim()}>
					{isSearching ? '검색중...' : '🔍'}
				</button>
				{#if viewMode === 'search'}
					<button class="icon-btn" onclick={clearSearch}>×</button>
				{/if}
			</div>
		</div>
	</header>

	<div class="notebook-container">
		<!-- 사이드바 -->
		<aside class="sidebar" oncontextmenu={(e) => e.preventDefault()}>
			<div class="nav-actions">
				<button class="btn-primary" onclick={() => handleNewFile()}>➕ 새 파일</button>
				<button class="refresh-btn" onclick={() => handleNewFolder()}>📁 새 폴더</button>
				<button
					class="toggle-hidden-btn"
					class:active={showHidden}
					title={showHidden ? '숨김 파일 숨기기' : '숨김 파일 표시'}
					onclick={async () => { showHidden = !showHidden; await loadRoot(); }}
				>👁</button>
			</div>

			{#if viewMode === 'browse'}
				<div
					class="explorer-list"
					class:drag-over={rootDragOver}
					role="tree"
					tabindex="-1"
					ondragover={handleRootDragOver}
					ondragleave={handleRootDragLeave}
					ondrop={handleRootDrop}
				>
					{#key showHidden}
						{#each rootItems as item}
							<FileTreeNode
								{item}
								onSelectFile={handleFileSelect}
								onSelectFolder={handleFolderSelect}
								{currentPath}
								selectedFilePath={selectedFile?.path}
								onContextMenu={handleTreeContextMenu}
								{showHidden}
								onDrop={handleDrop}
							/>
						{/each}
					{/key}
				</div>

				{#if rootItems.length === 0 && !loading}
					<div class="empty-state"><p>비어있음</p></div>
				{/if}
			{:else}
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
						<div class="empty-state"><p>검색 결과가 없습니다</p></div>
					{/if}
				</div>
			{/if}
		</aside>

		<!-- 메인 컨텐츠 -->
		<main class="content-area">
			{#if loading}
				<div class="loading">
					<div class="spinner"></div>
					<p>불러오는 중...</p>
				</div>
			{:else if error}
				<div class="error-message"><p>⚠️ {error}</p></div>
			{:else if selectedFile}
				<div class="editor-container">
					<div class="editor-header">
						{#if isCreating}
							<input
								type="text"
								class="filename-input"
								bind:value={newFileName}
								placeholder="파일명 (예: new-note.md, data.csv)"
							/>
						{:else if titleEditing}
							<input
								class="title-edit-input"
								bind:value={titleEditValue}
								onblur={submitTitleEdit}
								onkeydown={handleTitleEditKeydown}
								use:focusOnMount
							/>
						{:else}
							<button
								class="editable-title"
								onclick={startTitleEdit}
								title="클릭하여 이름 변경"
							>{selectedFile.name}</button>
						{/if}
						<div class="editor-actions">
							{#if !isCreating}
								<span class="file-size">{formatFileSize(selectedFile.size || 0)}</span>
							{/if}
							<button class="btn-primary" onclick={handleSave} disabled={isSaving}>
								{isSaving ? '저장 중...' : '💾 저장'}
							</button>
						</div>
					</div>
					<div class="markdown-editor-wrapper">
						{#key selectedFile?.path || 'new'}
							<TuiEditor
								bind:value={editContent}
								height="calc(100vh - 120px)"
								previewStyle="tab"
								initialEditType="markdown"
							/>
						{/key}
					</div>
				</div>
			{:else}
				<div class="welcome-message">
					<h2>📓 Obsidian Vault</h2>
					<p>왼쪽에서 파일을 선택하거나 우클릭으로 새 파일/폴더를 만드세요.</p>
				</div>
			{/if}
		</main>
	</div>
</div>

<!-- 컨텍스트 메뉴 -->
{#if contextMenu.visible && contextMenu.item}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="context-menu"
		role="menu"
		tabindex="-1"
		style="top: {contextMenu.y}px; left: {contextMenu.x}px"
		onclick={(e) => e.stopPropagation()}
		onkeydown={(e) => { if (e.key === 'Escape') closeContextMenu(); }}
		oncontextmenu={(e) => { e.preventDefault(); e.stopPropagation(); }}
	>
		{#if contextMenu.item.type === 'folder'}
			<button class="ctx-item" onclick={contextCreateFile}>📄 새 파일</button>
			<button class="ctx-item" onclick={contextCreateFolder}>📁 새 폴더</button>
			<div class="ctx-divider"></div>
			<button class="ctx-item" onclick={() => openRenameModal(contextMenu.item)}>✏️ 이름 변경</button>
			<button class="ctx-item danger" onclick={contextDeleteItem}>🗑 폴더 삭제</button>
		{:else}
			<button class="ctx-item" onclick={contextCreateFile}>📄 같은 위치에 새 파일</button>
			<button class="ctx-item" onclick={contextCreateFolder}>📁 같은 위치에 새 폴더</button>
			<div class="ctx-divider"></div>
			<button class="ctx-item" onclick={() => openRenameModal(contextMenu.item)}>✏️ 이름 변경</button>
			<button class="ctx-item danger" onclick={contextDeleteItem}>🗑 파일 삭제</button>
		{/if}
	</div>
{/if}

<!-- 이름 변경 모달 -->
{#if renameModal.visible}
	<div
		class="rename-overlay"
		role="button"
		tabindex="-1"
		onclick={() => renameModal = { ...renameModal, visible: false }}
		onkeydown={(e) => { if (e.key === 'Escape') renameModal = { ...renameModal, visible: false }; }}
	></div>
	<div class="rename-modal">
		<p class="rename-label">이름 변경</p>
		<input
			class="rename-input"
			bind:value={renameModal.value}
			onkeydown={handleRenameKeydown}
			use:focusOnMount
		/>
		<div class="rename-actions">
			<button class="btn-primary" onclick={() => { submitRename(renameModal.item, renameModal.value); renameModal = { ...renameModal, visible: false }; }}>확인</button>
			<button class="refresh-btn" onclick={() => renameModal = { ...renameModal, visible: false }}>취소</button>
		</div>
	</div>
{/if}

<style>
	@import '$lib/styles/module.css';

	.notebook-page {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: var(--bg-primary);
		overflow: hidden;
	}

	.page-header {
		flex-shrink: 0;
		padding: 6px 12px;
		border-bottom: 1px solid var(--border-color);
	}

	.header-content {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.header-content h1 {
		margin: 0;
		font-size: 1.1rem;
		white-space: nowrap;
	}

	.stats-chips {
		display: flex;
		gap: 6px;
		flex-shrink: 0;
	}

	.chip {
		padding: 2px 8px;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 6px;
		font-size: 0.8rem;
		color: var(--text-secondary);
		white-space: nowrap;
	}

	.search-bar {
		display: flex;
		gap: 6px;
		flex: 1;
		max-width: 400px;
		margin-left: auto;
	}

	.search-bar input {
		flex: 1;
		padding: 4px 10px;
		border: 1px solid var(--border-color);
		border-radius: 6px;
		background: var(--bg-secondary);
		color: var(--text-primary);
		font-size: 0.9rem;
	}

	.notebook-container {
		flex: 1;
		display: grid;
		grid-template-columns: 260px 1fr;
		overflow: hidden;
	}

	.sidebar {
		background: var(--bg-primary);
		border-right: 1px solid var(--border-color);
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.nav-actions {
		display: flex;
		gap: 6px;
		padding: 8px;
		border-bottom: 1px solid var(--border-color);
		flex-shrink: 0;
	}

	.nav-actions button {
		flex: 1;
		font-size: 0.8rem;
		padding: 4px 6px;
	}

	.toggle-hidden-btn {
		flex: 0 0 auto !important;
		padding: 4px 8px !important;
		background: none;
		border: 1px solid var(--border-color);
		border-radius: 4px;
		cursor: pointer;
		color: var(--text-tertiary);
		font-size: 0.9rem;
		transition: all 0.15s;
	}

	.toggle-hidden-btn:hover {
		border-color: var(--color-impact-3);
		color: var(--color-impact-3);
	}

	.toggle-hidden-btn.active {
		border-color: var(--color-impact-3);
		color: var(--color-impact-3);
		background: rgba(59, 186, 156, 0.1);
	}

	.explorer-list {
		display: flex;
		flex-direction: column;
		overflow-y: auto;
		flex: 1;
		transition: background 0.1s;
	}

	.explorer-list.drag-over {
		background: rgba(59, 186, 156, 0.07);
		outline: 1px dashed var(--color-impact-3);
		outline-offset: -2px;
	}

	.explorer-item {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 4px 8px;
		background: none;
		border: 1px solid transparent;
		border-radius: 0;
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
		color: var(--color-impact-3);
		font-weight: 600;
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
		background: var(--bg-primary);
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		gap: 16px;
	}

	.spinner {
		width: 36px;
		height: 36px;
		border: 3px solid var(--border-color);
		border-top-color: var(--primary-color);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error-message {
		margin: 12px;
		padding: 12px;
		background: var(--bg-danger);
		border: 1px solid var(--text-danger);
		border-radius: 6px;
		color: var(--text-danger);
	}

	.empty-state {
		padding: 20px;
		text-align: center;
		color: var(--text-tertiary);
		font-size: 0.85rem;
	}

	.welcome-message {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: var(--text-secondary);
	}

	.welcome-message h2 {
		margin: 0 0 8px 0;
		color: var(--text-primary);
	}

	/* Editor */
	.editor-container {
		display: flex;
		flex-direction: column;
		height: 100%;
		overflow: hidden;
	}

	.editor-header {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 6px 12px;
		border-bottom: 1px solid var(--border-color);
		flex-shrink: 0;
	}

	.editor-header h2, .editable-title {
		margin: 0;
		font-size: 1rem;
		color: var(--text-primary);
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.filename-input {
		flex: 1;
		max-width: 280px;
		padding: 4px 10px;
		border: 1px solid var(--border-color);
		border-radius: 4px;
		background: var(--bg-secondary);
		color: var(--text-primary);
		font-size: 0.95rem;
	}

.editor-actions {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-left: auto;
	}

	.file-size {
		font-size: 0.8rem;
		color: var(--text-tertiary);
	}

	.markdown-editor-wrapper {
		flex: 1;
		overflow: hidden;
	}

	/* Context Menu */
	.context-menu {
		position: fixed;
		z-index: 1000;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 6px;
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
		padding: 4px;
		min-width: 180px;
	}

	.ctx-item {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		padding: 6px 10px;
		background: none;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		text-align: left;
		font-size: 0.875rem;
		color: var(--text-primary);
		transition: background 0.1s;
	}

	.ctx-item:hover {
		background: var(--bg-tertiary);
	}

	.ctx-item.danger {
		color: var(--text-danger, #e74c3c);
	}

	.ctx-item.danger:hover {
		background: rgba(231, 76, 60, 0.1);
	}

	.ctx-divider {
		height: 1px;
		background: var(--border-color);
		margin: 4px 0;
	}

	/* Editable title */
	.editable-title {
		background: none;
		border: none;
		padding: 2px 4px;
		border-radius: 4px;
		cursor: text;
		text-align: left;
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-primary);
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.editable-title:hover {
		background: var(--bg-tertiary);
	}

	.title-edit-input {
		flex: 1;
		padding: 2px 8px;
		border: 1px solid var(--color-impact-3);
		border-radius: 4px;
		background: var(--bg-primary);
		color: var(--text-primary);
		font-size: 1rem;
		font-weight: 600;
		outline: none;
	}

	/* Rename modal */
	.rename-overlay {
		position: fixed;
		inset: 0;
		z-index: 1000;
		background: rgba(0, 0, 0, 0.3);
	}

	.rename-modal {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		z-index: 1001;
		background: var(--bg-secondary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		padding: 20px;
		min-width: 320px;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
	}

	.rename-label {
		margin: 0 0 10px;
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--text-primary);
	}

	.rename-input {
		width: 100%;
		padding: 8px 12px;
		border: 1px solid var(--border-color);
		border-radius: 6px;
		background: var(--bg-primary);
		color: var(--text-primary);
		font-size: 0.95rem;
		box-sizing: border-box;
		outline: none;
	}

	.rename-input:focus {
		border-color: var(--color-impact-3);
	}

	.rename-actions {
		display: flex;
		gap: 8px;
		justify-content: flex-end;
		margin-top: 12px;
	}

	/* Responsive */
	.notebook-page {
		&.tablet, &.mobile {
			.notebook-container {
				grid-template-columns: 1fr;
				grid-template-rows: 200px 1fr;
			}

			.sidebar {
				border-right: none;
				border-bottom: 1px solid var(--border-color);
			}
		}
	}
</style>
