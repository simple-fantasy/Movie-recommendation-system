/* =========================================
   CineMatch Enhanced Dashboard — ECharts + Dark Theme + Lazy Loading
   ========================================= */

(function () {
  'use strict';

  // ── ECharts dynamic loader ────────────────────────

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

  let _echartsReady = false;
  async function ensureEcharts() {
    if (window.echarts) { _echartsReady = true; console.log('[EnhancedDashboard] ECharts already loaded'); return; }
    if (_echartsReady) return;
    console.log('[EnhancedDashboard] Loading ECharts...');
    const cdns = [
      '/static/echarts/echarts.min.js',
      'https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js',
      'https://unpkg.com/echarts@5/dist/echarts.min.js',
      'https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js'
    ];
    for (const url of cdns) {
      try {
        console.log('[EnhancedDashboard] Trying ECharts CDN:', url);
        await loadScript(url, 4000);
        if (window.echarts) { _echartsReady = true; console.log('[EnhancedDashboard] ECharts loaded from:', url); return; }
      } catch (e) { console.warn('[EnhancedDashboard] CDN failed:', url, e.message); }
    }
    console.error('[EnhancedDashboard] All ECharts CDNs failed');
    throw new Error('ECharts 加载失败，请检查网络连接');
  }

  // ── Chart manager ─────────────────────────────────

  const charts = {};

  function disposeAll() {
    Object.values(charts).forEach(function(c) { if (c && !c.isDisposed()) c.dispose(); });
    for (var k in charts) delete charts[k];
  }

  window.addEventListener('resize', function() {
    Object.values(charts).forEach(function(c) { if (c && !c.isDisposed()) c.resize(); });
  });
  window.addEventListener('beforeunload', disposeAll);

  // ── Dark ECharts theme ────────────────────────────

  var darkTheme = {
    backgroundColor: 'transparent',
    textStyle: { color: '#94a3b8' },
    title: { textStyle: { color: '#f8fafc' } },
    legend: { textStyle: { color: '#94a3b8' } },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderColor: 'rgba(148, 163, 184, 0.2)',
      textStyle: { color: '#f8fafc' }
    }
  };

  // ── Helpers ───────────────────────────────────────

  function getSegmentName(key) {
    var names = {
      highly_active: '高活跃用户', moderately_active: '中活跃用户',
      low_active: '低活跃用户', dormant: '休眠用户',
      generous_raters: '宽松评分者', critical_raters: '严格评分者',
      balanced_raters: '平衡评分者'
    };
    return names[key] || key;
  }

  function setSkelError(el, msg) {
    if (!el) return;
    el.innerHTML = '<div class="d-flex flex-column align-items-center justify-content-center h-100 text-muted" style="min-height:200px;"><span style="font-size:2rem;opacity:0.4;margin-bottom:0.5rem;">⚠️</span><span>' + msg + '</span></div>';
  }

  // ── API fetch ─────────────────────────────────────

  function fetchJSON(url, timeoutMs) {
    console.log('[EnhancedDashboard] Fetching:', url);
    var timeout = timeoutMs || 8000;
    var controller = new AbortController();
    var timer = setTimeout(function() {
      controller.abort();
      console.error('[EnhancedDashboard] TIMEOUT:', url, 'after', timeout + 'ms');
    }, timeout);
    return fetch(url, { credentials: 'include', signal: controller.signal }).then(function(r) {
      clearTimeout(timer);
      console.log('[EnhancedDashboard] Response:', url, r.status);
      if (!r.ok) {
        return r.text().then(function(body) {
          console.error('[EnhancedDashboard] Error body:', body.substring(0, 300));
          throw new Error('HTTP ' + r.status + ' from ' + url);
        });
      }
      return r.json().then(function(data) {
        console.log('[EnhancedDashboard] Data OK:', url, Object.keys(data || {}));
        return data;
      });
    }).catch(function(e) {
      clearTimeout(timer);
      if (e.name === 'AbortError') {
        console.error('[EnhancedDashboard] Fetch ABORTED (timeout):', url);
        throw new Error('timeout: ' + url);
      }
      console.error('[EnhancedDashboard] Fetch failed:', url, e.message);
      throw e;
    });
  }

  // ── Render stat cards ─────────────────────────────

  function renderStats(data) {
    if (!data) return;
    document.getElementById('total-users').textContent = (data.total_users || 0).toLocaleString();
    document.getElementById('total-movies').textContent = (data.total_movies || 0).toLocaleString();
    document.getElementById('total-ratings').textContent = (data.total_ratings || 0).toLocaleString();
    document.getElementById('active-users-today').textContent = (data.active_users_today || 0).toLocaleString();
    document.getElementById('users-this-week').textContent = (data.users_this_week || 0).toLocaleString();
    document.getElementById('ratings-today').textContent = (data.ratings_today || 0).toLocaleString();
    updateTopMovies(data.top_movies_this_month || []);
  }

  function updateTopMovies(movies) {
    var container = document.getElementById('top-movies-list');
    if (!container) return;
    if (!movies || !movies.length) {
      container.innerHTML = '<div class="col-12 text-center py-4 text-muted">本月暂无评分数据</div>';
      return;
    }
    container.innerHTML = movies.map(function(movie, i) {
      return '<div class="col-md-6 col-lg-4 mb-3">' +
        '<div class="card h-100" style="background:var(--cinema-surface);border:1px solid var(--cinema-border);">' +
        '<div class="card-body">' +
        '<div class="d-flex align-items-center">' +
        '<div class="me-3"><div class="badge rounded-circle p-2" style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;background:var(--cinema-accent);color:#0a0a0a;"><strong>' + (i + 1) + '</strong></div></div>' +
        '<div class="flex-grow-1"><h6 class="card-title mb-1" style="color:var(--cinema-text);">' + escapeHtml(movie.title) + '</h6>' +
        '<p class="card-text mb-1"><small class="text-muted">(' + (movie.year || '未知') + ')</small></p>' +
        '<span class="badge" style="background:rgba(229,160,13,.15);color:var(--cinema-accent);"><i class="ph ph-star"></i> ' + movie.rating_count + ' 本月评分</span></div>' +
        '</div></div></div></div>';
    }).join('');
  }

  // ── Chart: user segments ──────────────────────────

  function renderUserSegments(segData, rateData) {
    var el1 = document.getElementById('user-segments-pie');
    var el2 = document.getElementById('rating-preferences-pie');
    if (!el1 && !el2) return;

    var segColors = { highly_active: '#22c55e', moderately_active: '#60a5fa', low_active: '#f59e0b', dormant: '#94a3b8' };
    var rateColors = { generous_raters: '#22c55e', critical_raters: '#ef4444', balanced_raters: '#60a5fa' };

    if (el1 && segData && !segData.error) {
      var c1 = echarts.init(el1);
      c1.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'item', formatter: '{b}: {c}% ({d}%)', backgroundColor: 'rgba(15,23,42,0.92)', borderColor: 'rgba(148,163,184,0.2)', textStyle: { color: '#f8fafc' } },
        series: [{
          type: 'pie', radius: ['40%', '70%'], center: ['50%', '55%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 8, borderColor: '#1f1f1f', borderWidth: 2 },
          label: { show: false },
          emphasis: { label: { show: true, fontWeight: 'bold' } },
          data: Object.entries(segData).map(function(e) {
            return { name: getSegmentName(e[0]), value: e[1], itemStyle: { color: segColors[e[0]] || '#94a3b8' } };
          })
        }]
      });
      charts['user-segments-pie'] = c1;
    } else if (el1) {
      setSkelError(el1, '暂无分群数据');
    }

    if (el2 && rateData && !rateData.error) {
      var c2 = echarts.init(el2);
      c2.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'item', formatter: '{b}: {c}% ({d}%)', backgroundColor: 'rgba(15,23,42,0.92)', borderColor: 'rgba(148,163,184,0.2)', textStyle: { color: '#f8fafc' } },
        series: [{
          type: 'pie', radius: ['40%', '70%'], center: ['50%', '55%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 8, borderColor: '#1f1f1f', borderWidth: 2 },
          label: { show: false },
          emphasis: { label: { show: true, fontWeight: 'bold' } },
          data: Object.entries(rateData).map(function(e) {
            return { name: getSegmentName(e[0]), value: e[1], itemStyle: { color: rateColors[e[0]] || '#94a3b8' } };
          })
        }]
      });
      charts['rating-preferences-pie'] = c2;
    } else if (el2) {
      setSkelError(el2, '暂无偏好数据');
    }
  }

  // ── Chart: activity heatmap ───────────────────────

  function renderActivityHeatmap(hmData) {
    var el = document.getElementById('activity-heatmap');
    if (!el) return;
    if (!hmData || !hmData.length) { setSkelError(el, '暂无活跃度数据'); return; }

    var hours = []; for (var i = 0; i < 24; i++) hours.push(i + '时');
    var days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    var maxVal = Math.max.apply(null, hmData.map(function(d) { return d[2]; })) || 0;

    var c = echarts.init(el);
    c.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        backgroundColor: 'rgba(15,23,42,0.92)', borderColor: 'rgba(148,163,184,0.2)',
        textStyle: { color: '#f8fafc' }, position: 'top',
        formatter: function(p) { return days[p.value[1]] + ' ' + hours[p.value[0]] + '<br/>活跃度: ' + p.value[2]; }
      },
      grid: { height: '50%', top: '10%', left: '10%' },
      xAxis: { type: 'category', data: hours, splitArea: { show: true } },
      yAxis: { type: 'category', data: days, splitArea: { show: true } },
      visualMap: {
        min: 0, max: maxVal || 1,
        calculable: true, orient: 'horizontal', left: 'center', bottom: '5%',
        inRange: { color: ['#1a1a2e', '#16213e', '#0f3460', '#533483', '#e5a00d'] }
      },
      series: [{
        type: 'heatmap', data: hmData, label: { show: false },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } }
      }]
    });
    charts['activity-heatmap'] = c;
  }

  // ── Chart: popular genres bar ─────────────────────

  function renderPopularGenres(genres) {
    var el = document.getElementById('popular-genres-bar');
    if (!el) return;
    if (!genres || !genres.length) { setSkelError(el, '暂无类型数据'); return; }

    var c = echarts.init(el);
    c.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: 'rgba(15,23,42,0.92)', borderColor: 'rgba(148,163,184,0.2)', textStyle: { color: '#f8fafc' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value', boundaryGap: [0, 0.01] },
      yAxis: { type: 'category', data: genres.map(function(d) { return d.genre; }).reverse(), axisLabel: { color: '#94a3b8' } },
      series: [{
        type: 'bar',
        data: genres.map(function(d) { return d.count; }).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#f59e0b' }, { offset: 1, color: '#e5a00d' }
          ]),
          borderRadius: [0, 4, 4, 0]
        }
      }]
    });
    charts['popular-genres-bar'] = c;
  }

  // ── System health ─────────────────────────────────

  function renderSystemHealth(health) {
    var container = document.getElementById('system-health');
    if (!container) return;
    if (!health || health.error) {
      container.innerHTML = '<div class="col-12 text-center py-4 text-muted">系统健康数据暂不可用</div>';
      return;
    }

    var dbOk = health.database_status === 'healthy';
    var integrity = health.data_integrity || {};
    var load = health.system_load || {};
    var cache = health.cache_efficiency || {};

    container.innerHTML =
      '<div class="col-md-3 mb-3"><div class="text-center">' +
      '<div class="h4 mb-2"><i class="ph ph-database" style="color:' + (dbOk ? '#22c55e' : '#ef4444') + ';font-size:1.75rem;"></i></div>' +
      '<h6 style="color:var(--cinema-text);">数据库状态</h6>' +
      '<span class="badge" style="background:' + (dbOk ? 'rgba(34,197,94,.15)' : 'rgba(239,68,68,.15)') + ';color:' + (dbOk ? '#22c55e' : '#ef4444') + ';">' + (dbOk ? '正常' : '异常') + '</span>' +
      '<div><small class="text-muted">' + (health.database_response_time || 'N/A') + '</small></div>' +
      '</div></div>' +
      '<div class="col-md-3 mb-3"><div class="text-center">' +
      '<div class="h4 mb-2"><i class="ph ph-activity" style="color:#60a5fa;font-size:1.75rem;"></i></div>' +
      '<h6 style="color:var(--cinema-text);">系统负载</h6>' +
      '<small class="text-muted">最近1h: ' + (load.ratings_last_hour || 0) + ' 评分</small><br>' +
      '<small class="text-muted">活跃用户: ' + (load.active_users_last_hour || 0) + '</small>' +
      '</div></div>' +
      '<div class="col-md-3 mb-3"><div class="text-center">' +
      '<div class="h4 mb-2"><i class="ph ph-shield-check" style="color:#22c55e;font-size:1.75rem;"></i></div>' +
      '<h6 style="color:var(--cinema-text);">数据完整性</h6>' +
      '<small class="text-muted">无评分电影: ' + (integrity.movies_without_ratings || 0) + '</small><br>' +
      '<small class="text-muted">孤立评分: ' + (integrity.orphan_ratings || 0) + '</small>' +
      '</div></div>' +
      '<div class="col-md-3 mb-3"><div class="text-center">' +
      '<div class="h4 mb-2"><i class="ph ph-clock" style="color:#f59e0b;font-size:1.75rem;"></i></div>' +
      '<h6 style="color:var(--cinema-text);">缓存状态</h6>' +
      '<small class="text-muted">' + (cache.cache_type || 'SimpleCache') + '</small><br>' +
      '<small class="text-muted">' + (health.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'N/A') + '</small>' +
      '</div></div>';
  }

  // ── Lazy IntersectionObserver ─────────────────────

  var _pendingCharts = {};
  var _chartObserved = {};

  function registerLazyChart(id, fn) {
    _pendingCharts[id] = fn;
  }

  function startLazyObserver() {
    if (!window.IntersectionObserver) {
      // No observer support: render all immediately
      Object.values(_pendingCharts).forEach(function(fn) { fn(); });
      _pendingCharts = {};
      return;
    }

    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (!entry.isIntersecting) return;
        var id = entry.target.id;
        if (_chartObserved[id]) return;
        _chartObserved[id] = true;

        if (_pendingCharts[id]) {
          _pendingCharts[id]();
          delete _pendingCharts[id];
        }
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '200px' });

    Object.keys(_pendingCharts).forEach(function(id) {
      var el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    // Fallback: render remaining after 6s
    setTimeout(function() {
      Object.values(_pendingCharts).forEach(function(fn) { fn(); });
      _pendingCharts = {};
    }, 6000);
  }

  // ── Main load ─────────────────────────────────────

  var _loading = false;

  function loadAll() {
    if (_loading) return;
    _loading = true;

    var btn = document.getElementById('refresh-dashboard-btn');
    var origText = btn ? btn.innerHTML : '';
    if (btn) {
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>加载中...';
      btn.disabled = true;
    }

    disposeAll();
    _pendingCharts = {};
    _chartObserved = {};

    // Step 1: Load ECharts (critical - this was the original bug!)
    ensureEcharts().then(function() {
      console.log('[EnhancedDashboard] ECharts ready');

      // Step 2: Fetch overview + user-segments + system-health in PARALLEL
      return Promise.allSettled([
        fetchJSON('/api/enhanced-stats/overview'),
        fetchJSON('/api/enhanced-stats/user-segments'),
        fetchJSON('/api/enhanced-stats/activity-heatmap'),
        fetchJSON('/api/enhanced-stats/system-health'),
      ]);
    }).then(function(results) {
      console.log('[EnhancedDashboard] All API calls completed. Results:',
        results.map(function(r, i) {
          var names = ['overview','segments','heatmap','health'];
          return names[i] + ': ' + r.status + (r.status === 'rejected' ? ' (' + r.reason.message + ')' : '');
        })
      );

      var overview = results[0].status === 'fulfilled' ? results[0].value : null;
      var segments = results[1].status === 'fulfilled' ? results[1].value : null;
      var heatmap = results[2].status === 'fulfilled' ? results[2].value : null;
      var health = results[3].status === 'fulfilled' ? results[3].value : null;

      console.log('[EnhancedDashboard] Parsed data:', {
        overview: overview ? 'yes (keys: ' + Object.keys(overview).join(',') + ')' : 'NULL',
        segments: segments ? 'yes (keys: ' + Object.keys(segments).join(',') + ')' : 'NULL',
        heatmap: heatmap ? 'yes (keys: ' + Object.keys(heatmap).join(',') + ')' : 'NULL',
        health: health ? 'yes (keys: ' + Object.keys(health).join(',') + ')' : 'NULL'
      });

      // Render non-chart sections immediately
      if (overview) {
        renderStats(overview);
        // Schedule chart that depends on overview data
        registerLazyChart('popular-genres-bar', function() {
          renderPopularGenres(overview.popular_genres || []);
        });
      }
      if (segments) {
        registerLazyChart('user-segments-pie', function() {
          renderUserSegments(segments.activity_segments, segments.rating_segments);
        });
        // Rating preferences pie is in the same card
        registerLazyChart('rating-preferences-pie', function() {
          renderUserSegments(segments.activity_segments, segments.rating_segments);
        });
      }
      if (heatmap) {
        registerLazyChart('activity-heatmap', function() {
          renderActivityHeatmap(heatmap.heatmap_data);
        });
      }
      if (health) {
        renderSystemHealth(health);
      }

      // Start lazy rendering
      startLazyObserver();

      if (btn) {
        btn.innerHTML = '<i class="ph ph-check-circle"></i> 刷新成功';
        setTimeout(function() { btn.innerHTML = origText; btn.disabled = false; }, 2000);
      }
    }).catch(function(e) {
      console.error('[EnhancedDashboard] Load failed:', e);
      // Show error on chart containers
      ['activity-heatmap', 'user-segments-pie', 'popular-genres-bar', 'rating-preferences-pie'].forEach(function(id) {
        setSkelError(document.getElementById(id), '加载失败，请刷新重试');
      });
      if (btn) {
        btn.innerHTML = '<i class="ph ph-x-circle"></i> 刷新失败';
        setTimeout(function() { btn.innerHTML = origText; btn.disabled = false; }, 2000);
      }
    }).finally(function() {
      _loading = false;
    });
  }

  // ── Export ────────────────────────────────────────

  function exportReport() {
    var ts = new Date().toISOString().slice(0, 10);
    var rows = ['﻿指标,数值'];
    var statIds = {
      'total-users': '总用户数', 'total-movies': '电影总数',
      'total-ratings': '总评分数', 'active-users-today': '今日活跃用户',
      'users-this-week': '本周新增用户', 'ratings-today': '今日评分数'
    };
    Object.keys(statIds).forEach(function(id) {
      var el = document.getElementById(id);
      if (el) rows.push(statIds[id] + ',' + el.textContent);
    });
    var blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'dashboard-' + ts + '.csv';
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // ── Init ──────────────────────────────────────────

  function init() {
    console.log('[EnhancedDashboard] init() called');
    window.__ENHANCED_DASHBOARD_INITIALIZED = true;

    var refreshBtn = document.getElementById('refresh-dashboard-btn');
    var exportBtn = document.getElementById('export-dashboard-btn');
    if (refreshBtn) refreshBtn.addEventListener('click', loadAll);
    if (exportBtn) exportBtn.addEventListener('click', exportReport);
    loadAll();
  }

  // Expose for inline fallback
  window.__initEnhancedDashboard = init;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
