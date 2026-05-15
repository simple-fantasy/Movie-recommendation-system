document.addEventListener('DOMContentLoaded', () => {
  let currentPage = 1;
  let searchQuery = '';
  let hasMore = true;

  const loadingEl = document.getElementById('loading');
  const contentEl = document.getElementById('lists-content');
  const gridEl = document.getElementById('lists-grid');
  const searchInput = document.getElementById('search-input');
  const loadMoreBtn = document.getElementById('load-more-btn');

  function setLoading(state) {
    if (loadingEl) loadingEl.style.display = state ? 'flex' : 'none';
    if (contentEl) contentEl.style.display = state ? 'none' : 'block';
  }

  function handleSearch() {
    searchQuery = searchInput?.value.trim() || '';
    currentPage = 1;
    setLoading(true);
    loadLists(1);
  }

  function loadMoreLists() {
    if (!hasMore) return;
    loadLists(currentPage + 1);
  }

  async function loadLists(page = 1) {
    try {
      let url = `/api/movie-lists/public?page=${page}`;
      if (searchQuery) {
        url += `&search=${encodeURIComponent(searchQuery)}`;
      }

      const res = await fetch(url);
      const data = await res.json();

      if (data.movie_lists) {
        if (page === 1) {
          gridEl.innerHTML = '';
        }

        displayLists(data.movie_lists);

        if (!data.pagination.has_next) {
          if (loadMoreBtn) loadMoreBtn.style.display = 'none';
          hasMore = false;
        } else {
          if (loadMoreBtn) loadMoreBtn.style.display = 'inline-block';
          hasMore = true;
        }

        currentPage = data.pagination.page;
      }
    } catch (error) {
      console.error('加载影单失败:', error);
      alert('加载影单失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }

  function displayLists(lists) {
    if (!gridEl) return;

    if (lists.length === 0) {
      gridEl.innerHTML = `
        <div class="col-12">
          <div class="empty-state">
            <div class="empty-state-icon">📋</div>
            <h3>暂无影单</h3>
            <p>还没有公开的影单，成为第一个创建者吧！</p>
          </div>
        </div>
      `;
      return;
    }

    lists.forEach(list => {
      const col = document.createElement('div');
      col.className = 'col-md-4 mb-4';

      const card = document.createElement('div');
      card.className = 'card';
      card.onclick = () => window.location.href = `/movie-lists/${list.id}`;

      card.innerHTML = `
        <div class="list-cover">
          ${list.cover_image ? `<img src="${list.cover_image}" alt="${list.name}">` : ''}
          ${list.is_public ? '<span class="public-badge">🌐 公开</span>' : ''}
        </div>
        <div class="list-content">
          <h5 class="list-title">${list.name}</h5>
          <p class="list-description">${list.description || '暂无描述'}</p>
          <div class="list-meta">
            <span>🎬 ${list.movie_count}部电影</span>
            <span>👁️ ${list.view_count}</span>
            <span>❤️ ${list.like_count}</span>
          </div>
          <p class="text-muted mt-2 mb-0" style="font-size: 0.875rem;">
            创建者: ${list.username}
          </p>
        </div>
      `;

      col.appendChild(card);
      gridEl.appendChild(col);
    });
  }

  if (searchInput) {
    searchInput.addEventListener('keyup', handleSearch);
  }
  if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', loadMoreLists);
  }

  loadLists();
});