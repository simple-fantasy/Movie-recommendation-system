const GENRE_MAP = {
  'Action': '动作',
  'Adventure': '冒险',
  'Animation': '动画',
  'Children': '儿童',
  'Comedy': '喜剧',
  'Crime': '犯罪',
  'Documentary': '纪录片',
  'Drama': '剧情',
  'Fantasy': '奇幻',
  'Film-Noir': '黑色电影',
  'Horror': '恐怖',
  'Musical': '音乐',
  'Mystery': '悬疑',
  'Romance': '爱情',
  'Sci-Fi': '科幻',
  'Thriller': '惊悚',
  'War': '战争',
  'Western': '西部',
};

function formatGenre(genre) {
  return GENRE_MAP[genre] || genre;
}

function formatGenres(genres) {
  if (!genres) return [];
  if (Array.isArray(genres)) return genres.map(g => formatGenre(g.trim()));
  return String(genres).split('|').map(g => formatGenre(g.trim()));
}

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('search-query');
  const searchForm = document.getElementById('search-form');
  const suggestionsDropdown = document.getElementById('suggestions-dropdown');
  const resultsSection = document.getElementById('results-section');
  const moviesGrid = document.getElementById('movies-grid');
  const resultsCount = document.getElementById('results-count');
  const searchTime = document.getElementById('search-time');
  const paginationEl = document.getElementById('pagination');
  const noResults = document.getElementById('no-results');
  const popularTags = document.getElementById('popular-tags');

  let searchTimeout = null;
  let currentSort = 'relevance';
  let currentQuery = '';
  let currentPage = 1;

  function attachEventListeners() {
    const resetButton = document.getElementById('reset-filters-btn');

    if (searchInput) {
      searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        if (query.length >= 2) {
          clearTimeout(searchTimeout);
          searchTimeout = setTimeout(() => loadSuggestions(query), 300);
        } else {
          hideSuggestions();
        }
      });

      searchInput.addEventListener('blur', () => setTimeout(hideSuggestions, 200));
      searchInput.addEventListener('focus', () => {
        const query = searchInput.value.trim();
        if (query.length >= 2) {
          loadSuggestions(query);
        }
      });

      searchInput.addEventListener('keydown', (event) => {
        const suggestions = Array.from(document.querySelectorAll('.suggestion-item'));
        const active = document.querySelector('.suggestion-item.active');

        if (event.key === 'ArrowDown' && suggestions.length) {
          event.preventDefault();
          const index = active ? suggestions.indexOf(active) : -1;
          const next = suggestions[Math.min(index + 1, suggestions.length - 1)];
          if (active) active.classList.remove('active');
          next?.classList.add('active');
        }

        if (event.key === 'ArrowUp' && suggestions.length) {
          event.preventDefault();
          const index = active ? suggestions.indexOf(active) : suggestions.length;
          const prev = suggestions[Math.max(index - 1, 0)];
          if (active) active.classList.remove('active');
          prev?.classList.add('active');
        }

        if (event.key === 'Enter' && active) {
          event.preventDefault();
          selectSuggestion(active);
        }

        if (event.key === 'Escape') {
          hideSuggestions();
        }
      });
    }

    if (searchForm) {
      searchForm.addEventListener('submit', (event) => {
        event.preventDefault();
        performSearch(1);
      });
    }

    if (resetButton) {
      resetButton.addEventListener('click', resetFilters);
    }

    document.querySelectorAll('.sort-btn').forEach((button) => {
      button.addEventListener('click', () => {
        document.querySelectorAll('.sort-btn').forEach((btn) => btn.classList.remove('active'));
        button.classList.add('active');
        currentSort = button.dataset.sort || 'relevance';
        if (currentQuery) {
          performSearch(1);
        }
      });
    });

    if (suggestionsDropdown) {
      suggestionsDropdown.addEventListener('click', (event) => {
        const item = event.target.closest('.suggestion-item');
        if (item) {
          selectSuggestion(item);
        }
      });
    }

    if (moviesGrid) {
      moviesGrid.addEventListener('click', (event) => {
        const card = event.target.closest('.movie-card[data-movie-id]');
        if (card) {
          const movieId = card.dataset.movieId;
          if (movieId) {
            window.location.href = `/movie/${movieId}`;
          }
        }
      });
    }

    if (paginationEl) {
      paginationEl.addEventListener('click', (event) => {
        const button = event.target.closest('button[data-page]');
        if (button) {
          const page = Number(button.dataset.page);
          if (!Number.isNaN(page)) {
            performSearch(page);
          }
        }
      });
    }

    if (popularTags) {
      popularTags.addEventListener('click', (event) => {
        const tag = event.target.closest('.popular-tag');
        if (tag) {
          const value = tag.dataset.value;
          if (value && searchInput) {
            searchInput.value = value;
            performSearch(1);
          }
        }
      });
    }
  }

  async function loadSuggestions(query) {
    try {
      const data = await api(`/api/search/suggestions?q=${encodeURIComponent(query)}`);
      if (data.suggestions && data.suggestions.length > 0) {
        showSuggestions(data.suggestions);
      } else {
        hideSuggestions();
      }
    } catch (error) {
      hideSuggestions();
    }
  }

  function showSuggestions(suggestions) {
    if (!suggestionsDropdown) return;
    suggestionsDropdown.innerHTML = suggestions.map((suggestion) => `
      <div class="suggestion-item" data-value="${escapeHtml(suggestion.value)}" data-type="${escapeHtml(suggestion.type)}">
        <div class="suggestion-type">${suggestion.type === 'movie' ? '电影' : '类别'}</div>
        <div class="suggestion-text">
          ${escapeHtml(suggestion.text)}${suggestion.year ? `<span class="suggestion-year">(${escapeHtml(suggestion.year)})</span>` : ''}
        </div>
      </div>
    `).join('');
    suggestionsDropdown.style.display = 'block';
  }

  function hideSuggestions() {
    if (suggestionsDropdown) {
      suggestionsDropdown.style.display = 'none';
    }
  }

  function selectSuggestion(element) {
    if (!element || !searchInput) return;
    const value = element.dataset.value || element.getAttribute('data-value') || '';
    searchInput.value = value;
    hideSuggestions();
    performSearch(1);
  }

  function resetFilters() {
    const inputs = [
      document.getElementById('genre-filter'),
      document.getElementById('year-min'),
      document.getElementById('year-max'),
      document.getElementById('rating-min'),
      document.getElementById('search-query'),
    ];

    inputs.forEach((input) => {
      if (!input) return;
      if (input.tagName === 'SELECT' || input.tagName === 'INPUT') {
        input.value = '';
      }
    });

    if (resultsSection) {
      resultsSection.style.display = 'none';
    }
    if (noResults) {
      noResults.style.display = 'none';
    }
    if (moviesGrid) {
      moviesGrid.innerHTML = '';
    }
    if (searchInput) {
      searchInput.focus();
    }
  }

  function collectFilters(page = 1) {
    const genre = document.getElementById('genre-filter')?.value || '';
    const yearMin = document.getElementById('year-min')?.value || '';
    const yearMax = document.getElementById('year-max')?.value || '';
    const ratingMin = document.getElementById('rating-min')?.value || '';
    return { genre, yearMin, yearMax, ratingMin, page };
  }

  async function performSearch(page = 1) {
    const query = searchInput?.value.trim() || '';
    const filters = collectFilters(page);
    const hasFilters = query || filters.genre || filters.yearMin || filters.yearMax || filters.ratingMin;
    if (!hasFilters) {
      showToast('请输入搜索条件或选择筛选器', 'error');
      return;
    }

    currentQuery = query;
    currentPage = page;

    if (resultsSection) {
      resultsSection.style.display = 'none';
    }
    if (noResults) {
      noResults.style.display = 'none';
    }
    if (moviesGrid) {
      showLoading(moviesGrid, '搜索中...');
    }

    try {
      const params = new URLSearchParams({
        q: query,
        genre: filters.genre,
        year_min: filters.yearMin,
        year_max: filters.yearMax,
        rating_min: filters.ratingMin,
        sort_by: currentSort,
        page: String(page),
        per_page: '20',
      });
      const data = await api(`/api/search/advanced?${params.toString()}`);
      if (data.error) {
        throw new Error(data.error);
      }
      displayResults(data);
    } catch (error) {
      if (moviesGrid) {
        renderStateMessage(moviesGrid, 'error', '搜索失败', error.message || '请稍后重试。');
      }
    }
  }

  function displayResults(data) {
    if (moviesGrid) {
      moviesGrid.innerHTML = '';
    }
    if (resultsSection) {
      resultsSection.style.display = 'block';
    }
    if (resultsCount) {
      resultsCount.textContent = `找到 ${data.pagination?.total || 0} 部电影`;
    }
    if (searchTime) {
      searchTime.textContent = `搜索耗时: ${data.search_time || '--'}`;
    }

    const items = Array.isArray(data.results) ? data.results : [];
    if (!items.length) {
      if (moviesGrid) {
        renderStateMessage(moviesGrid, 'info', '没有找到结果', '请尝试更换关键词或调整筛选条件。');
      }
      if (paginationEl) {
        paginationEl.innerHTML = '';
      }
      return;
    }

    if (moviesGrid) {
      moviesGrid.innerHTML = items.map((movie) => {
          const poster = movie.poster_url || movie.poster;
          const title = escapeHtml(movie.title);
          const posterHTML = hasValidPoster(poster)
            ? `<img src="${poster}" alt="${title}" class="movie-poster" loading="lazy" onerror="this.replaceWith(this.nextElementSibling)" />`
            : '';
          const fallbackHTML = posterHTML
            ? `<div class="poster-gradient" style="display:none;${posterGradientStyle(movie.title)}"><span class="poster-initial">${posterInitial(movie.title)}</span></div>`
            : `<div class="poster-gradient" style="${posterGradientStyle(movie.title)}"><span class="poster-initial">${posterInitial(movie.title)}</span></div>`;
          return `
        <div class="movie-card" data-movie-id="${movie.id}">
          ${posterHTML}${fallbackHTML}
          <div class="movie-info">
            <h3 class="movie-title">${escapeHtml(movie.title)}</h3>
            <div class="movie-meta">
              <span class="movie-year">${escapeHtml(movie.year || '未知')}</span>
              <div class="movie-rating">⭐ ${escapeHtml(movie.avg_rating ? movie.avg_rating.toFixed(1) : 'N/A')}</div>
            </div>
            <div class="movie-genres">${formatGenres(movie.genres).slice(0, 3).map((genre) => `<span class="genre-tag">${escapeHtml(genre)}</span>`).join('')}</div>
          </div>
        </div>
      `;}).join('');
    }
    renderPagination(data.pagination || {});
  }

  function renderPagination(pagination) {
    if (!paginationEl) return;
    const page = pagination.page || 1;
    const pages = pagination.pages || 1;
    if (pages <= 1) {
      paginationEl.innerHTML = '';
      return;
    }

    const buttons = [];
    if (pagination.has_prev) {
      buttons.push(`<button class="page-btn" type="button" data-page="${page - 1}">上一页</button>`);
    }
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(pages, page + 2);

    if (startPage > 1) {
      buttons.push(`<button class="page-btn" type="button" data-page="1">1</button>`);
      if (startPage > 2) {
        buttons.push(`<span class="page-btn" disabled>...</span>`);
      }
    }

    for (let index = startPage; index <= endPage; index += 1) {
      buttons.push(`<button class="page-btn ${index === page ? 'active' : ''}" type="button" data-page="${index}">${index}</button>`);
    }

    if (endPage < pages) {
      if (endPage < pages - 1) {
        buttons.push(`<span class="page-btn" disabled>...</span>`);
      }
      buttons.push(`<button class="page-btn" type="button" data-page="${pages}">${pages}</button>`);
    }
    if (pagination.has_next) {
      buttons.push(`<button class="page-btn" type="button" data-page="${page + 1}">下一页</button>`);
    }

    paginationEl.innerHTML = buttons.join('');
  }

  async function loadPopularSearches() {
    try {
      const data = await api('/api/search/history');
      if (data.popular_searches && Array.isArray(data.popular_searches)) {
        renderPopularSearchTags(data.popular_searches);
        return;
      }
    } catch (error) {
      // Ignore and show default tags
    }
    renderPopularSearchTags(['动作', '喜剧', '科幻', '爱情', '恐怖', '高分', '经典']);
  }

  function renderPopularSearchTags(tags) {
    if (!popularTags) return;
    popularTags.innerHTML = tags.map((value) => `<div class="popular-tag" data-value="${escapeHtml(value)}">${escapeHtml(value)}</div>`).join('');
  }

  function searchPopular(value) {
    if (!searchInput) return;
    searchInput.value = value;
    performSearch(1);
  }

  attachEventListeners();
  loadPopularSearches();
});
