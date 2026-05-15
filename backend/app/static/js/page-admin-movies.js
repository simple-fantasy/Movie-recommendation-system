document.addEventListener('DOMContentLoaded', () => {
  const deleteModalEl = document.getElementById('deleteModal');
  const deleteMovieTitleEl = document.getElementById('deleteMovieTitle');
  const deleteForm = document.getElementById('deleteForm');

  function showAlert(message) {
    window.alert(message);
  }

  async function fetchMetadata(movieId, movieTitle) {
    if (!confirm(`确定要获取《${movieTitle}》的详细信息吗？`)) return;

    try {
      const response = await fetch(`/admin/movies/${movieId}/fetch-metadata`, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      const data = await response.json();

      if (data.success) {
        showAlert('获取成功！页面将刷新显示新数据');
        location.reload();
      } else {
        showAlert('获取失败: ' + (data.message || '未知错误'));
      }
    } catch (error) {
      showAlert('网络错误，请重试');
    }
  }

  function showDeleteModal(movieId, movieTitle) {
    if (!deleteModalEl || !deleteForm || !deleteMovieTitleEl) return;
    deleteMovieTitleEl.textContent = movieTitle;
    deleteForm.action = `/admin/movies/${movieId}/delete`;
    new bootstrap.Modal(deleteModalEl).show();
  }

  document.body.addEventListener('click', (event) => {
    const fetchButton = event.target.closest('.btn-fetch-metadata');
    const deleteButton = event.target.closest('.btn-delete-movie');

    if (fetchButton) {
      const movieId = Number(fetchButton.dataset.id);
      const movieTitle = fetchButton.dataset.title || '';
      if (!Number.isNaN(movieId)) {
        fetchMetadata(movieId, movieTitle);
      }
      return;
    }

    if (deleteButton) {
      const movieId = Number(deleteButton.dataset.id);
      const movieTitle = deleteButton.dataset.title || '';
      if (!Number.isNaN(movieId)) {
        showDeleteModal(movieId, movieTitle);
      }
    }
  });
});
