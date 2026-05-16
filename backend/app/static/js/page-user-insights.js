async function loadInsights() {
  try {
    const data = await api('/api/user/insights');

    if (data.insights && data.insights.length > 0) {
      displayInsights(data.insights);
    } else {
      displayEmptyState();
    }
  } catch (error) {
    console.error('加载用户洞察失败:', error);
    const grid = document.getElementById('insights-grid');
    if (grid) {
      if (error.message.includes('401') || error.message.includes('登录')) {
        grid.innerHTML = `
          <div class="col-12">
            <div class="empty-state">
              <div class="empty-state-icon">🔒</div>
              <h3>请先登录</h3>
              <p>登录后可查看个性化用户洞察</p>
              <a href="/login" class="btn btn-primary mt-3">去登录</a>
            </div>
          </div>
        `;
      } else {
        grid.innerHTML = `
          <div class="col-12">
            <div class="empty-state">
              <div class="empty-state-icon">⚠️</div>
              <h3>加载失败</h3>
              <p>${escapeHtml(error.message || '请稍后重试')}</p>
            </div>
          </div>
        `;
      }
    }
  } finally {
    const loading = document.getElementById('loading');
    const content = document.getElementById('insights-content');
    if (loading) loading.style.setProperty('display', 'none', 'important');
    if (content) content.style.setProperty('display', 'block', 'important');
  }
}

function displayInsights(insights) {
  const grid = document.getElementById('insights-grid');
  if (!grid) return;

  grid.innerHTML = '';

  insights.forEach((insight, index) => {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4';

    const card = document.createElement('div');
    card.className = 'card';
    card.style.animationDelay = `${index * 0.1}s`;

    const body = document.createElement('div');
    body.className = 'card-body text-center';

    const icon = document.createElement('div');
    icon.className = 'insight-icon';
    icon.textContent = insight.icon;

    const title = document.createElement('h5');
    title.className = 'insight-title';
    title.textContent = insight.title;

    const description = document.createElement('p');
    description.className = 'insight-description';
    description.textContent = insight.description;

    body.appendChild(icon);
    body.appendChild(title);
    body.appendChild(description);
    card.appendChild(body);
    col.appendChild(card);
    grid.appendChild(col);
  });
}

function displayEmptyState() {
  const grid = document.getElementById('insights-grid');
  if (!grid) return;

  grid.innerHTML = '';
  const col = document.createElement('div');
  col.className = 'col-12';

  const emptyState = document.createElement('div');
  emptyState.className = 'empty-state';
  emptyState.innerHTML = `
    <div class="empty-state-icon">📊</div>
    <h3>暂无洞察数据</h3>
    <p>您需要先进行一些评分、收藏或评论操作，系统才能为您生成个性化洞察。</p>
    <a href="/app" class="btn btn-primary mt-3">开始探索电影</a>
  `;

  col.appendChild(emptyState);
  grid.appendChild(col);
}

function init() { loadInsights(); }
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
