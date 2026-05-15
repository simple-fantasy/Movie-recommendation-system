function renderStars(rating) {
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
  return `<span class="rating-star">${stars}</span> <span class="small-note">(${rating})</span>`;
}

async function loadRatings() {
  const list = document.getElementById('ratings-list');
  if (!list) return;
  list.innerHTML = '<div class="text-center py-4"><span class="small-note">加载中...</span></div>';

  try {
    const data = await api('/api/my/ratings?limit=100');

    // 计算统计数据
    if (data.length > 0) {
      const ratings = data.map((r) => r.rating);
      const count = ratings.length;
      const avg = (ratings.reduce((a, b) => a + b, 0) / count).toFixed(1);
      const max = Math.max(...ratings).toFixed(1);
      const min = Math.min(...ratings).toFixed(1);

      const statCount = document.getElementById('stat-count');
      const statAvg = document.getElementById('stat-avg');
      const statMax = document.getElementById('stat-max');
      const statMin = document.getElementById('stat-min');

      if (statCount) statCount.textContent = count;
      if (statAvg) statAvg.textContent = avg;
      if (statMax) statMax.textContent = max;
      if (statMin) statMin.textContent = min;

      // 计算评分分布（0.5-5.0，分成10个区间）
      const histogram = new Array(10).fill(0);
      for (const r of ratings) {
        const idx = Math.min(Math.floor((r - 0.5) / 0.5), 9);
        histogram[idx]++;
      }
      const maxCount = Math.max(...histogram);
      const bars = document.querySelectorAll('.hist-bar');
      bars.forEach((bar, i) => {
        bar.style.height = maxCount > 0 ? `${(histogram[i] / maxCount) * 100}%` : '4px';
      });
    }

    if (!data || !data.length) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">⭐</div>
          <p>暂无评分记录</p>
          <p class="small-note">去搜索并评分喜欢的电影吧</p>
          <a href="/app" class="btn btn-primary mt-3">去评分</a>
        </div>
      `;
      return;
    }

    let html = '<div class="list-group">';
    for (const r of data) {
      const title = formatMovieTitle(r.title || '未知电影');
      const timeStr = r.timestamp ? new Date(r.timestamp).toLocaleString('zh-CN') : '未知时间';
      html += `
        <div class="list-group-item list-group-item-action">
          <div class="d-flex justify-content-between align-items-start">
            <div class="flex-grow-1">
              <div class="fw-semibold">${escapeHtml(title)}</div>
              <div class="small-note mt-1">${renderStars(r.rating)}</div>
              <div class="small-note">${escapeHtml(r.genres || '未分类')} | ID: ${r.movie_id}</div>
              <div class="small-note">评分于 ${timeStr}</div>
            </div>
            <a href="/movie/${r.movie_id}" class="btn btn-sm btn-outline-primary ml-3">详情</a>
          </div>
        </div>
      `;
    }
    html += '</div>';
    list.innerHTML = html;
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

async function initAuth() {
  try {
    const data = await api('/api/me');
    if (data.authenticated) {
      setAuthUI(true, data.username, data.is_admin);
      loadRatings();
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
  btnRefresh.onclick = loadRatings;
}

initAuth();
