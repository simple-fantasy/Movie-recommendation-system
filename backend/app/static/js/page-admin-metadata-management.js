document.addEventListener('DOMContentLoaded', () => {
  const filterForm = document.getElementById('filterForm');
  const moviesTableBody = document.getElementById('moviesTableBody');
  const paginationEl = document.getElementById('pagination');
  const batchUpdateModalEl = document.getElementById('batchUpdateModal');
  const importModalEl = document.getElementById('importModal');
  const progressModalEl = document.getElementById('progressModal');
  const startBatchUpdateButton = document.getElementById('btn-start-batch-update');
  const startImportButton = document.getElementById('btn-start-import');
  const searchInput = document.getElementById('searchInput');
  const metadataStatusSelect = document.getElementById('metadataStatus');
  const posterStatusSelect = document.getElementById('posterStatus');

  let currentPage = 1;
  let currentFilters = {};

  function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
  }

  function showAlert(type, message) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
      ${escapeHtml(message)}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    setTimeout(() => {
      if (alert.parentNode) alert.parentNode.removeChild(alert);
    }, 3000);
  }

  function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function getMetadataStatusBadge(movie) {
    const hasTitle = movie.title;
    const hasYear = movie.year;
    const hasDirector = movie.director;
    const hasGenres = movie.genres;
    const hasDescription = movie.description;
    const completeCount = [hasTitle, hasYear, hasDirector, hasGenres, hasDescription].filter(Boolean).length;
    if (completeCount >= 4) {
      return '<span class="badge bg-success">完整</span>';
    } else if (completeCount >= 2) {
      return '<span class="badge bg-warning">不完整</span>';
    }
    return '<span class="badge bg-danger">缺失</span>';
  }

  async function loadStatistics() {
    try {
      const response = await fetch('/admin/api/metadata-stats');
      const stats = await response.json();
      document.getElementById('totalMovies').textContent = stats.total_movies || 0;
      document.getElementById('missingMetadata').textContent = stats.missing_metadata || 0;
      document.getElementById('missingPosters').textContent = stats.missing_posters || 0;
      document.getElementById('completeMovies').textContent = stats.complete_movies || 0;
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  }

  async function loadMovies() {
    try {
      const params = new URLSearchParams({ page: currentPage, ...currentFilters });
      const response = await fetch(`/admin/api/movies-metadata?${params}`);
      const data = await response.json();
      renderMoviesTable(data.movies || []);
      renderPagination(data.pagination || { pages: 1, page: 1, has_prev: false, has_next: false });
    } catch (error) {
      console.error('加载电影列表失败:', error);
      if (moviesTableBody) {
        moviesTableBody.innerHTML = `
          <tr>
            <td colspan="8" class="text-center py-4 text-danger">
              加载失败，请刷新页面重试
            </td>
          </tr>
        `;
      }
    }
  }

  function renderMoviesTable(movies) {
    if (!moviesTableBody) return;
    if (!movies.length) {
      moviesTableBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-4 text-muted">
            没有找到符合条件的电影
          </td>
        </tr>
      `;
      return;
    }
    moviesTableBody.innerHTML = movies.map(movie => `
      <tr>
        <td>
          <div class="d-flex align-items-center">
            ${movie.poster_url ? 
              `<img src="${escapeHtml(movie.poster_url)}" class="movie-poster me-2" alt="${escapeHtml(movie.title)}">` :
              `<div class="movie-poster-placeholder me-2">无海报</div>`
            }
            <div>
              <div class="fw-semibold">${escapeHtml(movie.title)}</div>
              <small class="text-muted">ID: ${movie.id}</small>
            </div>
          </div>
        </td>
        <td>${escapeHtml(movie.year || '-')}</td>
        <td>${escapeHtml(movie.director || '-')}</td>
        <td>
          <div class="genre-tags">
            ${(movie.genres || '').split('|').slice(0, 2).map(genre => `<span class="badge bg-secondary me-1">${escapeHtml(genre.trim())}</span>`).join('')}
          </div>
        </td>
        <td>${getMetadataStatusBadge(movie)}</td>
        <td>${movie.poster_url ? '<span class="badge bg-success">有海报</span>' : '<span class="badge bg-danger">无海报</span>'}</td>
        <td>${formatDate(movie.updated_at)}</td>
        <td>
          <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-primary btn-update-metadata" data-id="${movie.id}">
              <i class="bi bi-arrow-repeat"></i>
            </button>
            <button type="button" class="btn btn-outline-info btn-edit-movie" data-id="${movie.id}">
              <i class="bi bi-pencil"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  function renderPagination(pagination) {
    if (!paginationEl) return;
    const pages = pagination.pages || 1;
    const page = pagination.page || 1;
    if (pages <= 1) {
      paginationEl.innerHTML = '';
      return;
    }
    let html = '';
    if (pagination.has_prev) {
      html += `<li class="page-item"><button type="button" class="page-link" data-page="${page - 1}">上一页</button></li>`;
    }
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(pages, page + 2);
    for (let i = startPage; i <= endPage; i += 1) {
      html += `<li class="page-item ${i === page ? 'active' : ''}"><button type="button" class="page-link" data-page="${i}">${i}</button></li>`;
    }
    if (pagination.has_next) {
      html += `<li class="page-item"><button type="button" class="page-link" data-page="${page + 1}">下一页</button></li>`;
    }
    paginationEl.innerHTML = html;
  }

  function showModal(element) {
    if (!element) return null;
    return new bootstrap.Modal(element);
  }

  async function updateMetadata(movieId) {
    try {
      const response = await fetch(`/api/admin/movies/${movieId}/update-metadata`, { method: 'POST' });
      const result = await response.json();
      if (result.success) {
        showAlert('success', '元数据更新成功');
        loadMovies();
        loadStatistics();
      } else {
        showAlert('danger', result.message || '更新失败');
      }
    } catch (error) {
      console.error('更新元数据失败:', error);
      showAlert('danger', '更新失败，请重试');
    }
  }

  function editMovie(movieId) {
    window.open(`/admin/movies/${movieId}/edit`, '_blank');
  }

  async function startBatchUpdate() {
    const updateScope = document.getElementById('updateScope')?.value;
    const dataSource = document.getElementById('dataSource')?.value;
    const modal = showModal(batchUpdateModalEl);
    modal?.hide();
    const progressModal = showModal(progressModalEl);
    progressModal?.show();
    try {
      const response = await fetch('/api/admin/batch-update-metadata', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scope: updateScope, data_source: dataSource })
      });
      const result = await response.json();
      if (result.task_id) {
        pollTaskProgress(result.task_id);
      } else {
        showAlert('danger', result.message || '启动批量更新失败');
      }
    } catch (error) {
      console.error('批量更新失败:', error);
      showAlert('danger', '批量更新失败，请重试');
    }
  }

  async function startImport() {
    const fileInput = document.getElementById('importFile');
    const file = fileInput?.files?.[0];
    if (!file) {
      showAlert('warning', '请选择要导入的文件');
      return;
    }
    const importMode = document.getElementById('importMode')?.value;
    const modal = showModal(importModalEl);
    modal?.hide();
    const progressModal = showModal(progressModalEl);
    progressModal?.show();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('import_mode', importMode);
    try {
      const response = await fetch('/api/admin/import-metadata', { method: 'POST', body: formData });
      const result = await response.json();
      if (result.task_id) {
        pollTaskProgress(result.task_id);
      } else {
        showAlert('danger', result.message || '导入失败');
      }
    } catch (error) {
      console.error('导入失败:', error);
      showAlert('danger', '导入失败，请重试');
    }
  }

  async function pollTaskProgress(taskId) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressDetail = document.getElementById('progressDetail');
    if (!progressBar || !progressText || !progressDetail) return;

    try {
      const response = await fetch(`/admin/api/task-progress/${taskId}`);
      const result = await response.json();
      const percent = result.progress || 0;
      progressBar.style.width = `${percent}%`;
      progressText.textContent = result.message || '处理中...';
      progressDetail.textContent = result.detail || '';
      if (!result.completed) {
        setTimeout(() => pollTaskProgress(taskId), 1000);
      } else {
        showAlert('success', '处理完成');
        loadMovies();
        loadStatistics();
      }
    } catch (error) {
      console.error('轮询任务进度失败:', error);
      showAlert('danger', '无法获取任务进度');
    }
  }

  if (filterForm) {
    filterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      currentPage = 1;
      currentFilters = {
        search: searchInput?.value || '',
        metadata_status: metadataStatusSelect?.value || '',
        poster_status: posterStatusSelect?.value || ''
      };
      loadMovies();
    });
  }

  if (moviesTableBody) {
    moviesTableBody.addEventListener('click', (event) => {
      const updateButton = event.target.closest('.btn-update-metadata');
      const editButton = event.target.closest('.btn-edit-movie');
      if (updateButton) {
        const id = Number(updateButton.dataset.id);
        if (!Number.isNaN(id)) updateMetadata(id);
        return;
      }
      if (editButton) {
        const id = Number(editButton.dataset.id);
        if (!Number.isNaN(id)) editMovie(id);
      }
    });
  }

  if (paginationEl) {
    paginationEl.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-page]');
      if (!button) return;
      const page = Number(button.dataset.page);
      if (!Number.isNaN(page)) {
        currentPage = page;
        loadMovies();
      }
    });
  }

  if (startBatchUpdateButton) {
    startBatchUpdateButton.addEventListener('click', startBatchUpdate);
  }
  if (startImportButton) {
    startImportButton.addEventListener('click', startImport);
  }

  loadStatistics();
  loadMovies();
});
