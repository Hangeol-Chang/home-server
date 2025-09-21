<script>
	import { onMount } from 'svelte';
	import axios from 'axios';
	
	let schedules = [];
	let tasks = [];
	let loading = true;
	let error = null;
	
	let newSchedule = {
		title: '',
		description: '',
		start_time: '',
		end_time: '',
		is_recurring: false
	};
	
	let newTask = {
		title: '',
		description: '',
		priority: 'medium',
		due_date: '',
		is_completed: false
	};
	
	async function loadData() {
		try {
			loading = true;
			const [schedulesRes, tasksRes] = await Promise.all([
				axios.get('/api/schedule-manager/schedules'),
				axios.get('/api/schedule-manager/tasks')
			]);
			
			schedules = schedulesRes.data;
			tasks = tasksRes.data;
		} catch (err) {
			error = '데이터를 불러오는데 실패했습니다: ' + err.message;
		} finally {
			loading = false;
		}
	}
	
	async function addSchedule() {
		try {
			const response = await axios.post('/api/schedule-manager/schedules', newSchedule);
			schedules = [response.data, ...schedules];
			newSchedule = { title: '', description: '', start_time: '', end_time: '', is_recurring: false };
		} catch (err) {
			error = '일정 추가에 실패했습니다: ' + err.message;
		}
	}
	
	async function addTask() {
		try {
			const response = await axios.post('/api/schedule-manager/tasks', newTask);
			tasks = [response.data, ...tasks];
			newTask = { title: '', description: '', priority: 'medium', due_date: '', is_completed: false };
		} catch (err) {
			error = '작업 추가에 실패했습니다: ' + err.message;
		}
	}
	
	async function toggleTask(task) {
		try {
			const updatedTask = { ...task, is_completed: !task.is_completed };
			await axios.put(`/api/schedule-manager/tasks/${task.id}`, updatedTask);
			tasks = tasks.map(t => t.id === task.id ? updatedTask : t);
		} catch (err) {
			error = '작업 상태 변경에 실패했습니다: ' + err.message;
		}
	}
	
	async function deleteSchedule(id) {
		try {
			await axios.delete(`/api/schedule-manager/schedules/${id}`);
			schedules = schedules.filter(s => s.id !== id);
		} catch (err) {
			error = '일정 삭제에 실패했습니다: ' + err.message;
		}
	}
	
	async function deleteTask(id) {
		try {
			await axios.delete(`/api/schedule-manager/tasks/${id}`);
			tasks = tasks.filter(t => t.id !== id);
		} catch (err) {
			error = '작업 삭제에 실패했습니다: ' + err.message;
		}
	}
	
	function formatDateTime(dateTimeString) {
		return new Date(dateTimeString).toLocaleString('ko-KR');
	}
	
	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString('ko-KR');
	}
	
	function getPriorityColor(priority) {
		switch (priority) {
			case 'high': return '#ef4444';
			case 'medium': return '#f59e0b';
			case 'low': return '#10b981';
			default: return '#6b7280';
		}
	}
	
	function getPriorityText(priority) {
		switch (priority) {
			case 'high': return '높음';
			case 'medium': return '보통';
			case 'low': return '낮음';
			default: return '보통';
		}
	}
	
	onMount(loadData);
</script>

<svelte:head>
	<title>Schedule Manager - Home Server</title>
</svelte:head>

<main>
	<div class="header">
		<h1>📅 Schedule Manager</h1>
		<p>일정 및 작업 관리</p>
		<nav class="breadcrumb">
			<a href="/">🏠 홈</a> / <span>Schedule Manager</span>
		</nav>
	</div>

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>데이터를 불러오는 중...</p>
		</div>
	{:else if error}
		<div class="error">
			<h3>⚠️ 오류 발생</h3>
			<p>{error}</p>
			<button on:click={loadData}>다시 시도</button>
		</div>
	{:else}
		<!-- 요약 카드들 -->
		<section class="summary">
			<div class="summary-card">
				<h3>총 일정</h3>
				<div class="count">{schedules.length}개</div>
			</div>
			<div class="summary-card">
				<h3>총 작업</h3>
				<div class="count">{tasks.length}개</div>
			</div>
			<div class="summary-card">
				<h3>완료된 작업</h3>
				<div class="count">{tasks.filter(t => t.is_completed).length}개</div>
			</div>
			<div class="summary-card">
				<h3>진행률</h3>
				<div class="count">
					{tasks.length > 0 ? Math.round((tasks.filter(t => t.is_completed).length / tasks.length) * 100) : 0}%
				</div>
			</div>
		</section>

		<div class="content-grid">
			<!-- 새 일정 추가 -->
			<section class="add-schedule">
				<h2>새 일정 추가</h2>
				<form on:submit|preventDefault={addSchedule} class="form">
					<div class="form-group">
						<label for="schedule-title">제목</label>
						<input 
							type="text" 
							id="schedule-title"
							bind:value={newSchedule.title} 
							required
							placeholder="일정 제목"
						/>
					</div>
					<div class="form-group">
						<label for="schedule-description">설명</label>
						<textarea 
							id="schedule-description"
							bind:value={newSchedule.description}
							placeholder="일정 설명"
							rows="3"
						></textarea>
					</div>
					<div class="form-row">
						<div class="form-group">
							<label for="start-time">시작 시간</label>
							<input 
								type="datetime-local" 
								id="start-time"
								bind:value={newSchedule.start_time}
								required
							/>
						</div>
						<div class="form-group">
							<label for="end-time">종료 시간</label>
							<input 
								type="datetime-local" 
								id="end-time"
								bind:value={newSchedule.end_time}
								required
							/>
						</div>
					</div>
					<div class="form-group">
						<label class="checkbox-label">
							<input 
								type="checkbox" 
								bind:checked={newSchedule.is_recurring}
							/>
							반복 일정
						</label>
					</div>
					<button type="submit" class="submit-btn">일정 추가</button>
				</form>
			</section>

			<!-- 새 작업 추가 -->
			<section class="add-task">
				<h2>새 작업 추가</h2>
				<form on:submit|preventDefault={addTask} class="form">
					<div class="form-group">
						<label for="task-title">제목</label>
						<input 
							type="text" 
							id="task-title"
							bind:value={newTask.title} 
							required
							placeholder="작업 제목"
						/>
					</div>
					<div class="form-group">
						<label for="task-description">설명</label>
						<textarea 
							id="task-description"
							bind:value={newTask.description}
							placeholder="작업 설명"
							rows="3"
						></textarea>
					</div>
					<div class="form-row">
						<div class="form-group">
							<label for="priority">우선순위</label>
							<select id="priority" bind:value={newTask.priority}>
								<option value="high">높음</option>
								<option value="medium">보통</option>
								<option value="low">낮음</option>
							</select>
						</div>
						<div class="form-group">
							<label for="due-date">마감일</label>
							<input 
								type="date" 
								id="due-date"
								bind:value={newTask.due_date}
							/>
						</div>
					</div>
					<button type="submit" class="submit-btn">작업 추가</button>
				</form>
			</section>
		</div>

		<div class="content-grid">
			<!-- 일정 목록 -->
			<section class="schedules">
				<h2>최근 일정</h2>
				{#if schedules.length === 0}
					<div class="empty-state">
						<p>등록된 일정이 없습니다.</p>
						<p>위에서 새 일정을 추가해보세요!</p>
					</div>
				{:else}
					<div class="schedule-list">
						{#each schedules.slice(0, 5) as schedule}
							<div class="schedule-item">
								<div class="schedule-info">
									<div class="title">{schedule.title}</div>
									<div class="description">{schedule.description || '설명 없음'}</div>
									<div class="time">
										{formatDateTime(schedule.start_time)} ~ {formatDateTime(schedule.end_time)}
									</div>
									{#if schedule.is_recurring}
										<span class="recurring-badge">🔄 반복</span>
									{/if}
								</div>
								<button 
									class="delete-btn"
									on:click={() => deleteSchedule(schedule.id)}
									title="삭제"
								>
									🗑️
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</section>

			<!-- 작업 목록 -->
			<section class="tasks">
				<h2>작업 목록</h2>
				{#if tasks.length === 0}
					<div class="empty-state">
						<p>등록된 작업이 없습니다.</p>
						<p>위에서 새 작업을 추가해보세요!</p>
					</div>
				{:else}
					<div class="task-list">
						{#each tasks.slice(0, 10) as task}
							<div class="task-item" class:completed={task.is_completed}>
								<div class="task-checkbox">
									<input 
										type="checkbox" 
										checked={task.is_completed}
										on:change={() => toggleTask(task)}
									/>
								</div>
								<div class="task-info">
									<div class="title" class:completed={task.is_completed}>
										{task.title}
									</div>
									<div class="description">{task.description || '설명 없음'}</div>
									<div class="meta">
										<span 
											class="priority-badge"
											style="background-color: {getPriorityColor(task.priority)}"
										>
											{getPriorityText(task.priority)}
										</span>
										{#if task.due_date}
											<span class="due-date">📅 {formatDate(task.due_date)}</span>
										{/if}
									</div>
								</div>
								<button 
									class="delete-btn"
									on:click={() => deleteTask(task.id)}
									title="삭제"
								>
									🗑️
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</section>
		</div>
	{/if}
</main>

<style>
	main {
		max-width: 1400px;
		margin: 0 auto;
		padding: 2rem;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		min-height: 100vh;
		color: white;
	}
	
	.header {
		text-align: center;
		margin-bottom: 3rem;
	}
	
	.header h1 {
		font-size: 2.5rem;
		margin: 0;
		text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
	}
	
	.breadcrumb {
		margin-top: 1rem;
		opacity: 0.8;
	}
	
	.breadcrumb a {
		color: white;
		text-decoration: none;
	}
	
	.breadcrumb a:hover {
		text-decoration: underline;
	}
	
	.loading {
		text-align: center;
		padding: 4rem;
	}
	
	.spinner {
		border: 3px solid rgba(255,255,255,0.3);
		border-radius: 50%;
		border-top: 3px solid white;
		width: 40px;
		height: 40px;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	.error {
		text-align: center;
		padding: 2rem;
		background: rgba(239, 68, 68, 0.2);
		border-radius: 12px;
		margin: 2rem 0;
	}
	
	.summary {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 3rem;
	}
	
	.summary-card {
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		border-radius: 12px;
		padding: 1.5rem;
		text-align: center;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.summary-card h3 {
		margin: 0 0 1rem 0;
		opacity: 0.8;
		font-size: 1rem;
	}
	
	.count {
		font-size: 2rem;
		font-weight: bold;
		color: #3b82f6;
	}
	
	.content-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
		gap: 2rem;
		margin-bottom: 3rem;
	}
	
	section {
		margin-bottom: 2rem;
	}
	
	section h2 {
		font-size: 1.5rem;
		margin-bottom: 1.5rem;
		text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
	}
	
	.form {
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		border-radius: 12px;
		padding: 2rem;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.form-group {
		margin-bottom: 1rem;
	}
	
	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}
	
	.form-group label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}
	
	.checkbox-label {
		display: flex !important;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}
	
	.form-group input,
	.form-group select,
	.form-group textarea {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid rgba(255, 255, 255, 0.3);
		border-radius: 8px;
		background: rgba(255, 255, 255, 0.1);
		color: white;
		font-size: 1rem;
		font-family: inherit;
	}
	
	.form-group input::placeholder,
	.form-group textarea::placeholder {
		color: rgba(255, 255, 255, 0.6);
	}
	
	.submit-btn {
		background: #10b981;
		border: none;
		color: white;
		padding: 0.75rem 2rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 1rem;
		font-weight: 500;
		transition: background 0.2s ease;
		width: 100%;
	}
	
	.submit-btn:hover {
		background: #059669;
	}
	
	.schedule-list,
	.task-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.schedule-item,
	.task-item {
		background: rgba(255, 255, 255, 0.1);
		backdrop-filter: blur(10px);
		border-radius: 12px;
		padding: 1.5rem;
		border: 1px solid rgba(255, 255, 255, 0.2);
		display: flex;
		align-items: flex-start;
		gap: 1rem;
	}
	
	.task-item.completed {
		opacity: 0.7;
	}
	
	.task-checkbox {
		margin-top: 0.25rem;
	}
	
	.task-checkbox input {
		width: 1.25rem;
		height: 1.25rem;
	}
	
	.schedule-info,
	.task-info {
		flex: 1;
	}
	
	.title {
		font-weight: 600;
		font-size: 1.1rem;
		margin-bottom: 0.5rem;
	}
	
	.title.completed {
		text-decoration: line-through;
		opacity: 0.7;
	}
	
	.description {
		opacity: 0.8;
		margin-bottom: 0.75rem;
		line-height: 1.4;
	}
	
	.time,
	.meta {
		font-size: 0.875rem;
		opacity: 0.7;
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}
	
	.recurring-badge,
	.priority-badge {
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		border-radius: 12px;
		font-weight: 500;
	}
	
	.recurring-badge {
		background: rgba(59, 130, 246, 0.3);
		color: #93c5fd;
	}
	
	.priority-badge {
		color: white;
	}
	
	.due-date {
		opacity: 0.7;
	}
	
	.delete-btn {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 6px;
		transition: background 0.2s ease;
		opacity: 0.7;
	}
	
	.delete-btn:hover {
		background: rgba(239, 68, 68, 0.2);
		opacity: 1;
	}
	
	.empty-state {
		text-align: center;
		padding: 3rem;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 12px;
		opacity: 0.7;
	}
	
	button {
		background: rgba(255, 255, 255, 0.2);
		border: 1px solid rgba(255, 255, 255, 0.3);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	button:hover:not(:disabled) {
		background: rgba(255, 255, 255, 0.3);
	}
	
	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>