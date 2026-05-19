/* =========================================
   CineMatch Dashboard — Unified Data + Lazy Charts
   ========================================= */

(function () {
  'use strict';

  // ── ECharts loader ────────────────────────────────

  function loadScript(src, timeoutMs) {
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src;
      s.async = true;
      const timer = setTimeout(() => { s.remove(); reject(new Error('timeout')); }, timeoutMs);
      s.onload = () => { clearTimeout(timer); resolve(); };
      s.onerror = () => { clearTimeout(timer); s.remove(); reject(new Error('failed')); };
      document.head.appendChild(s);
    });
  }

  async function ensureEcharts() {
    if (window.echarts) return;
    const cdns = [
      '/static/echarts/echarts.min.js',
      'https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js',
      'https://unpkg.com/echarts@5/dist/echarts.min.js',
      'https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js'
    ];
    for (const url of cdns) {
      try {
        await loadScript(url, 3000);
        if (window.echarts) return;
      } catch (e) { /* try next */ }
    }
    throw new Error('ECharts 加载失败，请检查网络连接');
  }

  // ── Chart manager ─────────────────────────────────

  const chartManager = {
    charts: [],
    add(chart) { this.charts.push(chart); return chart; },
    resizeAll() {
      this.charts.forEach(c => { if (c && !c.isDisposed()) c.resize(); });
    },
    disposeAll() {
      this.charts.forEach(c => { if (c && !c.isDisposed()) c.dispose(); });
      this.charts = [];
    }
  };

  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => chartManager.resizeAll(), 120);
  });
  window.addEventListener('beforeunload', () => chartManager.disposeAll());

  // ── Dark ECharts theme ────────────────────────────

  const darkTheme = {
    backgroundColor: 'transparent',
    textStyle: { color: '#94a3b8' },
    title: { textStyle: { color: '#f8fafc' } },
    legend: { textStyle: { color: '#94a3b8' } },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderColor: 'rgba(148, 163, 184, 0.2)',
      textStyle: { color: '#f8fafc' }
    },
    xAxis: {
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.3)' } },
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.08)' } }
    },
    yAxis: {
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.3)' } },
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.08)' } }
    }
  };

  // ── Helpers ───────────────────────────────────────

  function fmtNum(x, digits) {
    const n = Number(x);
    if (!Number.isFinite(n)) return '-';
    return n.toFixed(digits);
  }

  function setError(el, msg) {
    if (!el) return;
    el.innerHTML = `<div class="chart-error"><div class="chart-error-icon">⚠️</div><span>${msg}</span></div>`;
  }

  function setEmpty(el, msg, hint) {
    if (!el) return;
    el.innerHTML = `<div class="chart-error"><div class="chart-error-icon">📭</div><span>${msg}</span>${hint ? '<small style="opacity:0.6;margin-top:0.25rem;">' + hint + '</small>' : ''}</div>`;
  }

  // ── API ───────────────────────────────────────────

  async function fetchJson(url) {
    const res = await fetch(url, { credentials: 'include' });
    if (!res.ok) throw new Error(`请求失败 (${res.status})`);
    return res.json();
  }

  // ── Offline metrics renderer ──────────────────────

  function renderOfflineMetrics(data) {
    const box = document.getElementById('offlineMetrics');
    if (!box) return;

    if (!data) {
      box.innerHTML = `
        <div class="empty-state-card">
          <div class="empty-icon">📊</div>
          <div class="empty-title">暂无离线评估数据</div>
          <div class="empty-desc">运行评估脚本生成 ItemCF 离线指标</div>
          <code>python -m backend.scripts.evaluate_itemcf</code>
        </div>`;
      return;
    }

    const fmt = (v) => (typeof v === 'number' ? v.toFixed(4) : v);
    box.innerHTML = `
      <div class="metrics-grid">
        <div class="metric-item"><div class="metric-value">${fmt(data['precision@k'])}</div><div class="metric-label">Precision@K</div></div>
        <div class="metric-item"><div class="metric-value">${fmt(data['recall@k'])}</div><div class="metric-label">Recall@K</div></div>
        <div class="metric-item"><div class="metric-value">${fmt(data['map@k'])}</div><div class="metric-label">MAP@K</div></div>
        <div class="metric-item"><div class="metric-value">${fmt(data['ndcg@k'])}</div><div class="metric-label">NDCG@K</div></div>
        <div class="metric-item"><div class="metric-value">${fmt(data.coverage)}</div><div class="metric-label">Coverage</div></div>
        <div class="metric-item"><div class="metric-value">${fmt(data.avg_log_popularity)}</div><div class="metric-label">AvgLogPop</div></div>
        <div class="metric-item" style="grid-column:span 2;"><div class="metric-value">${data.users_evaluated || '-'}</div><div class="metric-label">Users Evaluated</div></div>
      </div>
      <div style="margin-top:1rem;padding-top:0.75rem;border-top:1px solid var(--cinema-border);font-size:0.8rem;color:var(--cinema-text-secondary);">
        配置：K=${data.k || '-'}，评分阈值=${data.like_threshold || '-'}，最少评分=${data.min_ratings || '-'}
      </div>`;
  }

  // ── Multi-model comparison renderer ───────────────

  function renderMultiModel(data) {
    const box = document.getElementById('multiModelMetrics');
    if (!box) return;

    if (!data || !data.results || data.results.length === 0) {
      box.innerHTML = `
        <div class="empty-state-card">
          <div class="empty-icon">🔄</div>
          <div class="empty-title">暂无多模型对比数据</div>
          <div class="empty-desc">运行评估脚本并启用消融实验</div>
          <code>python -m backend.scripts.evaluate_models --models all --ablation</code>
        </div>`;
      return;
    }

    const mainResults = data.results.filter(r => !r.recall_k && r.per_seed_limit === 50);
    const hybridAblation = data.results.filter(r => r.model === 'hybrid' && r.recall_k);
    const itemcfAblation = data.results.filter(r => r.model === 'itemcf' && r.per_seed_limit !== 50);

    let html = '<div style="overflow-x:auto;">';

    if (mainResults.length > 0) {
      html += '<div style="font-weight:600;margin-bottom:0.75rem;color:var(--cinema-text);">主模型对比</div>';
      html += '<table class="data-table"><thead><tr>';
      html += '<th>模型</th><th>P@K</th><th>R@K</th><th>MAP@K</th><th>NDCG@K</th><th>MRR@K</th><th>Coverage</th><th>用户数</th>';
      html += '</tr></thead><tbody>';
      for (const r of mainResults) {
        const bc = r.model === 'hybrid' ? 'badge-hybrid' : (r.model === 'ncf' ? 'badge-ncf' : 'badge-itemcf');
        const bt = r.model === 'hybrid' ? 'Hybrid' : (r.model === 'ncf' ? 'NCF' : 'ItemCF');
        html += `<tr><td><span class="model-badge ${bc}">${bt}</span></td>`;
        html += `<td>${r.precision_at_k?.toFixed(4) || '-'}</td>`;
        html += `<td>${r.recall_at_k?.toFixed(4) || '-'}</td>`;
        html += `<td>${r.map_at_k?.toFixed(4) || '-'}</td>`;
        html += `<td>${r.ndcg_at_k?.toFixed(4) || '-'}</td>`;
        html += `<td>${r.mrr_at_k?.toFixed(4) || '-'}</td>`;
        html += `<td>${r.coverage?.toFixed(4) || '-'}</td>`;
        html += `<td>${r.users_evaluated || 0}</td></tr>`;
      }
      html += '</tbody></table>';
    }

    if (hybridAblation.length > 0) {
      html += '<div style="font-weight:600;margin:1.5rem 0 0.75rem;color:var(--cinema-text);">消融实验：Hybrid 召回量影响</div>';
      html += '<table class="data-table"><thead><tr><th>Recall@K</th><th>P@K</th><th>R@K</th><th>NDCG@K</th><th>耗时(s)</th></tr></thead><tbody>';
      for (const r of hybridAblation) {
        html += `<tr><td>${r.recall_k}</td><td>${r.precision_at_k?.toFixed(4) || '-'}</td><td>${r.recall_at_k?.toFixed(4) || '-'}</td><td>${r.ndcg_at_k?.toFixed(4) || '-'}</td><td>${r.runtime_seconds?.toFixed(2) || '-'}</td></tr>`;
      }
      html += '</tbody></table>';
    }

    if (itemcfAblation.length > 0) {
      html += '<div style="font-weight:600;margin:1.5rem 0 0.75rem;color:var(--cinema-text);">消融实验：ItemCF 种子限制影响</div>';
      html += '<table class="data-table"><thead><tr><th>Seed Limit</th><th>P@K</th><th>R@K</th><th>NDCG@K</th><th>耗时(s)</th></tr></thead><tbody>';
      for (const r of itemcfAblation) {
        html += `<tr><td>${r.per_seed_limit}</td><td>${r.precision_at_k?.toFixed(4) || '-'}</td><td>${r.recall_at_k?.toFixed(4) || '-'}</td><td>${r.ndcg_at_k?.toFixed(4) || '-'}</td><td>${r.runtime_seconds?.toFixed(2) || '-'}</td></tr>`;
      }
      html += '</tbody></table>';
    }

    html += '</div>';
    html += `<div style="margin-top:1rem;color:var(--cinema-text-secondary);font-size:0.8rem;">生成时间：${data.timestamp || 'N/A'}</div>`;
    box.innerHTML = html;
  }

  // ── Chart renderers ───────────────────────────────

  function renderRatings(stats) {
    const el = document.getElementById('chartRatings');
    if (!el) return;
    if (!stats || !stats.labels || !stats.labels.length) { setEmpty(el, '暂无评分数据', '用户评分后将在此显示分布'); return; }
    const chart = chartManager.add(echarts.init(el));
    chart.setOption({
      ...darkTheme,
      tooltip: { ...darkTheme.tooltip, trigger: 'axis' },
      xAxis: { ...darkTheme.xAxis, type: 'category', data: stats.labels },
      yAxis: { ...darkTheme.yAxis, type: 'value' },
      series: [{ type: 'bar', data: stats.values, itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] } }]
    });
  }

  function renderGenres(stats) {
    const el = document.getElementById('chartGenres');
    if (!el) return;
    if (!stats || !stats.labels || !stats.labels.length) { setEmpty(el, '暂无类型数据', '导入电影数据后将在此显示'); return; }
    const chart = chartManager.add(echarts.init(el));
    const items = stats.labels.map((name, i) => ({ name, value: stats.values[i] }));
    const colors = ['#f59e0b', '#fbbf24', '#fcd34d', '#60a5fa', '#34d399', '#a78bfa', '#f87171', '#fb923c', '#e5a00d', '#818cf8'];
    chart.setOption({
      ...darkTheme,
      tooltip: { ...darkTheme.tooltip, trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        type: 'pie', radius: ['30%', '65%'], center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#0f172a', borderWidth: 2 },
        label: { color: '#94a3b8', fontSize: 10 },
        data: items.slice(0, 14).map((item, i) => ({ ...item, itemStyle: { color: colors[i % colors.length] } }))
      }]
    });
  }

  function renderYears(stats) {
    const el = document.getElementById('chartYears');
    if (!el) return;
    if (!stats || !stats.years || !stats.years.length) { setEmpty(el, '暂无年份数据', '导入电影数据后将在此显示'); return; }
    const chart = chartManager.add(echarts.init(el));
    chart.setOption({
      ...darkTheme,
      tooltip: { ...darkTheme.tooltip, trigger: 'axis' },
      legend: { ...darkTheme.legend, data: ['评分数量', '平均评分'] },
      grid: { left: 50, right: 50, bottom: 30, top: 40 },
      xAxis: { ...darkTheme.xAxis, type: 'category', data: stats.years },
      yAxis: [
        { ...darkTheme.yAxis, type: 'value', name: '评分数量', nameTextStyle: { color: '#94a3b8' } },
        { ...darkTheme.yAxis, type: 'value', name: '平均评分', min: 0, max: 5, nameTextStyle: { color: '#94a3b8' } }
      ],
      series: [
        { type: 'bar', yAxisIndex: 0, data: stats.counts, itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] } },
        { type: 'line', yAxisIndex: 1, data: stats.avg_ratings, smooth: true, itemStyle: { color: '#60a5fa' }, lineStyle: { width: 3 }, symbol: 'circle', symbolSize: 8 }
      ]
    });
  }

  function renderPopular(stats) {
    const el = document.getElementById('chartPopular');
    if (!el) return;
    if (!stats || !stats.labels || !stats.labels.length) { setEmpty(el, '暂无热门电影数据', '用户评分后将在此显示'); return; }
    const chart = chartManager.add(echarts.init(el));
    chart.setOption({
      ...darkTheme,
      tooltip: { ...darkTheme.tooltip, trigger: 'axis' },
      legend: { ...darkTheme.legend, data: ['评分人数', '平均评分'] },
      grid: { left: 50, right: 50, bottom: 80, top: 40 },
      xAxis: { ...darkTheme.xAxis, type: 'category', data: stats.labels, axisLabel: { ...darkTheme.xAxis.axisLabel, rotate: 30, fontSize: 10 } },
      yAxis: [
        { ...darkTheme.yAxis, type: 'value', name: '评分人数', nameTextStyle: { color: '#94a3b8' } },
        { ...darkTheme.yAxis, type: 'value', name: '平均评分', min: 0, max: 5, nameTextStyle: { color: '#94a3b8' } }
      ],
      series: [
        { name: '评分人数', type: 'bar', yAxisIndex: 0, data: stats.counts, itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] } },
        { name: '平均评分', type: 'line', yAxisIndex: 1, data: stats.avg_ratings, smooth: true, itemStyle: { color: '#60a5fa' }, lineStyle: { width: 3 } }
      ]
    });
  }

  function renderUsers(stats) {
    const el = document.getElementById('chartUsers');
    if (!el) return;
    if (!stats || !stats.labels || !stats.labels.length) { setEmpty(el, '暂无用户数据', '用户活动后将在此显示'); return; }
    const chart = chartManager.add(echarts.init(el));
    chart.setOption({
      ...darkTheme,
      tooltip: { ...darkTheme.tooltip, trigger: 'axis' },
      xAxis: { ...darkTheme.xAxis, type: 'category', data: stats.labels, axisLabel: { ...darkTheme.xAxis.axisLabel, rotate: 30, fontSize: 10 } },
      yAxis: { ...darkTheme.yAxis, type: 'value' },
      series: [{ type: 'bar', data: stats.values, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#f59e0b' }, { offset: 1, color: '#d97706' }]), borderRadius: [4, 4, 0, 0] } }]
    });
  }

  function renderMovieCounts(stats) {
    const el = document.getElementById('chartMovieCounts');
    if (!el) return;
    if (!stats || !stats.labels || !stats.labels.length) { setEmpty(el, '暂无数据', '导入数据后将在此显示'); return; }
    const chart = chartManager.add(echarts.init(el));
    chart.setOption({
      ...darkTheme,
      tooltip: { ...darkTheme.tooltip, trigger: 'axis' },
      xAxis: { ...darkTheme.xAxis, type: 'category', data: stats.labels, axisLabel: { ...darkTheme.xAxis.axisLabel, rotate: 30, fontSize: 10 } },
      yAxis: { ...darkTheme.yAxis, type: 'value' },
      series: [{ type: 'bar', data: stats.values, itemStyle: { color: '#34d399', borderRadius: [4, 4, 0, 0] } }]
    });
  }

  // ── Lazy chart observer ───────────────────────────

  const chartRenderers = {
    chartRatings: renderRatings,
    chartGenres: renderGenres,
    chartYears: renderYears,
    chartPopular: renderPopular,
    chartUsers: renderUsers,
    chartMovieCounts: renderMovieCounts,
  };

  let dashboardData = null;

  function initChartsWhenVisible() {
    if (!window.IntersectionObserver || !dashboardData) {
      // Fallback: render all immediately
      if (dashboardData) renderAllCharts();
      return;
    }

    const stats = dashboardData.stats || {};
    const rendered = new Set();

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const id = entry.target.id;
        if (rendered.has(id)) return;
        rendered.add(id);

        const renderer = chartRenderers[id];
        const statKey = {
          chartRatings: 'ratings', chartGenres: 'genres', chartYears: 'years',
          chartPopular: 'popular', chartUsers: 'user_activity', chartMovieCounts: 'movie_rating_counts'
        }[id];

        if (renderer && statKey) {
          renderer(stats[statKey]);
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '150px' });

    Object.keys(chartRenderers).forEach(id => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    // Fallback: render remaining after 5s
    setTimeout(() => {
      Object.keys(chartRenderers).forEach(id => {
        if (!rendered.has(id)) {
          const statKey = {
            chartRatings: 'ratings', chartGenres: 'genres', chartYears: 'years',
            chartPopular: 'popular', chartUsers: 'user_activity', chartMovieCounts: 'movie_rating_counts'
          }[id];
          if (chartRenderers[id] && statKey) chartRenderers[id](stats[statKey]);
        }
      });
    }, 5000);
  }

  function renderAllCharts() {
    const stats = dashboardData.stats || {};
    Object.entries(chartRenderers).forEach(([id, renderer]) => {
      const statKey = {
        chartRatings: 'ratings', chartGenres: 'genres', chartYears: 'years',
        chartPopular: 'popular', chartUsers: 'user_activity', chartMovieCounts: 'movie_rating_counts'
      }[id];
      if (statKey) renderer(stats[statKey]);
    });
  }

  // ── Fallback: load via individual API endpoints ────

  const STAT_URLS = {
    ratings: '/api/stats/ratings',
    genres: '/api/stats/genres',
    years: '/api/stats/years',
    popular: '/api/stats/popular?limit=12',
    user_activity: '/api/stats/user_activity?limit=12',
    movie_rating_counts: '/api/stats/movie_rating_counts',
  };

  async function loadFallback() {
    // Fire all individual API calls in parallel
    const results = await Promise.allSettled(
      Object.entries(STAT_URLS).map(([key, url]) =>
        fetchJson(url).then(data => ({ key, data })).catch(() => ({ key, data: null }))
      )
    );
    const stats = {};
    results.forEach(r => {
      if (r.status === 'fulfilled' && r.value) {
        stats[r.value.key] = r.value.data;
      }
    });

    // Also try evaluation metrics
    let offlineMetrics = null, multiModel = null;
    try { offlineMetrics = await fetchJson('/api/metrics/offline'); } catch (e) {}
    try { multiModel = await fetchJson('/api/metrics/evaluation'); } catch (e) {}

    return { offline_metrics: offlineMetrics, multi_model: multiModel, stats: stats };
  }

  // ── Main load ─────────────────────────────────────

  let loading = false;

  async function loadAll() {
    if (loading) return;
    loading = true;

    const btn = document.getElementById('btnRefresh');
    if (btn) btn.classList.add('spinning');

    try {
      // Try unified endpoint first, fall back to individual calls
      try {
        dashboardData = await fetchJson('/api/dashboard/overview');
      } catch (e) {
        console.warn('Unified API unavailable, falling back to individual endpoints');
        dashboardData = await loadFallback();
      }

      // Render non-chart sections immediately
      renderOfflineMetrics(dashboardData.offline_metrics);
      renderMultiModel(dashboardData.multi_model);

      // Lazy-render charts
      await ensureEcharts();
      initChartsWhenVisible();
    } catch (e) {
      console.error('Dashboard load failed:', e);
      Object.keys(chartRenderers).forEach(id => {
        setError(document.getElementById(id), '数据加载失败，请刷新重试');
      });
      setError(document.getElementById('offlineMetrics'), '数据加载失败');
      setError(document.getElementById('multiModelMetrics'), '数据加载失败');
    } finally {
      loading = false;
      if (btn) btn.classList.remove('spinning');
    }
  }

  // ── Init ──────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    loadAll();

    const btn = document.getElementById('btnRefresh');
    if (btn) {
      btn.addEventListener('click', () => {
        chartManager.disposeAll();
        loadAll();
      });
    }
  });
})();
