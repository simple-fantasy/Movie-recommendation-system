/* =========================================
   Admin shared utilities
   Load AFTER common.js in admin templates
   ========================================= */

function showAlert(type, message) {
  const alert = document.createElement('div');
  alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
  alert.innerHTML = `
    ${escapeHtml(message)}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  document.body.appendChild(alert);
  setTimeout(() => {
    if (alert.parentNode) alert.parentNode.removeChild(alert);
  }, 3000);
}

function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function renderPagination(containerEl, pagination, onPageChange) {
  if (!containerEl) return;
  const pages = pagination.pages || 1;
  const page = pagination.page || 1;
  if (pages <= 1) {
    containerEl.innerHTML = '';
    return;
  }
  let html = '';
  if (pagination.has_prev) {
    html += `<li class="page-item"><button type="button" class="page-link" data-page="${page - 1}">上一页</button></li>`;
  }
  const startPage = Math.max(1, page - 2);
  const endPage = Math.min(pages, page + 2);
  for (let i = startPage; i <= endPage; i += 1) {
    html += `<li class="page-item ${i === page ? 'active' : ''}"><button type="button" class="page-link" data-page="${i}">${i}</button></li>`;
  }
  if (pagination.has_next) {
    html += `<li class="page-item"><button type="button" class="page-link" data-page="${page + 1}">下一页</button></li>`;
  }
  containerEl.innerHTML = html;

  // Use a single delegated listener; avoid duplicates via flag
  if (!containerEl.dataset.paginationBound) {
    containerEl.dataset.paginationBound = '1';
    containerEl.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-page]');
      if (!button) return;
      const p = Number(button.dataset.page);
      if (!Number.isNaN(p) && typeof onPageChange === 'function') {
        onPageChange(p);
      }
    });
  }
}
