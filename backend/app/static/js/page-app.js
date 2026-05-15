const pageApiControllers = new Map();

function getFriendlyErrorMessage(status, data) {
  const code = data && data.code;
  const msg = data && data.error;

  if (code === 'MODEL_LOADING') return '🔄 NCF模型正在加载中，请5秒后再试';
  if (code === 'MODEL_NOT_AVAILABLE') return '⚠️ 推荐模型未就绪';
  if (code === 'UNAUTHORIZED' || status === 401) return '🔒 请先登录';
  if (code === 'NOT_FOUND' || status === 404) return '❓ 资源不存在';
  if (code === 'INVALID_PARAM') return '⚠️ ' + (msg || '参数错误');
  if (status === 503) return msg || '🔧 服务暂时不可用';
  if (status >= 500) return '🔧 服务器繁忙，请稍后重试';

  return msg || `请求失败 (${status})`;
}

async function pageApi(path, options = {}, retryCount = 1) {
  if (pageApiControllers.has(path)) {
    pageApiControllers.get(path).abort();
  }
  const controller = new AbortController();
  pageApiControllers.set(path, controller);

  const init = {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    credentials: 'include',
    signal: controller.signal,
    ...options,
  };

  if (options.body !== undefined && options.body !== null && typeof options.body !== 'string') {
    init.body = JSON.stringify(options.body);
  }

  const makeRequest = async () => {
    try {
      const res = await fetch(path, init);
      const ct = res.headers.get('content-type') || '';
      const data = ct.includes('application/json') ? await res.json() : await res.text();
      if (!res.ok) {
        throw new Error(getFriendlyErrorMessage(res.status, data));
      }
      return data;
    } catch (err) {
      if (err.name === 'AbortError') {
        throw new Error('请求已取消');
      }
      throw err;
    } finally {
      pageApiControllers.delete(path);
    }
  };

  let lastError;
  for (let i = 0; i <= retryCount; i++) {
    try {
      return await makeRequest();
    } catch (err) {
      lastError = err;
      if (i < retryCount && !err.message.includes('4')) {
        await new Promise((resolve) => setTimeout(resolve, 800 * (i + 1)));
        continue;
      }
      throw err;
    }
  }
  throw lastError;
}

const ECHARTS_CDNS = [
  '/static/echarts/echarts.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js',
  'https://unpkg.com/echarts@5/dist/echarts.min.js',
  'https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js',
];

function createScript(src, timeoutMs) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    const timer = setTimeout(() => {
      script.remove();
      reject(new Error(`timeout loading ${src}`));
    }, timeoutMs);
    script.onload = () => {
      clearTimeout(timer);
      resolve();
    };
    script.onerror = () => {
      clearTimeout(timer);
      script.remove();
      reject(new Error(`failed to load ${src}`));
    };
    document.head.appendChild(script);
  });
}

async function ensureEcharts() {
  if (window.echarts) return;
  let lastError = null;
  for (const url of ECHARTS_CDNS) {
    try {
      await createScript(url, 2500);
      if (window.echarts) return;
    } catch (err) {
      lastError = err;
    }
  }
  throw lastError || new Error('echarts load failed');
}

function setAuthUI(loggedIn, username, isAdmin = false) {
  const authStatus = document.getElementById('authStatus');
  if (authStatus) authStatus.textContent = loggedIn ? `已登录：${username}` : '未登录';
  const btnLoginPage = document.getElementById('btnLoginPage');
  const btnLogout = document.getElementById('btnLogout');
  const adminNavItem = document.getElementById('adminNavItem');
  if (btnLoginPage) btnLoginPage.style.display = loggedIn ? 'none' : 'inline-block';
  if (btnLogout) btnLogout.style.display = loggedIn ? 'inline-block' : 'none';
  if (adminNavItem) adminNavItem.style.display = loggedIn && isAdmin ? 'block' : 'none';
}

function pickMovie(movie) {
  const movieIdInput = document.getElementById('movieId');
  const movieTitleInput = document.getElementById('movieTitle');
  if (movieIdInput) movieIdInput.value = movie.id;
  if (movieTitleInput) movieTitleInput.value = movie.title;
  loadMovieDetail(movie.id).catch(() => {});
}

async function loadMovieDetail(movieId) {
  const box = document.getElementById('movieDetail');
  if (!box) return;
  box.innerHTML = '<div class="text-center py-3"><span style="opacity:0.6;">加载中...</span></div>';
  try {
    const m = await pageApi(`/api/movies/${movieId}`);
    const formattedTitle = formatMovieTitle(m.title);
    box.innerHTML = `
      <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; color: white;">${escapeHtml(formattedTitle)}</div>
      <div style="display: grid; gap: 0.5rem;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
          <span style="opacity: 0.6;">ID</span>
          <span class="mono">${m.id}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
          <span style="opacity: 0.6;">年份</span>
          <span>${m.year || '-'}</span>
        </div>
        <div style="font-size: 0.85rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 0.5rem; margin-top: 0.25rem;">
          <div style="opacity: 0.6; margin-bottom: 0.25rem;">类型</div>
          <div>${escapeHtml(m.genres || '未分类')}</div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 0.5rem; margin-top: 0.25rem;">
          <span style="opacity: 0.6;">平均评分</span>
          <span style="color: var(--accent-gold); font-weight: 600;">
            ${m.avg_rating === null ? '-' : '⭐ ' + Number(m.avg_rating).toFixed(1)}
            <span style="opacity: 0.6; font-weight: 400;">(${m.rating_count}人)</span>
          </span>
        </div>
      </div>
      <a href="/movie/${m.id}" class="btn btn-sm btn-outline-light mt-3 w-100" style="border-color: rgba(255,255,255,0.3); color: white; font-size: 0.8rem;">
        查看详情 →
      </a>
    `;
  } catch (err) {
    box.innerHTML = `<div class="small-note">加载失败：${escapeHtml(err.message)}</div>`;
  }
}

async function onLogout() {
  try {
    await pageApi('/api/auth/logout', { method: 'POST', body: '{}' });
    setAuthUI(false, '');
    const historyBox = document.getElementById('history');
    if (historyBox) historyBox.innerHTML = '';
    window.location.reload();
  } catch (err) {
    alert('退出失败：' + err.message);
  }
}

async function onSearch() {
  const q = document.getElementById('q')?.value.trim();
  const list = document.getElementById('movies');
  if (!list) return;
  list.innerHTML = '';
  if (!q) return;
  try {
    const movies = await pageApi('/api/movies?q=' + encodeURIComponent(q) + '&limit=20');
    for (const m of movies) {
      const el = document.createElement('div');
      el.className = 'list-group-item list-group-item-action clickable';
      const formattedTitle = formatMovieTitle(m.title);
      el.innerHTML = `<div class="fw-semibold">${escapeHtml(formattedTitle)} <span class="small-note">(${m.year || '-'})</span></div><div class="small-note">ID: <span class="mono">${m.id}</span> | ${escapeHtml(m.genres || '')}</div>`;
      el.onclick = () => pickMovie(m);
      list.appendChild(el);
    }
  } catch (err) {
    showToast('搜索失败：' + err.message, 'error');
  }
}

async function onRate() {
  const movie_id = Number(document.getElementById('movieId')?.value);
  const rating = Number(document.getElementById('rating')?.value);
  const msg = document.getElementById('rateMsg');
  if (msg) msg.textContent = '';
  try {
    await pageApi('/api/ratings', { method: 'POST', body: JSON.stringify({ movie_id, rating }) });
    if (msg) msg.textContent = '评分成功';
    await onLoadHistory();
  } catch (err) {
    if (msg) msg.textContent = '评分失败：' + err.message;
  }
}

async function onSimilar() {
  const movieId = Number(document.getElementById('movieId')?.value);
  const box = document.getElementById('similar');
  if (!box) return;
  box.innerHTML = '';
  if (!movieId) return;
  try {
    const data = await pageApi(`/api/movies/${movieId}/similar?n=10`);
    const items = data.similar || [];
    if (!items.length) {
      box.innerHTML = '<div class="small-note">暂无相似电影（可能还未训练相似度）。</div>';
      return;
    }
    box.innerHTML = items.map(x => `
      <a class="list-group-item list-group-item-action" href="/movie/${x.movie_id}">
        <div class="fw-semibold">${escapeHtml(x.title)}</div>
        <div class="small-note">score: ${x.score.toFixed(3)} | ${escapeHtml(x.genres || '')}</div>
      </a>
    `).join('');
  } catch (err) {
    box.innerHTML = '<div class="small-note">加载失败：' + escapeHtml(err.message) + '</div>';
  }
}

async function renderPersona() {
  await ensureEcharts();
  const box = document.getElementById('chartPersona');
  if (!box) return;
  const chart = echarts.init(box);
  try {
    const data = await pageApi('/api/my/persona?n=8&like_threshold=4.0');
    if (!data.labels || !data.labels.length) {
      chart.dispose();
      box.innerHTML = `
        <div class="text-center py-4">
          <div style="font-size: 3rem; opacity: 0.3;">📊</div>
          <p class="small-note mt-3">
            ${data.note === 'no ratings'
              ? '暂无评分数据<br/>请先搜索并评分几部电影'
              : '暂无画像数据<br/>请给喜欢的电影打 ≥4 分来构建偏好画像'}
          </p>
          <button type="button" class="btn btn-sm btn-outline-primary mt-2" data-action="switch-to-search-tab">
            去评分 →
          </button>
        </div>
      `;
      const switchBtn = box.querySelector('[data-action="switch-to-search-tab"]');
      if (switchBtn) {
        switchBtn.addEventListener('click', () => {
          const tab = new bootstrap.Tab(document.getElementById('tab-search'));
          tab.show();
        });
      }
      return;
    }

    const indicators = data.labels.map((name) => ({ name, max: 100 }));
    chart.setOption({
      tooltip: {},
      radar: { indicator: indicators },
      series: [{ type: 'radar', data: [{ value: data.values, name: '偏好强度' }] }],
    });
    const resizeHandler = () => chart.resize();
    window.addEventListener('resize', resizeHandler);
    box._chartInstance = chart;
    box._resizeHandler = resizeHandler;
  } catch (err) {
    chart.dispose();
    if (err.message.includes('🔒') || err.message.includes('登录') || err.message.includes('401')) {
      box.innerHTML = `
        <div class="text-center py-4">
          <div style="font-size: 3rem; opacity: 0.3;">🔒</div>
          <p class="small-note mt-3">
            登录后查看用户画像<br/>
            我们将分析你的类型偏好
          </p>
          <a href="/login" class="btn btn-sm btn-outline-primary mt-2">去登录 →</a>
        </div>
      `;
    } else {
      box.innerHTML = '<div class="small-note text-danger">' + escapeHtml(err.message) + '</div>';
    }
  }
}

async function renderTimeline() {
  await ensureEcharts();
  const box = document.getElementById('chartTimeline');
  if (!box) return;
  const chart = echarts.init(box);
  try {
    const data = await pageApi('/api/my/timeline');
    if (!data.months || !data.months.length) {
      chart.dispose();
      box.innerHTML = `
        <div class="text-center py-4">
          <div style="font-size: 3rem; opacity: 0.3;">📅</div>
          <p class="small-note mt-3">
            暂无时间线数据<br/>
            新评分记录会显示在这里
          </p>
        </div>
      `;
      return;
    }

    chart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['评分次数', '平均评分'] },
      xAxis: { type: 'category', data: data.months },
      yAxis: [
        { type: 'value', name: '评分次数' },
        { type: 'value', name: '平均评分', min: 0, max: 5 },
      ],
      series: [
        { name: '评分次数', type: 'bar', yAxisIndex: 0, data: data.counts },
        { name: '平均评分', type: 'line', yAxisIndex: 1, data: data.avg_ratings, smooth: true },
      ],
    });
    const resizeHandler = () => chart.resize();
    window.addEventListener('resize', resizeHandler);
    box._chartInstance = chart;
    box._resizeHandler = resizeHandler;
  } catch (err) {
    chart.dispose();
    if (err.message.includes('🔒') || err.message.includes('登录') || err.message.includes('401')) {
      box.innerHTML = `
        <div class="text-center py-4">
          <div style="font-size: 3rem; opacity: 0.3;">🔒</div>
          <p class="small-note mt-3">
            登录后查看观影时间线<br/>
            记录你的评分历史
          </p>
          <a href="/login" class="btn btn-sm btn-outline-primary mt-2">去登录 →</a>
        </div>
      `;
    } else {
      box.innerHTML = '<div class="small-note text-danger">' + escapeHtml(err.message) + '</div>';
    }
  }
}

async function loadPopular() {
  const box = document.getElementById('popular');
  if (!box) return;
  box.innerHTML = '<div class="small-note">加载中...</div>';
  try {
    const items = await pageApi('/api/movies/popular?limit=20&min_count=10');
    box.innerHTML = items.map((m) => `
      <a class="list-group-item list-group-item-action" href="/movie/${m.id}">
        <div class="fw-semibold">${escapeHtml(formatMovieTitle(m.title))}</div>
        <div class="small-note">均分：${Number(m.avg_rating).toFixed(2)} | 评分人数：${m.rating_count} | ${escapeHtml(m.genres || '')}</div>
      </a>
    `).join('');
  } catch (err) {
    box.innerHTML = '<div class="small-note">加载失败：' + escapeHtml(err.message) + '</div>';
  }
}

async function onLoadHistory() {
  const box = document.getElementById('history');
  if (!box) return;
  box.innerHTML = '<div class="small-note">加载中...</div>';
  try {
    const items = await pageApi('/api/my/ratings?limit=50');
    if (!items.length) {
      box.innerHTML = '<div class="small-note">暂无评分记录（先去"搜索与评分"里打分）。</div>';
      return;
    }
    box.innerHTML = items.map((x) => `
      <div class="list-group-item list-group-item-action clickable">
        <div class="fw-semibold">${escapeHtml(formatMovieTitle(x.title))} <span class="small-note">(${x.year || '-'})</span></div>
        <div class="small-note">评分：${x.rating} | ID: <span class="mono">${x.movie_id}</span> | ${escapeHtml(x.genres || '')}</div>
      </div>
    `).join('');
    box.querySelectorAll('.list-group-item.clickable').forEach((el, index) => {
      el.onclick = () => {
        pickMovie({ id: items[index].movie_id, title: items[index].title });
        const tab = new bootstrap.Tab(document.getElementById('tab-search'));
        tab.show();
      };
    });
  } catch (err) {
    box.innerHTML = '<div class="small-note">加载失败：' + escapeHtml(err.message) + '</div>';
  }
}

async function initAuth() {
  try {
    const data = await pageApi('/api/me');
    if (data.authenticated) {
      setAuthUI(true, data.username, data.is_admin);
      await onLoadHistory();
    } else {
      setAuthUI(false, '');
    }
  } catch (_err) {
    setAuthUI(false, '');
  }
}

const profileTab = document.getElementById('tab-profile');
if (profileTab) {
  profileTab.addEventListener('shown.bs.tab', () => {
    renderPersona().catch(() => {});
    renderTimeline().catch(() => {});
  });
}

const hotTab = document.getElementById('tab-hot');
let popularLoaded = false;
if (hotTab) {
  hotTab.addEventListener('shown.bs.tab', () => {
    if (!popularLoaded) {
      loadPopular();
      popularLoaded = true;
    }
  });
}

const btnLogout = document.getElementById('btnLogout');
if (btnLogout) btnLogout.onclick = onLogout;
const btnSearch = document.getElementById('btnSearch');
if (btnSearch) btnSearch.onclick = onSearch;
const btnRate = document.getElementById('btnRate');
if (btnRate) btnRate.onclick = onRate;
const btnSimilar = document.getElementById('btnSimilar');
if (btnSimilar) btnSimilar.onclick = onSimilar;
const btnLoadHistory = document.getElementById('btnLoadHistory');
if (btnLoadHistory) btnLoadHistory.onclick = onLoadHistory;

setAuthUI(false, '');
initAuth();
loadPopular();
