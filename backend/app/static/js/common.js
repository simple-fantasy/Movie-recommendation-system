function escapeHtml(value) {
  const div = document.createElement('div');
  div.textContent = value == null ? '' : String(value);
  return div.innerHTML;
}

function formatMovieTitle(title) {
  if (!title) return '';
  const patterns = [
    { suffix: ', The', prefix: 'The ' },
    { suffix: ', A', prefix: 'A ' },
    { suffix: ', An', prefix: 'An ' },
  ];
  for (const pattern of patterns) {
    if (title.endsWith(pattern.suffix)) {
      return pattern.prefix + title.slice(0, -pattern.suffix.length);
    }
  }
  return title;
}

function createToastContainer() {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  return container;
}

function showToast(message, type = 'success', duration = 3000) {
  const container = createToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast-custom toast-${type}`;

  const icon = type === 'error' ? '⚠️' : '✅';
  toast.innerHTML = `<span style="font-size:1.1rem;">${icon}</span><span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  window.requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(0)';
  });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }, duration);
}

function showLoading(container, label = '加载中...') {
  if (!container) return;
  container.innerHTML = `
    <div class="d-flex flex-column align-items-center justify-content-center py-5">
      <div class="spinner-border mb-3" role="status" style="color: var(--cinema-accent, #e5a00d); width: 3rem; height: 3rem;">
        <span class="visually-hidden">Loading...</span>
      </div>
      <div style="color: var(--cinema-text-secondary, #a3a3a3);">${escapeHtml(label)}</div>
    </div>
  `;
}

function hideLoading(container) {
  if (!container) return;
  container.innerHTML = '';
}

function renderStateMessage(container, type, title, message, actionsHtml = '') {
  if (!container) return;
  container.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">${type === 'error' ? '⚠️' : '🎬'}</div>
      <h5>${escapeHtml(title)}</h5>
      <p>${escapeHtml(message)}</p>
      ${actionsHtml}
    </div>
  `;
}

// Utility: debounce
function debounce(fn, wait = 300) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), wait);
  };
}

// Utility: render star rating HTML
function renderStars(rating) {
  if (rating == null) return '';
  const fullStars = Math.floor(rating);
  const halfStar = rating % 1 >= 0.5;
  let stars = '';
  for (let i = 1; i <= 5; i++) {
    if (i <= fullStars) stars += '★';
    else if (i === fullStars + 1 && halfStar) stars += '½';
    else stars += '☆';
  }
  return `<span class="rating-star">${stars}</span>`;
}

// Utility: translate genre English → Chinese
function formatGenre(genre) {
  const map = window.GENRE_MAP || {};
  return map[genre] || genre;
}

// Utility: format number
function formatNumber(n) {
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return String(n);
}

/**
 * Normalize any movie-like object to a consistent shape.
 * Handles backend field name variations (movie_id vs id, score vs avg_rating, etc).
 */
function normalizeMovie(raw) {
  if (!raw || typeof raw !== 'object') return { id: null, title: '未知电影', year: null, genres: '', avg_rating: null, rating_count: 0, poster: null, backdrop: null, overview: null };
  const posterUrl = raw.poster || raw.poster_url || null;
  const backdropUrl = raw.backdrop || raw.backdrop_url || null;
  return {
    id: raw.id || raw.movie_id || null,
    title: raw.title || raw.name || '未知电影',
    year: raw.year || null,
    genres: raw.genres || '',
    avg_rating: raw.avg_rating !== undefined && raw.avg_rating !== null ? raw.avg_rating : (raw.score !== undefined && raw.score !== null ? raw.score : null),
    rating_count: raw.rating_count || 0,
    poster: optimizePosterUrl(posterUrl, 'w342'),
    poster_original: posterUrl,
    backdrop: optimizePosterUrl(backdropUrl, 'w780'),
    backdrop_original: backdropUrl,
    overview: raw.overview || raw.description || null,
    user_rating: raw.user_rating || raw.rating || null,
    director: raw.director || null,
    actors: raw.actors || null,
    runtime: raw.runtime || null,
    reason: raw.reason || null,
    because: raw.because || null,
    // Keep original fields for passthrough
    _raw: raw
  };
}

// ── Poster gradient fallback utilities ──

const POSTER_GRADIENTS = [
  ['#667eea', '#764ba2'], ['#f093fb', '#f5576c'], ['#4facfe', '#00f2fe'],
  ['#43e97b', '#38f9d7'], ['#fa709a', '#fee140'], ['#a18cd1', '#fbc2eb'],
  ['#fad0c4', '#ffd1ff'], ['#ffecd2', '#fcb69f'],
];

function _hashStr(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) { h = ((h << 5) - h) + str.charCodeAt(i); h |= 0; }
  return Math.abs(h);
}

function hasValidPoster(url) {
  if (!url || typeof url !== 'string') return false;
  return url.startsWith('http') && !url.includes('placeholder') && !url.includes('no-poster');
}

/**
 * Rewrite TMDB image URL to a smaller/larger size for performance.
 * TMDB sizes: w92, w154, w185, w342, w500, w780, w1280, original
 * Default: w342 (good for cards up to ~300px wide on 2x displays)
 */
function optimizePosterUrl(url, size) {
  if (!url || !url.includes('image.tmdb.org/t/p/')) return url;
  return url.replace(/\/t\/p\/\w+\//, '/t/p/' + (size || 'w342') + '/');
}

function posterGradientStyle(title) {
  const pair = POSTER_GRADIENTS[_hashStr(title || '') % POSTER_GRADIENTS.length];
  return `background: linear-gradient(135deg, ${pair[0]}, ${pair[1]});`;
}

function posterInitial(title) {
  if (!title) return '?';
  const ch = title.charAt(0);
  return /[a-zA-Z一-鿿]/.test(ch) ? ch.toUpperCase() : title.charAt(1) || ch;
}

// English-to-Chinese genre mapping (shared across pages)
window.GENRE_MAP = {
  'Action': '动作', 'Adventure': '冒险', 'Animation': '动画', 'Children': '儿童',
  'Comedy': '喜剧', 'Crime': '犯罪', 'Documentary': '纪录片', 'Drama': '剧情',
  'Fantasy': '奇幻', 'Film-Noir': '黑色电影', 'Horror': '恐怖', 'Musical': '音乐',
  'Mystery': '悬疑', 'Romance': '爱情', 'Sci-Fi': '科幻', 'Thriller': '惊悚',
  'War': '战争', 'Western': '西部',
};
