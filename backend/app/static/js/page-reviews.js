function renderStars(rating) {
  if (!rating) return '';
  const fullStars = Math.floor(rating);
  const halfStar = rating % 1 >= 0.5;
  let stars = '';
  for (let i = 1; i <= 5; i++) {
    if (i <= fullStars) {
      stars += '★';
    } else if (i === fullStars + 1 && halfStar) {
      stars += '½';
    } else {
      stars += '☆';
    }
  }
  return `<span class="rating-star">${stars}</span>`;
}

function getStatusBadge(status) {
  const badges = {
    approved: { class: 'bg-green-100 text-green-700', text: '已通过' },
    pending: { class: 'bg-yellow-100 text-yellow-700', text: '待审核' },
    rejected: { class: 'bg-red-100 text-red-700', text: '已拒绝' },
  };
  const b = badges[status] || badges.approved;
  return `<span class="badge ${b.class}">${b.text}</span>`;
}

async function loadReviews() {
  const list = document.getElementById('reviews-list');
  if (!list) return;
  list.innerHTML = '<div class="text-center py-4"><span class="small-note">加载中...</span></div>';

  try {
    const data = await api('/api/my/reviews');

    // 计算统计数据
    if (data.reviews && data.reviews.length > 0) {
      const count = data.reviews.length;
      const totalLikes = data.reviews.reduce((sum, r) => sum + (r.likes_count || 0), 0);
      const avgLikes = count > 0 ? (totalLikes / count).toFixed(1) : '0';

      const statCount = document.getElementById('stat-count');
      const statLikes = document.getElementById('stat-likes');
      const statAvgLikes = document.getElementById('stat-avg-likes');

      if (statCount) statCount.textContent = count;
      if (statLikes) statLikes.textContent = totalLikes;
      if (statAvgLikes) statAvgLikes.textContent = avgLikes;
    }

    if (!data.reviews || !data.reviews.length) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">💬</div>
          <p>暂无评论记录</p>
          <p class="small-note">去电影详情页发表你的评论吧</p>
          <a href="/app" class="btn btn-primary mt-3">去发现电影</a>
        </div>
      `;
      return;
    }

    let html = '<div class="space-y-4">';
    for (const r of data.reviews) {
      const movieTitle = formatMovieTitle(r.movie?.title || '未知电影');
      const timeStr = new Date(r.created_at).toLocaleString('zh-CN');
      html += `
        <div class="card p-4">
          <div class="d-flex justify-content-between align-items-start mb-3">
            <div>
              <a href="/movie/${r.movie?.id || r.movie_id}" class="fw-semibold text-dark">${escapeHtml(movieTitle)}</a>
              ${renderStars(r.rating)}
            </div>
            <div class="d-flex gap-2">
              ${getStatusBadge(r.status)}
              <button type="button" class="btn btn-sm btn-outline-danger btn-delete-review" data-review-id="${r.id}">删除</button>
            </div>
          </div>
          <div class="review-content text-muted mb-3">${escapeHtml(r.content)}</div>
          <div class="d-flex justify-content-between small-note">
            <span>👍 ${r.likes_count || 0} 赞</span>
            <span>${timeStr}</span>
          </div>
        </div>
      `;
    }
    html += '</div>';
    list.innerHTML = html;
    list.querySelectorAll('.btn-delete-review').forEach((button) => {
      const reviewId = Number(button.dataset.reviewId);
      if (Number.isNaN(reviewId)) return;
      button.addEventListener('click', async () => {
        await deleteReview(reviewId);
      });
    });
  } catch (err) {
    if (err.message.includes('401') || err.message.includes('登录')) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🔒</div>
          <p>请先登录</p>
          <a href="/login" class="btn btn-primary mt-3">去登录</a>
        </div>
      `;
    } else {
      list.innerHTML = `<div class="small-note text-danger">加载失败：${escapeHtml(err.message)}</div>`;
    }
  }
}

async function deleteReview(id) {
  if (!confirm('确定要删除这条评论吗？')) return;
  try {
    await api('/api/reviews/' + id, { method: 'DELETE' });
    await loadReviews();
  } catch (err) {
    alert('删除失败：' + err.message);
  }
}

async function postReview() {
  const movieId = document.getElementById('new-movie-id')?.value.trim();
  const rating = document.getElementById('new-rating')?.value;
  const content = document.getElementById('new-content')?.value.trim();
  const msg = document.getElementById('post-msg');

  if (msg) msg.textContent = '';

  if (!movieId) {
    if (msg) msg.textContent = '请输入电影ID';
    return;
  }

  if (!content) {
    if (msg) msg.textContent = '请输入评论内容';
    return;
  }

  if (content.length < 5) {
    if (msg) msg.textContent = '评论内容至少需要5个字符';
    return;
  }

  try {
    await api('/api/reviews', {
      method: 'POST',
      body: JSON.stringify({
        movie_id: parseInt(movieId),
        rating: rating ? parseFloat(rating) : undefined,
        content: content,
      }),
    });

    if (msg) {
      msg.textContent = '评论发表成功！';
      msg.style.color = 'green';
    }
    const idInput = document.getElementById('new-movie-id');
    const ratingInput = document.getElementById('new-rating');
    const contentInput = document.getElementById('new-content');
    if (idInput) idInput.value = '';
    if (ratingInput) ratingInput.value = '';
    if (contentInput) contentInput.value = '';
    await loadReviews();
  } catch (err) {
    if (msg) {
      msg.textContent = '发表失败：' + err.message;
      msg.style.color = 'red';
    }
  }
}

function setAuthUI(loggedIn, username, isAdmin) {
  const authStatus = document.getElementById('authStatus');
  const btnLogin = document.getElementById('btnLoginPage');
  const btnLogout = document.getElementById('btnLogout');
  const adminNav = document.getElementById('adminNavItem');
  if (authStatus) authStatus.textContent = loggedIn ? `已登录：${username}` : '未登录';
  if (btnLogin) btnLogin.style.display = loggedIn ? 'none' : 'inline-block';
  if (btnLogout) btnLogout.style.display = loggedIn ? 'inline-block' : 'none';
  if (adminNav) adminNav.style.display = loggedIn && isAdmin ? 'block' : 'none';
}

async function initAuth() {
  try {
    const data = await api('/api/me');
    if (data.authenticated) {
      setAuthUI(true, data.username, data.is_admin);
      await loadReviews();
    } else {
      setAuthUI(false, '');
    }
  } catch (_err) {
    setAuthUI(false, '');
  }
}

const btnLogout = document.getElementById('btnLogout');
if (btnLogout) {
  btnLogout.onclick = async () => {
    try {
      await api('/api/auth/logout', { method: 'POST', body: '{}' });
      window.location.reload();
    } catch (err) {
      alert('退出失败：' + err.message);
    }
  };
}

const btnRefresh = document.getElementById('btnRefresh');
if (btnRefresh) {
  btnRefresh.onclick = loadReviews;
}

const btnPostReview = document.getElementById('btn-post-review');
if (btnPostReview) {
  btnPostReview.onclick = postReview;
}

initAuth();
