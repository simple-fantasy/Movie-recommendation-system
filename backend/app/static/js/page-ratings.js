function renderStats(stats) {
  if (!stats || !stats.count) return;
  const statCount = document.getElementById('stat-count');
  const statAvg = document.getElementById('stat-avg');
  const statMax = document.getElementById('stat-max');
  const statMin = document.getElementById('stat-min');
  if (statCount) statCount.textContent = stats.count;
  if (statAvg) statAvg.textContent = stats.avg;
  if (statMax) statMax.textContent = stats.max;
  if (statMin) statMin.textContent = stats.min;

  // 渲染评分分布直方图
  if (stats.histogram) {
    const maxCount = Math.max(...stats.histogram, 1);
    const bars = document.querySelectorAll('.hist-bar');
    bars.forEach((bar, i) => {
      const val = stats.histogram[i] || 0;
      bar.style.height = maxCount > 0 ? (val / maxCount) * 100 + '%' : '4px';
    });
  }
}

function renderStars(rating) {
  if (!rating) return '';
  const full = Math.floor(rating);
  const half = rating - full >= 0.3 ? 1 : 0;
  return '★'.repeat(full) + (half ? '☆' : '') + '★'.repeat(5 - full - half).replace(/★/g, '<span style="color:#475569;">★</span>');
}

async function loadRatings() {
  const list = document.getElementById('ratings-list');
  if (!list) return;
  list.innerHTML = '<div class="text-center py-4"><span class="small-note">加载中...</span></div>';

  try {
    const data = await api('/api/my/ratings?limit=100');
    const ratings = data.ratings || [];
    const stats = data.stats || {};

    renderStats(stats);

    if (!ratings.length) {
      list.innerHTML = `
        <div class="text-center text-secondary py-5">
          <div style="font-size:3rem;">⭐</div>
          <p>暂无评分记录</p>
          <p class="small">去搜索并评分喜欢的电影吧</p>
          <a href="/app" class="btn btn-cinema btn-sm mt-2">去评分</a>
        </div>
      `;
      return;
    }

    let html = '<div class="list-group">';
    for (const r of ratings) {
      const title = formatMovieTitle(r.title || '未知电影');
      const timeStr = r.timestamp ? new Date(r.timestamp).toLocaleString('zh-CN') : '未知时间';
      const posterHtml = r.poster_url
        ? '<img class="poster-thumb" src="' + escapeHtml(r.poster_url) + '" alt="' + escapeHtml(title) + '" loading="lazy" onerror="this.style.display=\'none\'">'
        : '';
      html += `
        <div class="list-item">
          ${posterHtml}
          <div class="flex-grow-1">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <div class="fw-semibold">${escapeHtml(title)}</div>
                <div class="small-note mt-1">${renderStars(r.rating)} <span class="small-note">(${r.rating})</span></div>
                <div class="small-note">${escapeHtml(r.genres || '未分类')}</div>
                <div class="small-note">评分于 ${timeStr}</div>
              </div>
              <a href="/movie/${r.movie_id}" class="btn btn-sm btn-outline-primary">详情</a>
            </div>
          </div>
        </div>
      `;
    }
    html += '</div>';
    list.innerHTML = html;
  } catch (err) {
    if (err.message.includes('401') || err.message.includes('登录')) {
      list.innerHTML = `
        <div class="text-center text-secondary py-5">
          <div style="font-size:3rem;">🔒</div>
          <p>请先登录</p>
          <a href="/login" class="btn btn-cinema btn-sm mt-2">去登录</a>
        </div>
      `;
    } else {
      list.innerHTML = '<div class="small-note text-danger">加载失败：' + escapeHtml(err.message) + '</div>';
    }
  }
}

function setAuthUI(loggedIn, username, isAdmin) {
  const authStatus = document.getElementById('authStatus');
  const btnLogin = document.getElementById('btnLoginPage');
  const btnLogout = document.getElementById('btnLogout');
  const adminNav = document.getElementById('adminNavItem');
  if (authStatus) authStatus.textContent = loggedIn ? '已登录：' + username : '未登录';
  if (btnLogin) btnLogin.style.display = loggedIn ? 'none' : 'inline-block';
  if (btnLogout) btnLogout.style.display = loggedIn ? 'inline-block' : 'none';
  if (adminNav) adminNav.style.display = loggedIn && isAdmin ? 'block' : 'none';
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
