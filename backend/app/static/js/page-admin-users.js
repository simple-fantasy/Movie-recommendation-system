document.addEventListener('DOMContentLoaded', () => {
  async function toggleAdmin(userId, username, isAdmin) {
    const action = isAdmin ? '撤销管理员权限' : '设为管理员';
    if (!confirm(`确定要${action}用户 "${username}" 吗？`)) return;

    try {
      const response = await fetch(`/api/admin/users/${userId}/toggle-admin`, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      const data = await response.json();
      if (data.success) {
        alert(data.message);
        location.reload();
      } else {
        alert('操作失败: ' + (data.error || '未知错误'));
      }
    } catch (error) {
      alert('网络错误，请重试');
    }
  }

  async function toggleActive(userId, username, isActive) {
    const action = isActive ? '禁用' : '启用';
    if (!confirm(`确定要${action}用户 "${username}" 吗？`)) return;

    try {
      const response = await fetch(`/api/admin/users/${userId}/toggle-active`, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      const data = await response.json();
      if (data.success) {
        alert(data.message);
        location.reload();
      } else {
        alert('操作失败: ' + (data.error || '未知错误'));
      }
    } catch (error) {
      alert('网络错误，请重试');
    }
  }

  document.body.addEventListener('click', (event) => {
    const adminButton = event.target.closest('.btn-toggle-admin');
    if (adminButton) {
      const userId = Number(adminButton.dataset.id);
      const username = adminButton.dataset.username || '';
      const isAdmin = adminButton.dataset.admin === 'True' || adminButton.dataset.admin === 'true';
      if (!Number.isNaN(userId)) {
        toggleAdmin(userId, username, isAdmin);
      }
      return;
    }

    const activeButton = event.target.closest('.btn-toggle-active');
    if (activeButton) {
      const userId = Number(activeButton.dataset.id);
      const username = activeButton.dataset.username || '';
      const isActive = activeButton.dataset.active === 'True' || activeButton.dataset.active === 'true';
      if (!Number.isNaN(userId)) {
        toggleActive(userId, username, isActive);
      }
    }
  });
});
