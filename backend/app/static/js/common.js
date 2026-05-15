function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
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

// Utility: format number
function formatNumber(n) {
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return String(n);
}
