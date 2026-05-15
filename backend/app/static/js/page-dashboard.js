document.addEventListener('DOMContentLoaded', () => {
  function showError(message) {
    console.error(message);
  }

  function loadScript(src, timeoutMs) {
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src;
      s.async = true;
      const timer = setTimeout(() => {
        s.remove();
        reject(new Error('timeout loading ' + src));
      }, timeoutMs);

      s.onload = () => {
        clearTimeout(timer);
        resolve();
      };
      s.onerror = () => {
        clearTimeout(timer);
        s.remove();
        reject(new Error('failed to load ' + src));
      };
      document.head.appendChild(s);
    });
  }

  async function ensureEcharts() {
    if (window.echarts) return;
    const timeoutMs = 2500;
    const cdns = [
      '/static/echarts/echarts.min.js',
      'https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js',
      'https://unpkg.com/echarts@5/dist/echarts.min.js',
      'https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js'
    ];
    let lastErr = null;
    for (const url of cdns) {
      try {
        await loadScript(url, timeoutMs);
        if (window.echarts) return;
      } catch (e) {
        lastErr = e;
      }
    }
    throw lastErr || new Error('echarts load failed');
  }

  const chartManager = {
    charts: [],
    add(chart) {
      this.charts.push(chart);
      return chart;
    },
    resizeAll() {
      this.charts.forEach(chart => {
        if (chart && !chart.isDisposed()) {
          chart.resize();
        }
      });
    },
    disposeAll() {
      this.charts.forEach(chart => {
        if (chart && !chart.isDisposed()) {
          chart.dispose();
        }
      });
      this.charts = [];
    }
  };

  let resizeTimeout;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      chartManager.resizeAll();
    }, 100);
  });

  async function fetchJson(url, retryCount = 1) {
    const friendlyErrors = {
      401: '🔒 请先登录',
      404: '❓ 数据不存在',
      503: '🔧 服务暂时不可用',
    };

    for (let i = 0; i <= retryCount; i++) {
      try {
        const res = await fetch(url, { credentials: 'include' });
        if (!res.ok) {
          const msg = friendlyErrors[res.status] || `请求失败 (${res.status})`;
          throw new Error(msg);
        }
        return await res.json();
      } catch (err) {
        if (i === retryCount) throw err;
        await new Promise(r => setTimeout(r, 500 * (i + 1)));
      }
    }
  }

  function fmtNum(x, digits) {
    const n = Number(x);
    if (!Number.isFinite(n)) return '-';
    return n.toFixed(digits);
  }

  async function renderOfflineMetrics() {
    const box = document.getElementById('offlineMetrics');
    if (!box) return;
    try {
      const m = await fetchJson('/api/metrics/offline');
      const fmt = (v) => (typeof v === 'number' ? v.toFixed(4) : v);
      box.innerHTML = `
        <div class="metrics-grid">
          <div class="metric-item">
            <div class="metric-value">${fmt(m['precision@k'])}</div>
            <div class="metric-label">Precision@K</div>
          </div>
          <div class="metric-item">
            <div class="metric-value">${fmt(m['recall@k'])}</div>
            <div class="metric-label">Recall@K</div>
          </div>
          <div class="metric-item">
            <div class="metric-value">${fmt(m['map@k'])}</div>
            <div class="metric-label">MAP@K</div>
          </div>
          <div class="metric-item">
            <div class="metric-value">${fmt(m['ndcg@k'])}</div>
            <div class="metric-label">NDCG@K</div>
          </div>
          <div class="metric-item">
            <div class="metric-value">${fmt(m.coverage)}</div>
            <div class="metric-label">Coverage</div>
          </div>
          <div class="metric-item">
            <div class="metric-value">${fmt(m.avg_log_popularity)}</div>
            <div class="metric-label">AvgLogPop</div>
          </div>
          <div class="metric-item" style="grid-column: span 2;">
            <div class="metric-value">${m.users_evaluated}</div>
            <div class="metric-label">Users Evaluated</div>
          </div>
        </div>
        <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid var(--border-color);">
          <span style="color:var(--text-secondary); font-size:0.8rem;">
            配置参数：K=${m.k}, 评分阈值=${m.like_threshold}, 最少评分=${m.min_ratings}
          </span>
        </div>
      `;
    } catch (e) {
      box.innerHTML = `
        <div class="empty-state">
          <div style="font-size:2rem; opacity:0.5;">📊</div>
          <p style="margin-top:0.5rem;">暂无离线评估数据</p>
          <p style="font-size:0.8rem; opacity:0.7;">运行 <code style="background:rgba(245,158,11,0.1); padding:0.2rem 0.4rem; border-radius:4px;">python -m backend.scripts.evaluate_itemcf</code> 生成评估结果</p>
        </div>
      `;
    }
  }

  async function renderMultiModelMetrics() {
    const box = document.getElementById('multiModelMetrics');
    if (!box) return;
    try {
      const data = await fetchJson('/api/metrics/evaluation');
      if (!data.results || data.results.length === 0) {
        box.innerHTML = `
          <div class="empty-state">
            <div style="font-size:2rem; opacity:0.5;">🔄</div>
            <p style="margin-top:0.5rem;">暂无多模型评估数据</p>
          </div>
        `;
        return;
      }

      const mainResults = data.results.filter(r => !r.recall_k && r.per_seed_limit === 50);
      const hybridAblation = data.results.filter(r => r.model === 'hybrid' && r.recall_k);
      const itemcfAblation = data.results.filter(r => r.model === 'itemcf' && r.per_seed_limit !== 50);

      let html = '<div style="overflow-x:auto;">';

      if (mainResults.length > 0) {
        html += '<div style="font-weight:600; margin-bottom:0.75rem; color:var(--text-primary);">主模型对比</div>';
        html += '<table class="data-table">';
        html += '<thead><tr>';
        html += '<th>模型</th><th>P@K</th><th>R@K</th><th>MAP@K</th><th>NDCG@K</th><th>MRR@K</th><th>Coverage</th><th>用户数</th>';
        html += '</tr></thead><tbody>';
        for (const r of mainResults) {
          const badgeClass = r.model === 'hybrid' ? 'badge-hybrid' : (r.model === 'ncf' ? 'badge-ncf' : 'badge-itemcf');
          const badgeText = r.model === 'hybrid' ? 'Hybrid' : (r.model === 'ncf' ? 'NCF' : 'ItemCF');
          html += '<tr>';
          html += `<td><span class="model-badge ${badgeClass}">${badgeText}</span></td>`;
          html += `<td>${r.precision_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.recall_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.map_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.ndcg_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.mrr_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.coverage?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.users_evaluated || 0}</td>`;
          html += '</tr>';
        }
        html += '</tbody></table>';
      }

      if (hybridAblation.length > 0) {
        html += '<div style="font-weight:600; margin:1.5rem 0 0.75rem; color:var(--text-primary);">消融实验：Hybrid 不同召回数量</div>';
        html += '<table class="data-table">';
        html += '<thead><tr>';
        html += '<th>Recall@K</th><th>P@K</th><th>R@K</th><th>NDCG@K</th><th>耗时(s)</th>';
        html += '</tr></thead><tbody>';
        for (const r of hybridAblation) {
          html += '<tr>';
          html += `<td>${r.recall_k}</td>`;
          html += `<td>${r.precision_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.recall_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.ndcg_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.runtime_seconds?.toFixed(2) || '-'}</td>`;
          html += '</tr>';
        }
        html += '</tbody></table>';
      }

      if (itemcfAblation.length > 0) {
        html += '<div style="font-weight:600; margin:1.5rem 0 0.75rem; color:var(--text-primary);">消融实验：ItemCF 不同种子限制</div>';
        html += '<table class="data-table">';
        html += '<thead><tr>';
        html += '<th>Seed Limit</th><th>P@K</th><th>R@K</th><th>NDCG@K</th><th>耗时(s)</th>';
        html += '</tr></thead><tbody>';
        for (const r of itemcfAblation) {
          html += '<tr>';
          html += `<td>${r.per_seed_limit}</td>`;
          html += `<td>${r.precision_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.recall_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.ndcg_at_k?.toFixed(4) || '-'}</td>`;
          html += `<td>${r.runtime_seconds?.toFixed(2) || '-'}</td>`;
          html += '</tr>';
        }
        html += '</tbody></table>';
      }

      html += '</div>';
      html += `<div style="margin-top:1rem; color:var(--text-secondary); font-size:0.8rem;">生成时间：${data.timestamp || 'N/A'}</div>`;
      box.innerHTML = html;
    } catch (e) {
      box.innerHTML = `
        <div class="empty-state">
          <div style="font-size:2rem; opacity:0.5;">🔄</div>
          <p style="margin-top:0.5rem;">暂无多模型评估数据</p>
          <p style="font-size:0.8rem; opacity:0.7;">运行 <code style="background:rgba(245,158,11,0.1); padding:0.2rem 0.4rem; border-radius:4px;">python -m backend.scripts.evaluate_models --models all --ablation</code> 生成结果</p>
        </div>
      `;
    }
  }

  const darkTheme = {
    backgroundColor: 'transparent',
    textStyle: { color: '#94a3b8' },
    title: { textStyle: { color: '#f8fafc' } },
    legend: { textStyle: { color: '#94a3b8' } },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: 'rgba(148, 163, 184, 0.2)',
      textStyle: { color: '#f8fafc' }
    },
    xAxis: {
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.3)' } },
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.1)' } }
    },
    yAxis: {
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.3)' } },
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.1)' } }
    }
  };

  async function renderRatings() {
    try {
      const data = await fetchJson('/api/stats/ratings');
      const chart = chartManager.add(echarts.init(document.getElementById('chartRatings')));
      chart.setOption({
        ...darkTheme,
        tooltip: { ...darkTheme.tooltip, trigger: 'axis' },
        xAxis: { ...darkTheme.xAxis, type: 'category', data: data.labels },
        yAxis: { ...darkTheme.yAxis, type: 'value' },
        series: [{ type: 'bar', data: data.values, itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] } }]
      });
    } catch (e) {
      const target = document.getElementById('chartRatings');
      if (target) target.innerHTML = '<div style="text-align:center;padding:2rem;color:#94a3b8;">' + e.message + '</div>';
    }
  }

  async function renderPopular() {
    try {
      const data = await fetchJson('/api/stats/popular?limit=12');
      const chart = chartManager.add(echarts.init(document.getElementById('chartPopular')));
      chart.setOption({
        ...darkTheme,
        tooltip: { ...darkTheme.tooltip, trigger: 'axis' },
        legend: { ...darkTheme.legend, data: ['评分人数', '平均评分'] },
        grid: { left: 50, right: 50, bottom: 80, top: 40 },
        xAxis: { ...darkTheme.xAxis, type: 'category', data: data.labels, axisLabel: { ...darkTheme.xAxis.axisLabel, rotate: 35, fontSize: 10 } },
        yAxis: [
          { ...darkTheme.yAxis, type: 'value', name: '评分人数', nameTextStyle: { color: '#94a3b8' } },
          { ...darkTheme.yAxis, type: 'value', name: '平均评分', min: 0, max: 5, nameTextStyle: { color: '#94a3b8' } }
        ],
        series: [
          { name: '评分人数', type: 'bar', yAxisIndex: 0, data: data.counts, itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] } },
          { name: '平均评分', type: 'line', yAxisIndex: 1, data: data.avg_ratings, smooth: true, itemStyle: { color: '#60a5fa' }, lineStyle: { width: 3 } }
        ]
      });
    } catch (e) {
      const target = document.getElementById('chartPopular');
      if (target) target.innerHTML = '<div style="text-align:center;padding:2rem;color:#94a3b8;">' + e.message + '</div>';
    }
  }

  async function renderUsers() {
    try {
      const data = await fetchJson('/api/stats/user_activity?limit=12');
      const chart = chartManager.add(echarts.init(document.getElementById('chartUsers')));
      chart.setOption({
        ...darkTheme,
        tooltip: { ...darkTheme.tooltip, trigger: 'axis' },
        xAxis: { ...darkTheme.xAxis, type: 'category', data: data.labels, axisLabel: { ...darkTheme.xAxis.axisLabel, rotate: 35, fontSize: 10 } },
        yAxis: { ...darkTheme.yAxis, type: 'value' },
        series: [{ type: 'bar', data: data.values, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [ { offset: 0, color: '#f59e0b' }, { offset: 1, color: '#d97706' } ]), borderRadius: [4, 4, 0, 0] } }]
      });
    } catch (e) {
      const target = document.getElementById('chartUsers');
      if (target) target.innerHTML = '<div style="text-align:center;padding:2rem;color:#94a3b8;">' + e.message + '</div>';
    }
  }

  async function renderMovieCounts() {
    try {
      const data = await fetchJson('/api/stats/movie_rating_counts');
      const chart = chartManager.add(echarts.init(document.getElementById('chartMovieCounts')));
      chart.setOption({
        ...darkTheme,
        tooltip: { ...darkTheme.tooltip, trigger: 'axis' },
        xAxis: { ...darkTheme.xAxis, type: 'category', data: data.labels, axisLabel: { ...darkTheme.xAxis.axisLabel, rotate: 35, fontSize: 10 } },
        yAxis: { ...darkTheme.yAxis, type: 'value' },
        series: [{ type: 'bar', data: data.values, itemStyle: { color: '#34d399', borderRadius: [4, 4, 0, 0] } }]
      });
    } catch (e) {
      const target = document.getElementById('chartMovieCounts');
      if (target) target.innerHTML = '<div style="text-align:center;padding:2rem;color:#94a3b8;">' + e.message + '</div>';
    }
  }

  async function renderGenres() {
    try {
      const data = await fetchJson('/api/stats/genres');
      const chart = chartManager.add(echarts.init(document.getElementById('chartGenres')));
      const items = data.labels.map((name, i) => ({ name, value: data.values[i] }));
      const colors = ['#f59e0b', '#fbbf24', '#fcd34d', '#60a5fa', '#34d399', '#a78bfa', '#f87171', '#fb923c'];
      chart.setOption({
        ...darkTheme,
        tooltip: { ...darkTheme.tooltip, trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        series: [{
          type: 'pie',
          radius: ['30%', '65%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 6, borderColor: '#0f172a', borderWidth: 2 },
          label: { color: '#94a3b8', fontSize: 11 },
          data: items.slice(0, 12).map((item, i) => ({ ...item, itemStyle: { color: colors[i % colors.length] } }))
        }]
      });
    } catch (e) {
      const target = document.getElementById('chartGenres');
      if (target) target.innerHTML = '<div style="text-align:center;padding:2rem;color:#94a3b8;">' + e.message + '</div>';
    }
  }

  async function renderYears() {
    try {
      const data = await fetchJson('/api/stats/years');
      const chart = chartManager.add(echarts.init(document.getElementById('chartYears')));
      chart.setOption({
        ...darkTheme,
        tooltip: { ...darkTheme.tooltip, trigger: 'axis' },
        legend: { ...darkTheme.legend, data: ['评分数量', '平均评分'] },
        xAxis: { ...darkTheme.xAxis, type: 'category', data: data.years },
        yAxis: [
          { ...darkTheme.yAxis, type: 'value', name: '评分数量', nameTextStyle: { color: '#94a3b8' } },
          { ...darkTheme.yAxis, type: 'value', name: '平均评分', min: 0, max: 5, nameTextStyle: { color: '#94a3b8' } }
        ],
        series: [
          { type: 'bar', yAxisIndex: 0, data: data.counts, itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] } },
          { type: 'line', yAxisIndex: 1, data: data.avg_ratings, smooth: true, itemStyle: { color: '#60a5fa' }, lineStyle: { width: 3 }, symbol: 'circle', symbolSize: 8 }
        ]
      });
    } catch (e) {
      const target = document.getElementById('chartYears');
      if (target) target.innerHTML = '<div style="text-align:center;padding:2rem;color:#94a3b8;">' + e.message + '</div>';
    }
  }

  window.addEventListener('beforeunload', () => {
    chartManager.disposeAll();
  });

  ensureEcharts()
    .then(() => Promise.allSettled([
      renderOfflineMetrics(),
      renderMultiModelMetrics(),
      renderRatings(),
      renderGenres(),
      renderYears(),
      renderPopular(),
      renderUsers(),
      renderMovieCounts()
    ]))
    .then((results) => {
      const failures = results.filter(r => r.status === 'rejected');
      if (failures.length > 0) {
        console.error('部分图表加载失败:', failures);
      }
    })
    .catch((e) => {
      console.error(e);
    });
});