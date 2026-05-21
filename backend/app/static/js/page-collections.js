function renderStats(stats) {
  const ids = ['favorite', 'watchlist', 'seen', 'total'];
  ids.forEach((key) => {
    const el = document.getElementById('stat-' + key);
    if (el) el.textContent = stats[key] != null ? stats[key] : '-';
  });
}

function renderStars(rating) {
  if (!rating) return '';
  const full = Math.floor(rating);
  const half = rating - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return (
    '<span style="color:#f59e0b;">' +
    '★'.repeat(full) +
    (half ? '☆' : '') +
    '</span>' +
    '<span style="color:#475569;">' +
    '★'.repeat(empty) +
    '</span>'
  );
}

async function fetchCollections() {
  const box = document.getElementById('collections-list');
  if (!box) return;
  box.innerHTML = '<div class="text-center py-4"><span class="small-note">加载中...</span></div>';
  try {
    const params = new URLSearchParams(window.location.search);
    const type = params.get('type') || '';
    const url = '/api/my/collections' + (type ? '?type=' + encodeURIComponent(type) : '');
    const response = await api(url);
    const collections = response.collections || [];
    const stats = response.stats || {};

    renderStats(stats);

    if (!collections.length) {
      box.innerHTML = '<div class="text-center text-secondary py-5"><div style="font-size:3rem;">📭</div><p>暂无收藏记录</p><p class="small">去浏览电影并将喜欢的内容加入收藏吧</p><a href="/app" class="btn btn-cinema btn-sm mt-2">去浏览</a></div>';
      return;
    }

    const typeLabels = { favorite: '收藏', watchlist: '想看', seen: '已看' };
    const typeClass = { favorite: 'type-favorite', watchlist: 'type-watchlist', seen: 'type-seen' };

    box.innerHTML = collections
      .map((item) => {
        const movie = item.movie || {};
        const title = escapeHtml(movie.title || '未知电影');
        const year = movie.year || '-';
        const genres = movie.genres || '-';
        const poster = movie.poster_url || '';
        const typeLabel = typeLabels[item.collection_type] || item.collection_type;
        const typeCls = typeClass[item.collection_type] || '';
        const notes = item.notes ? '<div class="small-note mt-1">📝 ' + escapeHtml(item.notes) + '</div>' : '';
        const ratingHtml = item.rating
          ? '<div class="small-note">' + renderStars(item.rating) + ' (' + item.rating + ')</div>'
          : '';
        const timeStr = item.created_at || '';

        return `
          <div class="list-item">
            ${
              poster
                ? '<img class="poster-thumb" src="' + escapeHtml(poster) + '" alt="' + escapeHtml(title) + '" loading="lazy" onerror="this.style.display=\'none\'">'
                : '<div class="poster-thumb d-flex align-items-center justify-content-center" style="background:var(--cinema-surface);color:var(--cinema-accent);font-weight:700;font-size:18px;">' + escapeHtml(title.charAt(0)) + '</div>'
            }
            <div class="flex-grow-1">
              <div class="d-flex justify-content-between align-items-start">
                <div>
                  <span class="type-badge ${typeCls}">${typeLabel}</span>
                  <span class="fw-semibold ms-2">${title}</span>
                  <span class="small-note ms-2">(${year})</span>
                </div>
                <button class="btn btn-sm btn-outline-danger btn-remove-collection" data-id="${item.id}">移除</button>
              </div>
              <div class="small-note mt-1">${escapeHtml(genres)}</div>
              ${ratingHtml}
              ${notes}
              <div class="small-note mt-1" style="font-size:11px;">创建于 ${timeStr}</div>
            </div>
          </div>
        `;
      })
      .join('');

    box.querySelectorAll('.btn-remove-collection').forEach((button) => {
      button.addEventListener('click', async () => {
        const collectionId = button.dataset.id;
        if (!collectionId) return;
        button.disabled = true;
        try {
          await api('/api/collections/' + collectionId, { method: 'DELETE' });
          await fetchCollections();
          showToast('已移除收藏', 'success');
        } catch (err) {
          showToast('移除失败：' + err.message, 'error');
        } finally {
          button.disabled = false;
        }
      });
    });
  } catch (err) {
    box.innerHTML = '<div class="small-note text-danger">加载失败：' + escapeHtml(err.message) + '</div>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  fetchCollections();

  const filterAll = document.getElementById('filter-all');
  const filterFavorite = document.getElementById('filter-favorite');
  const filterWatchlist = document.getElementById('filter-watchlist');
  const filterSeen = document.getElementById('filter-seen');
  const btnRefresh = document.getElementById('btnRefresh');

  if (btnRefresh) btnRefresh.onclick = fetchCollections;

  function setFilter(type) {
    const url = new URL(window.location);
    if (type) {
      url.searchParams.set('type', type);
    } else {
      url.searchParams.delete('type');
    }
    window.history.replaceState({}, '', url);
    fetchCollections();
  }

  if (filterAll) filterAll.onclick = () => setFilter('');
  if (filterFavorite) filterFavorite.onclick = () => setFilter('favorite');
  if (filterWatchlist) filterWatchlist.onclick = () => setFilter('watchlist');
  if (filterSeen) filterSeen.onclick = () => setFilter('seen');
});
