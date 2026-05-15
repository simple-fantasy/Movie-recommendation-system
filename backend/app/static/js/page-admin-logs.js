document.addEventListener('DOMContentLoaded', () => {
  const refreshBtn = document.getElementById('btn-refresh-logs');
  const filterGroup = document.getElementById('log-filter-group');
  const loadMoreBtn = document.getElementById('btn-load-more-logs');
  const loadingEl = document.getElementById('loading');
  const contentEl = document.getElementById('logs-content');
  const container = document.getElementById('logs-container');

  let currentFilter = 'all';
  let allLogs = [];
  let displayedLogs = [];
  const LOGS_PER_PAGE = 50;

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function createLogEntry(log) {
    const div = document.createElement('div');
    div.className = `log-entry ${String(log.level || 'INFO').toLowerCase()}`;

    const timestamp = new Date(log.timestamp).toLocaleString('zh-CN');
    const level = log.level || 'INFO';
    const message = log.message || '';

    let details = '';
    if (log.path) details += `<div><strong>路径:</strong> ${escapeHtml(log.path)}</div>`;
    if (log.user_id) details += `<div><strong>用户ID:</strong> ${escapeHtml(String(log.user_id))}</div>`;
    if (log.method) details += `<div><strong>方法:</strong> ${escapeHtml(log.method)}</div>`;
    if (log.status_code) details += `<div><strong>状态码:</strong> ${escapeHtml(String(log.status_code))}</div>`;

    div.innerHTML = `
      <div class="log-timestamp">${timestamp}</div>
      <div class="log-message">
        <span class="log-level ${level}">${level}</span>
        ${escapeHtml(message)}
      </div>
      ${details ? `<div class="log-details">${details}</div>` : ''}
    `;

    return div;
  }

  function displayLogs(logs) {
    if (!container) return;
    container.innerHTML = '';

    if (!logs.length) {
      container.innerHTML = `
        <div class="empty-state">
          <h3>暂无日志</h3>
          <p>当前筛选条件下没有找到日志记录</p>
        </div>
      `;
      return;
    }

    logs.forEach(log => container.appendChild(createLogEntry(log)));
  }

  function updateFilterButtons(activeButton) {
    if (!filterGroup) return;
    filterGroup.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    if (activeButton) activeButton.classList.add('active');
  }

  function getFilteredLogs() {
    if (currentFilter === 'all') return allLogs;
    return allLogs.filter(log => (log.level || 'INFO') === currentFilter);
  }

  function loadMoreLogs() {
    const filteredLogs = getFilteredLogs();
    const currentCount = displayedLogs.length;
    const newLogs = filteredLogs.slice(currentCount, currentCount + LOGS_PER_PAGE);
    displayedLogs = displayedLogs.concat(newLogs);

    newLogs.forEach(log => {
      if (container) {
        container.appendChild(createLogEntry(log));
      }
    });
  }

  function showLoading() {
    if (loadingEl) loadingEl.style.display = 'flex';
    if (contentEl) contentEl.style.display = 'none';
  }

  function hideLoading() {
    if (loadingEl) loadingEl.style.display = 'none';
    if (contentEl) contentEl.style.display = 'block';
  }

  async function loadLogs() {
    showLoading();

    try {
      const response = await fetch('/api/admin/logs');
      const data = await response.json();
      allLogs = Array.isArray(data.logs) ? data.logs : [];
      displayedLogs = allLogs.slice(0, LOGS_PER_PAGE);
      displayLogs(displayedLogs);
    } catch (error) {
      console.error('加载日志失败:', error);
      if (container) {
        container.innerHTML = `
          <div class="empty-state">
            <h3>加载日志失败</h3>
            <p>请稍后重试</p>
          </div>
        `;
      }
    } finally {
      hideLoading();
    }
  }

  function refreshLogs() {
    currentFilter = 'all';
    updateFilterButtons(filterGroup?.querySelector('[data-level="all"]'));
    loadLogs();
  }

  if (filterGroup) {
    filterGroup.addEventListener('click', (event) => {
      const button = event.target.closest('.filter-btn');
      if (!button) return;
      const level = button.dataset.level;
      if (!level) return;
      currentFilter = level;
      updateFilterButtons(button);
      displayedLogs = getFilteredLogs().slice(0, LOGS_PER_PAGE);
      displayLogs(displayedLogs);
    });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener('click', refreshLogs);
  }

  if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', loadMoreLogs);
  }

  loadLogs();
});
