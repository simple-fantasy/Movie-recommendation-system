async function fetchCollections() {
  const box = document.getElementById('collections-list');
  if (!box) return;
  box.innerHTML = '<div class="small-note">加载中...</div>';
  try {
    const response = await api('/api/my/collections');
    const collections = response.collections || [];
    if (!collections.length) {
      box.innerHTML = '<div class="small-note">暂无收藏列表。去浏览电影并将喜欢的内容加入收藏吧。</div>';
      return;
    }
    box.innerHTML = collections.map((item) => `
      <div class="list-group-item">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <div class="fw-semibold">${escapeHtml(item.name)}</div>
            <div class="small-note">创建于 ${escapeHtml(item.created_at || '-')}</div>
          </div>
          <button class="btn btn-sm btn-outline-danger btn-remove-collection" data-id="${item.id}">移除</button>
        </div>
        <div class="mt-2 small-note">${escapeHtml(item.description || '无描述')}</div>
      </div>
    `).join('');

    box.querySelectorAll('.btn-remove-collection').forEach((button) => {
      button.addEventListener('click', async () => {
        const collectionId = button.dataset.id;
        if (!collectionId) return;
        button.disabled = true;
        try {
          await api(`/api/collections/${collectionId}`, { method: 'DELETE' });
          await fetchCollections();
          showToast('已移除收藏列表', 'success');
        } catch (err) {
          showToast('移除失败：' + err.message, 'error');
        } finally {
          button.disabled = false;
        }
      });
    });
  } catch (err) {
    box.innerHTML = '<div class="small-note">加载失败：' + escapeHtml(err.message) + '</div>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  fetchCollections();
});
