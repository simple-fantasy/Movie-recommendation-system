document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('create-form');
  if (!form) return;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const name = document.getElementById('name').value.trim();
    const description = document.getElementById('description').value.trim();
    const is_public = document.getElementById('is_public').checked;
    const allow_comments = document.getElementById('allow_comments').checked;

    if (!name) {
      alert('请输入影单名称');
      return;
    }

    try {
      const response = await api('/api/movie-lists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description,
          is_public,
          allow_comments,
        }),
      });

      if (response.success) {
        alert('影单创建成功！');
        window.location.href = `/movie-lists/${response.movie_list.id}`;
      } else {
        alert('创建失败: ' + (response.error || '未知错误'));
      }
    } catch (error) {
      console.error('创建影单失败:', error);
      alert('创建失败，请稍后重试');
    }
  });
});