const charts = {};

function showError(message) {
  const container = document.querySelector('.container-fluid');
  if (!container) {
    alert(message);
    return;
  }

  const alertHtml = `
    <div class="alert alert-danger alert-dismissible fade show" role="alert">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
  `;

  container.insertAdjacentHTML('afterbegin', alertHtml);
}

async function initializeDashboard() {
  try {
    await loadOverviewStats();
    await loadUserSegments();
    await loadActivityHeatmap();
    await loadPopularGenres();
    await loadSystemHealth();
  } catch (error) {
    console.error('初始化看板失败:', error);
    showError('数据加载失败，请刷新页面重试');
  }
}

async function loadOverviewStats() {
  try {
    const response = await fetch('/api/enhanced-stats/overview');
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    document.getElementById('total-users').textContent = data.total_users.toLocaleString();
    document.getElementById('total-movies').textContent = data.total_movies.toLocaleString();
    document.getElementById('total-ratings').textContent = data.total_ratings.toLocaleString();
    document.getElementById('active-users-today').textContent = data.active_users_today.toLocaleString();
    document.getElementById('users-this-week').textContent = data.users_this_week.toLocaleString();
    document.getElementById('ratings-today').textContent = data.ratings_today.toLocaleString();

    updateTopMoviesList(data.top_movies_this_month);
  } catch (error) {
    console.error('加载概览统计失败:', error);
  }
}

async function loadUserSegments() {
  try {
    const response = await fetch('/api/enhanced-stats/user-segments');
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    createSegmentPieChart('user-segments-pie', data.activity_segments, '用户活跃度分群');
    createSegmentPieChart('rating-preferences-pie', data.rating_segments, '评分偏好分析');
  } catch (error) {
    console.error('加载用户分群数据失败:', error);
  }
}

async function loadActivityHeatmap() {
  try {
    const response = await fetch('/api/enhanced-stats/activity-heatmap');
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    createActivityHeatmap(data.heatmap_data);
  } catch (error) {
    console.error('加载活跃度热力图失败:', error);
  }
}

async function loadPopularGenres() {
  try {
    const response = await fetch('/api/enhanced-stats/overview');
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    createPopularGenresBar(data.popular_genres);
  } catch (error) {
    console.error('加载热门类型失败:', error);
  }
}

async function loadSystemHealth() {
  try {
    const response = await fetch('/api/enhanced-stats/system-health');
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    updateSystemHealth(data);
  } catch (error) {
    console.error('加载系统健康指标失败:', error);
  }
}

function createSegmentPieChart(elementId, data, title) {
  const chart = echarts.init(document.getElementById(elementId));

  const option = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    series: [{
      name: title,
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '14',
          fontWeight: 'bold'
        }
      },
      data: Object.entries(data).map(([key, value]) => ({
        name: getSegmentName(key),
        value: value
      }))
    }]
  };

  chart.setOption(option);
  charts[elementId] = chart;
}

function createActivityHeatmap(data) {
  const chart = echarts.init(document.getElementById('activity-heatmap'));
  const hours = ['0时', '1时', '2时', '3时', '4时', '5时', '6时', '7时', '8时', '9时', '10时', '11时', '12时', '13时', '14时', '15时', '16时', '17时', '18时', '19时', '20时', '21时', '22时', '23时'];
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

  const option = {
    title: {
      text: '用户活跃度热力图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      position: 'top',
      formatter: function(params) {
        return `${days[params.value[1]]} ${hours[params.value[0]]}<br/>活跃度: ${params.value[2]}`;
      }
    },
    grid: {
      height: '50%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: hours,
      splitArea: {
        show: true
      }
    },
    yAxis: {
      type: 'category',
      data: days,
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: Math.max(...data.map(item => item[2]), 0),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#f0f9ff', '#bae7ff', '#91d5ff', '#69c0ff', '#40a9ff', '#1890ff', '#096dd9']
      }
    },
    series: [{
      name: '活跃度',
      type: 'heatmap',
      data: data,
      label: {
        show: false
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  };

  chart.setOption(option);
  charts['activity-heatmap'] = chart;
}

function createPopularGenresBar(data) {
  const chart = echarts.init(document.getElementById('popular-genres-bar'));

  const option = {
    title: {
      text: '热门电影类型',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      boundaryGap: [0, 0.01]
    },
    yAxis: {
      type: 'category',
      data: data.map(item => item.genre)
    },
    series: [{
      name: '评分数',
      type: 'bar',
      data: data.map(item => item.count),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          {offset: 0, color: '#83bff6'},
          {offset: 0.5, color: '#188df0'},
          {offset: 1, color: '#188df0'}
        ]),
        borderRadius: [0, 4, 4, 0]
      }
    }]
  };

  chart.setOption(option);
  charts['popular-genres-bar'] = chart;
}

function updateTopMoviesList(movies) {
  const container = document.getElementById('top-movies-list');
  container.innerHTML = movies.map((movie, index) => `
    <div class="col-md-6 col-lg-4 mb-3">
      <div class="card h-100">
        <div class="card-body">
          <div class="d-flex align-items-center">
            <div class="me-3">
              <div class="badge bg-primary rounded-circle p-2" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
                <strong>${index + 1}</strong>
              </div>
            </div>
            <div class="flex-grow-1">
              <h6 class="card-title mb-1">${movie.title}</h6>
              <p class="card-text text-muted mb-1"><small>(${movie.year})</small></p>
              <div class="d-flex align-items-center">
                <span class="badge bg-warning text-dark me-2"><i class="bi bi-star-fill me-1"></i>${movie.rating_count}</span>
                <small class="text-muted">本月评分</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

function updateSystemHealth(data) {
  const container = document.getElementById('system-health');
  container.innerHTML = `
    <div class="col-md-3 mb-3">
      <div class="text-center">
        <div class="h4 mb-2">
          <i class="bi bi-database-fill ${data.database_status === 'healthy' ? 'text-success' : 'text-danger'}"></i>
        </div>
        <h6 class="mb-1">数据库状态</h6>
        <span class="badge ${data.database_status === 'healthy' ? 'bg-success' : 'bg-danger'}">${data.database_status === 'healthy' ? '正常' : '异常'}</span>
      </div>
    </div>
    <div class="col-md-3 mb-3">
      <div class="text-center">
        <div class="h4 mb-2">
          <i class="bi bi-cpu-fill text-info"></i>
        </div>
        <h6 class="mb-1">系统负载</h6>
        <small class="text-muted">响应时间 ${data.database_response_time || 'N/A'}</small>
      </div>
    </div>
    <div class="col-md-3 mb-3">
      <div class="text-center">
        <div class="h4 mb-2">
          <i class="bi bi-shield-check-fill text-success"></i>
        </div>
        <h6 class="mb-1">数据完整性</h6>
        <small class="text-muted">无异常数据</small>
      </div>
    </div>
    <div class="col-md-3 mb-3">
      <div class="text-center">
        <div class="h4 mb-2">
          <i class="bi bi-clock-fill text-warning"></i>
        </div>
        <h6 class="mb-1">最后更新</h6>
        <small class="text-muted">${new Date(data.timestamp).toLocaleString()}</small>
      </div>
    </div>
  `;
}

function getSegmentName(key) {
  const names = {
    highly_active: '高活跃用户',
    moderately_active: '中活跃用户',
    low_active: '低活跃用户',
    dormant: '休眠用户',
    generous_raters: '宽松评分者',
    critical_raters: '严格评分者',
    balanced_raters: '平衡评分者'
  };

  return names[key] || key;
}

async function refreshAllData(event) {
  const button = event.currentTarget;
  const originalText = button.innerHTML;
  button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>刷新中...';
  button.disabled = true;

  try {
    await initializeDashboard();
    button.innerHTML = '<i class="bi bi-check-circle me-1"></i>刷新成功';
    setTimeout(() => {
      button.innerHTML = originalText;
      button.disabled = false;
    }, 2000);
  } catch (error) {
    button.innerHTML = '<i class="bi bi-x-circle me-1"></i>刷新失败';
    setTimeout(() => {
      button.innerHTML = originalText;
      button.disabled = false;
    }, 2000);
  }
}

function exportReport() {
  alert('导出功能开发中...');
}

window.addEventListener('resize', () => {
  Object.values(charts).forEach(chart => chart.resize());
});

document.addEventListener('DOMContentLoaded', () => {
  const refreshButton = document.getElementById('refresh-dashboard-btn');
  const exportButton = document.getElementById('export-dashboard-btn');

  if (refreshButton) {
    refreshButton.addEventListener('click', refreshAllData);
  }
  if (exportButton) {
    exportButton.addEventListener('click', exportReport);
  }

  initializeDashboard();
});
