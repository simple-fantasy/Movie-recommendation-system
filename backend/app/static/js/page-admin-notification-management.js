document.addEventListener('DOMContentLoaded', () => {
  const btnShowSendNotification = document.getElementById('btn-show-send-notification-modal');
  const btnShowTemplateModal = document.getElementById('btn-show-template-modal');
  const btnShowAddTemplateModal = document.getElementById('btn-show-add-template-modal');
  const btnSendNotification = document.getElementById('btn-send-notification');
  const btnAddTemplate = document.getElementById('btn-add-template');
  const sendScopeSelect = document.getElementById('sendScope');
  const specificUsersDiv = document.getElementById('specificUsersDiv');
  const filterForm = document.getElementById('filterForm');
  const notificationsTableBody = document.getElementById('notificationsTableBody');
  const templatesTableBody = document.getElementById('templatesTableBody');
  const paginationEl = document.getElementById('pagination');

  const sendNotificationModalEl = document.getElementById('sendNotificationModal');
  const templateModalEl = document.getElementById('templateModal');
  const addTemplateModalEl = document.getElementById('addTemplateModal');

  let currentPage = 1;
  let totalPages = 1;
  let currentFilters = {};

  function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
  }

  function showModal(element) {
    if (!element) return null;
    return new bootstrap.Modal(element);
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

  function getTypeBadge(type) {
    const typeMap = {
      system: '<span class="badge bg-primary">系统通知</span>',
      review: '<span class="badge bg-success">评论通知</span>',
      recommend: '<span class="badge bg-warning">推荐通知</span>',
      achievement: '<span class="badge bg-info">成就通知</span>'
    };
    return typeMap[type] || '<span class="badge bg-secondary">未知类型</span>';
  }

  function getStatusBadge(isRead) {
    return isRead ? '<span class="badge bg-success">已读</span>' : '<span class="badge bg-warning">未读</span>';
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

  async function loadStatistics() {
    try {
      const response = await fetch('/admin/api/notification-stats');
      const stats = await response.json();
      document.getElementById('totalNotifications').textContent = stats.total_notifications || 0;
      document.getElementById('readNotifications').textContent = stats.read_notifications || 0;
      document.getElementById('unreadNotifications').textContent = stats.unread_notifications || 0;
      document.getElementById('todayNotifications').textContent = stats.today_notifications || 0;
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  }

  async function loadNotifications() {
    try {
      const params = new URLSearchParams({ page: currentPage, ...currentFilters });
      const response = await fetch(`/admin/api/notifications?${params}`);
      const data = await response.json();
      renderNotificationsTable(data.notifications || []);
      renderPagination(data.pagination || { pages: 1, page: 1, has_prev: false, has_next: false });
      totalPages = data.pagination?.pages || 1;
    } catch (error) {
      console.error('加载通知列表失败:', error);
      if (notificationsTableBody) {
        notificationsTableBody.innerHTML = `
          <tr>
            <td colspan="6" class="text-center py-4 text-danger">
              加载失败，请刷新页面重试
            </td>
          </tr>
        `;
      }
    }
  }

  function renderNotificationsTable(notifications) {
    if (!notificationsTableBody) return;
    if (!notifications.length) {
      notificationsTableBody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4 text-muted">
            没有找到符合条件的通知
          </td>
        </tr>
      `;
      return;
    }

    notificationsTableBody.innerHTML = notifications.map(notification => `
      <tr>
        <td>
          <div>
            <div class="fw-semibold">${escapeHtml(notification.title)}</div>
            <div class="text-muted small">${escapeHtml(notification.content)}</div>
          </div>
        </td>
        <td>${getTypeBadge(notification.type)}</td>
        <td>${notification.target_user ? `<span class="badge bg-info">${escapeHtml(notification.target_user)}</span>` : '<span class="badge bg-secondary">全体用户</span>'}</td>
        <td>${getStatusBadge(notification.is_read)}</td>
        <td>${formatDate(notification.created_at)}</td>
        <td>
          <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-info btn-view-notification" data-id="${notification.id}">
              <i class="bi bi-eye"></i>
            </button>
            <button type="button" class="btn btn-outline-danger btn-delete-notification" data-id="${notification.id}">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  function renderPagination(pagination) {
    if (!paginationEl) return;
    if ((pagination.pages || 1) <= 1) {
      paginationEl.innerHTML = '';
      return;
    }

    const page = pagination.page || 1;
    const pages = pagination.pages || 1;
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

  function changePage(page) {
    currentPage = page;
    loadNotifications();
  }

  function showSendNotificationModal() {
    const modal = showModal(sendNotificationModalEl);
    modal?.show();
  }

  function showTemplateModal() {
    const modal = showModal(templateModalEl);
    modal?.show();
  }

  function showAddTemplateModal() {
    const modal = showModal(addTemplateModalEl);
    modal?.show();
  }

  async function sendNotification() {
    const type = document.getElementById('notificationTypeSelect')?.value;
    const scope = sendScopeSelect?.value;
    const specificUsers = document.getElementById('specificUsers')?.value || '';
    const title = document.getElementById('notificationTitle')?.value.trim();
    const content = document.getElementById('notificationContent')?.value.trim();
    const relatedLink = document.getElementById('relatedLink')?.value.trim();

    if (!type || !scope || !title || !content) {
      showAlert('warning', '请填写必要信息');
      return;
    }

    if (scope === 'specific' && !specificUsers) {
      showAlert('warning', '请指定目标用户');
      return;
    }

    try {
      const response = await fetch('/admin/notifications/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type,
          scope,
          specific_users: specificUsers,
          title,
          content,
          related_link: relatedLink
        })
      });
      const result = await response.json();
      if (result.success) {
        showAlert('success', '通知发送成功');
        bootstrap.Modal.getInstance(sendNotificationModalEl)?.hide();
        document.getElementById('sendNotificationForm')?.reset();
        loadNotifications();
        loadStatistics();
      } else {
        showAlert('danger', result.message || '发送失败');
      }
    } catch (error) {
      console.error('发送通知失败:', error);
      showAlert('danger', '发送失败，请重试');
    }
  }

  async function loadTemplates() {
    try {
      const response = await fetch('/admin/api/notification-templates');
      const data = await response.json();
      renderTemplatesTable(data.templates || []);
    } catch (error) {
      console.error('加载模板失败:', error);
      if (templatesTableBody) {
        templatesTableBody.innerHTML = `
          <tr>
            <td colspan="5" class="text-center py-3 text-danger">
              加载模板失败
            </td>
          </tr>
        `;
      }
    }
  }

  function renderTemplatesTable(templates) {
    if (!templatesTableBody) return;
    if (!templates.length) {
      templatesTableBody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center py-3 text-muted">
            暂无模板
          </td>
        </tr>
      `;
      return;
    }

    templatesTableBody.innerHTML = templates.map(template => `
      <tr>
        <td>${escapeHtml(template.name)}</td>
        <td>${getTypeBadge(template.type)}</td>
        <td>${escapeHtml(template.title)}</td>
        <td>
          <div class="text-truncate" style="max-width: 200px;" title="${escapeHtml(template.content)}">
            ${escapeHtml(template.content)}
          </div>
        </td>
        <td>
          <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-primary btn-use-template" data-id="${template.id}">
              <i class="bi bi-check"></i>
            </button>
            <button type="button" class="btn btn-outline-danger btn-delete-template" data-id="${template.id}">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  async function addTemplate() {
    const name = document.getElementById('templateName')?.value.trim();
    const type = document.getElementById('templateType')?.value;
    const title = document.getElementById('templateTitle')?.value.trim();
    const content = document.getElementById('templateContent')?.value.trim();

    if (!name || !type || !title || !content) {
      showAlert('warning', '请填写完整信息');
      return;
    }

    try {
      const response = await fetch('/admin/api/notification-templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, type, title, content })
      });
      const result = await response.json();
      if (result.success) {
        showAlert('success', '模板添加成功');
        bootstrap.Modal.getInstance(addTemplateModalEl)?.hide();
        document.getElementById('addTemplateForm')?.reset();
        loadTemplates();
      } else {
        showAlert('danger', result.message || '添加失败');
      }
    } catch (error) {
      console.error('添加模板失败:', error);
      showAlert('danger', '添加失败，请重试');
    }
  }

  function useTemplate(templateId) {
    showAlert('info', '模板使用功能开发中...');
  }

  async function deleteTemplate(templateId) {
    if (!confirm('确定要删除这个模板吗？')) return;
    try {
      const response = await fetch(`/admin/api/notification-templates/${templateId}`, { method: 'DELETE' });
      const result = await response.json();
      if (result.success) {
        showAlert('success', '模板删除成功');
        loadTemplates();
      } else {
        showAlert('danger', result.message || '删除失败');
      }
    } catch (error) {
      console.error('删除模板失败:', error);
      showAlert('danger', '删除失败，请重试');
    }
  }

  function viewNotification(notificationId) {
    showAlert('info', '通知详情功能开发中...');
  }

  async function deleteNotification(notificationId) {
    if (!confirm('确定要删除这个通知吗？')) return;
    try {
      const response = await fetch(`/admin/api/notifications/${notificationId}`, { method: 'DELETE' });
      const result = await response.json();
      if (result.success) {
        showAlert('success', '通知删除成功');
        loadNotifications();
        loadStatistics();
      } else {
        showAlert('danger', result.message || '删除失败');
      }
    } catch (error) {
      console.error('删除通知失败:', error);
      showAlert('danger', '删除失败，请重试');
    }
  }

  if (btnShowSendNotification) {
    btnShowSendNotification.addEventListener('click', showSendNotificationModal);
  }
  if (btnShowTemplateModal) {
    btnShowTemplateModal.addEventListener('click', showTemplateModal);
  }
  if (btnShowAddTemplateModal) {
    btnShowAddTemplateModal.addEventListener('click', showAddTemplateModal);
  }
  if (btnSendNotification) {
    btnSendNotification.addEventListener('click', sendNotification);
  }
  if (btnAddTemplate) {
    btnAddTemplate.addEventListener('click', addTemplate);
  }
  if (sendScopeSelect && specificUsersDiv) {
    sendScopeSelect.addEventListener('change', () => {
      specificUsersDiv.style.display = sendScopeSelect.value === 'specific' ? 'block' : 'none';
    });
  }
  if (filterForm) {
    filterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      currentPage = 1;
      currentFilters = {
        search: document.getElementById('searchInput')?.value || '',
        type: document.getElementById('notificationType')?.value || '',
        status: document.getElementById('notificationStatus')?.value || ''
      };
      loadNotifications();
    });
  }
  if (notificationsTableBody) {
    notificationsTableBody.addEventListener('click', (event) => {
      const viewButton = event.target.closest('.btn-view-notification');
      const deleteButton = event.target.closest('.btn-delete-notification');
      if (viewButton) {
        const id = Number(viewButton.dataset.id);
        if (!Number.isNaN(id)) viewNotification(id);
      }
      if (deleteButton) {
        const id = Number(deleteButton.dataset.id);
        if (!Number.isNaN(id)) deleteNotification(id);
      }
    });
  }
  if (templatesTableBody) {
    templatesTableBody.addEventListener('click', (event) => {
      const useButton = event.target.closest('.btn-use-template');
      const deleteButton = event.target.closest('.btn-delete-template');
      if (useButton) {
        const id = Number(useButton.dataset.id);
        if (!Number.isNaN(id)) useTemplate(id);
      }
      if (deleteButton) {
        const id = Number(deleteButton.dataset.id);
        if (!Number.isNaN(id)) deleteTemplate(id);
      }
    });
  }
  if (paginationEl) {
    paginationEl.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-page]');
      if (!button) return;
      const page = Number(button.dataset.page);
      if (!Number.isNaN(page)) changePage(page);
    });
  }

  loadStatistics();
  loadNotifications();
  loadTemplates();
});
