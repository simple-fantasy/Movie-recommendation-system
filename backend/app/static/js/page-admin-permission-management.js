document.addEventListener('DOMContentLoaded', () => {
  const filterForm = document.getElementById('filterForm');
  const usersTableBody = document.getElementById('usersTableBody');
  const paginationEl = document.getElementById('pagination');
  const addAdminModalEl = document.getElementById('addAdminModal');
  const editPermissionModalEl = document.getElementById('editPermissionModal');
  const addAdminButton = document.getElementById('btn-add-admin');
  const updatePermissionButton = document.getElementById('btn-update-permission');
  const searchInput = document.getElementById('searchInput');
  const userTypeSelect = document.getElementById('userType');
  const permissionLevelSelect = document.getElementById('permissionLevel');

  let currentPage = 1;
  let currentFilters = {};

  function getUserTypeBadge(user) {
    if (user.is_admin) return '<span class="badge bg-danger">管理员</span>';
    if (user.is_active) return '<span class="badge bg-success">活跃用户</span>';
    return '<span class="badge bg-secondary">未活跃用户</span>';
  }

  function getPermissionBadge(user) {
    const map = {
      super_admin: '<span class="badge bg-dark">超级管理员</span>',
      admin: '<span class="badge bg-danger">管理员</span>',
      moderator: '<span class="badge bg-warning">版主</span>',
      user: '<span class="badge bg-info">普通用户</span>'
    };
    return map[user.permission_level] || map.user;
  }

  function getStatusBadge(user) {
    return user.is_active ? '<span class="badge bg-success">活跃</span>' : '<span class="badge bg-danger">禁用</span>';
  }

  async function loadStatistics() {
    try {
      const response = await fetch('/admin/api/permission-stats');
      const stats = await response.json();
      document.getElementById('totalUsers').textContent = stats.total_users || 0;
      document.getElementById('adminUsers').textContent = stats.admin_users || 0;
      document.getElementById('inactiveAdmins').textContent = stats.inactive_admins || 0;
      document.getElementById('recentLogins').textContent = stats.recent_logins || 0;
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  }

  async function loadUsers() {
    try {
      const params = new URLSearchParams({ page: currentPage, ...currentFilters });
      const response = await fetch(`/admin/api/users-permissions?${params}`);
      const data = await response.json();
      renderUsersTable(data.users || []);
      renderPagination(paginationEl, data.pagination, (page) => { currentPage = page; loadUsers(); });
    } catch (error) {
      console.error('加载用户列表失败:', error);
      if (usersTableBody) {
        usersTableBody.innerHTML = `
          <tr>
            <td colspan="8" class="text-center py-4 text-danger">
              加载失败，请刷新页面重试
            </td>
          </tr>
        `;
      }
    }
  }

  function renderUsersTable(users) {
    if (!usersTableBody) return;
    if (!users.length) {
      usersTableBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-4 text-muted">
            没有找到符合条件的用户
          </td>
        </tr>
      `;
      return;
    }

    usersTableBody.innerHTML = users.map(user => `
      <tr>
        <td>
          <div class="d-flex align-items-center">
            <div class="user-avatar me-2">
              ${user.avatar ? `<img src="${escapeHtml(user.avatar)}" class="rounded-circle" width="32" height="32" alt="${escapeHtml(user.username)}">` : `<div class="avatar-placeholder rounded-circle d-flex align-items-center justify-content-center" style="width: 32px; height: 32px; background: #e5e7eb; color: #9ca3af; font-size: 0.875rem;">${escapeHtml(user.username.charAt(0).toUpperCase())}</div>`}
            </div>
            <div>
              <div class="fw-semibold">${escapeHtml(user.username)}</div>
              <small class="text-muted">ID: ${user.id}</small>
            </div>
          </div>
        </td>
        <td>${escapeHtml(user.email)}</td>
        <td>${getUserTypeBadge(user)}</td>
        <td>${getPermissionBadge(user)}</td>
        <td>${getStatusBadge(user)}</td>
        <td>${formatDate(user.last_login)}</td>
        <td>${formatDate(user.created_at)}</td>
        <td>
          <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-primary btn-edit-permission" data-id="${user.id}" data-username="${escapeHtml(user.username)}" data-permission="${escapeHtml(user.permission_level)}" data-active="${user.is_active}">
              <i class="bi bi-pencil"></i>
            </button>
            ${!user.is_admin ? `<button type="button" class="btn btn-outline-success btn-make-admin" data-id="${user.id}"><i class="bi bi-shield-plus"></i></button>` : `<button type="button" class="btn btn-outline-warning btn-remove-admin" data-id="${user.id}"><i class="bi bi-shield-x"></i></button>`}
          </div>
        </td>
      </tr>
    `).join('');
  }

  function showModal(element) {
    if (!element) return null;
    return new bootstrap.Modal(element);
  }

  function openAddAdminModal() {
    const modal = showModal(addAdminModalEl);
    modal?.show();
  }

  function openEditPermissionModal(userId, username, permissionLevel, isActive) {
    document.getElementById('editUserId').value = userId;
    document.getElementById('editUsername').value = username;
    document.getElementById('editPermissionLevel').value = permissionLevel;
    document.getElementById('editUserStatus').value = isActive ? 'active' : 'inactive';
    const modal = showModal(editPermissionModalEl);
    modal?.show();
  }

  async function addAdmin() {
    const username = document.getElementById('adminUsername')?.value.trim();
    const permissionLevel = document.getElementById('adminPermissionLevel')?.value;
    if (!username || !permissionLevel) {
      showAlert('warning', '请填写完整信息');
      return;
    }
    try {
      const response = await fetch('/admin/api/add-admin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, permission_level: permissionLevel })
      });
      const result = await response.json();
      if (result.success) {
        showAlert('success', '管理员添加成功');
        showModal(addAdminModalEl)?.hide();
        document.getElementById('addAdminForm')?.reset();
        loadUsers();
        loadStatistics();
      } else {
        showAlert('danger', result.message || '添加失败');
      }
    } catch (error) {
      console.error('添加管理员失败:', error);
      showAlert('danger', '添加失败，请重试');
    }
  }

  async function updateUserPermission() {
    const userId = document.getElementById('editUserId')?.value;
    const permissionLevel = document.getElementById('editPermissionLevel')?.value;
    const isActive = document.getElementById('editUserStatus')?.value === 'active';
    try {
      const response = await fetch(`/admin/api/users/${userId}/permissions`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ permission_level: permissionLevel, is_active: isActive })
      });
      const result = await response.json();
      if (result.success) {
        showAlert('success', '权限更新成功');
        showModal(editPermissionModalEl)?.hide();
        loadUsers();
        loadStatistics();
      } else {
        showAlert('danger', result.message || '更新失败');
      }
    } catch (error) {
      console.error('更新权限失败:', error);
      showAlert('danger', '更新失败，请重试');
    }
  }

  async function makeAdmin(userId) {
    if (!confirm('确定要将该用户设置为管理员吗？')) return;
    try {
      const response = await fetch(`/admin/api/users/${userId}/make-admin`, { method: 'POST' });
      const result = await response.json();
      if (result.success) {
        showAlert('success', '设置成功');
        loadUsers();
        loadStatistics();
      } else {
        showAlert('danger', result.message || '设置失败');
      }
    } catch (error) {
      console.error('设置管理员失败:', error);
      showAlert('danger', '设置失败，请重试');
    }
  }

  async function removeAdmin(userId) {
    if (!confirm('确定要移除该用户的管理员权限吗？')) return;
    try {
      const response = await fetch(`/admin/api/users/${userId}/remove-admin`, { method: 'POST' });
      const result = await response.json();
      if (result.success) {
        showAlert('success', '权限移除成功');
        loadUsers();
        loadStatistics();
      } else {
        showAlert('danger', result.message || '移除失败');
      }
    } catch (error) {
      console.error('移除权限失败:', error);
      showAlert('danger', '移除失败，请重试');
    }
  }

  if (filterForm) {
    filterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      currentPage = 1;
      currentFilters = {
        search: searchInput?.value || '',
        user_type: userTypeSelect?.value || '',
        permission_level: permissionLevelSelect?.value || ''
      };
      loadUsers();
    });
  }

  if (usersTableBody) {
    usersTableBody.addEventListener('click', (event) => {
      const editButton = event.target.closest('.btn-edit-permission');
      const makeAdminButton = event.target.closest('.btn-make-admin');
      const removeAdminButton = event.target.closest('.btn-remove-admin');
      if (editButton) {
        const userId = Number(editButton.dataset.id);
        const username = editButton.dataset.username || '';
        const permissionLevel = editButton.dataset.permission || 'user';
        const isActive = editButton.dataset.active === 'true';
        if (!Number.isNaN(userId)) {
          openEditPermissionModal(userId, username, permissionLevel, isActive);
        }
        return;
      }
      if (makeAdminButton) {
        const userId = Number(makeAdminButton.dataset.id);
        if (!Number.isNaN(userId)) makeAdmin(userId);
        return;
      }
      if (removeAdminButton) {
        const userId = Number(removeAdminButton.dataset.id);
        if (!Number.isNaN(userId)) removeAdmin(userId);
      }
    });
  }

  document.querySelector('.btn-show-add-admin')?.addEventListener('click', openAddAdminModal);
  document.querySelector('.btn-show-role-modal')?.addEventListener('click', () => showModal(document.getElementById('roleModal'))?.show());
  updatePermissionButton?.addEventListener('click', updateUserPermission);
  addAdminButton?.addEventListener('click', addAdmin);

  loadStatistics();
  loadUsers();
});
