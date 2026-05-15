let genresChart = null;
let yearsChart = null;

function displayGenresChart(genres) {
  const chartDom = document.getElementById('genres-chart');
  if (!chartDom) return;

  if (genresChart) {
    genresChart.dispose();
  }

  const data = Object.entries(genres || {}).map(([name, value]) => ({ name, value }));
  genresChart = echarts.init(chartDom);

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}'
    },
    series: [
      {
        name: '类型偏好',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        data
      }
    ]
  };

  genresChart.setOption(option);
}

function displayYearsChart(years) {
  const chartDom = document.getElementById('years-chart');
  if (!chartDom) return;

  if (yearsChart) {
    yearsChart.dispose();
  }

  const data = Object.entries(years || {}).map(([name, value]) => ({ name, value }));
  yearsChart = echarts.init(chartDom);

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '偏好度',
        type: 'bar',
        data: data.map(d => d.value),
        itemStyle: {
          color: '#3b82f6',
          borderRadius: [5, 5, 0, 0]
        }
      }
    ]
  };

  yearsChart.setOption(option);
}

function displayList(containerId, items, icon) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = '';

  if (!items || items.length === 0) {
    container.innerHTML = '<p class="text-muted">暂无数据</p>';
    return;
  }

  items.slice(0, 10).forEach(item => {
    const tag = document.createElement('span');
    tag.className = 'tag tag-primary';
    tag.textContent = `${icon} ${item}`;
    container.appendChild(tag);
  });
}

function displayUserType(userType, activityLevel) {
  const container = document.getElementById('user-type-tags');
  if (!container) return;

  container.innerHTML = '';
  const typeMap = {
    casual: '🌱 休闲用户',
    regular: '📚 常规用户',
    enthusiast: '🔥 资深影迷'
  };
  const activityMap = {
    low: '😴 低活跃',
    medium: '🚶 中活跃',
    high: '🏃 高活跃'
  };

  if (userType) {
    const tag = document.createElement('span');
    tag.className = 'tag tag-success';
    tag.textContent = typeMap[userType] || userType;
    container.appendChild(tag);
  }

  if (activityLevel) {
    const tag = document.createElement('span');
    tag.className = 'tag tag-warning';
    tag.textContent = activityMap[activityLevel] || activityLevel;
    container.appendChild(tag);
  }
}

function displayRatingBehavior(avgRating, variance) {
  const levelBar = document.getElementById('rating-level-bar');
  const varianceBar = document.getElementById('rating-variance-bar');
  if (avgRating && levelBar) {
    const percentage = (avgRating / 5) * 100;
    levelBar.style.width = `${percentage}%`;
    levelBar.textContent = `${avgRating.toFixed(1)}分`;
  }
  if (variance && varianceBar) {
    const percentage = Math.min(variance * 20, 100);
    varianceBar.style.width = `${percentage}%`;
    varianceBar.textContent = variance.toFixed(2);
  }
}

async function loadProfile() {
  try {
    const data = await api('/api/user/profile');

    if (data.profile) {
      displayProfile(data.profile);
    }
  } catch (error) {
    console.error('加载用户画像失败:', error);
    const content = document.getElementById('profile-content');
    if (content) {
      if (error.message.includes('401') || error.message.includes('登录')) {
        content.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🔒</div>
            <h3>请先登录</h3>
            <p>登录后可查看个性化用户画像</p>
            <a href="/login" class="btn btn-primary mt-3">去登录</a>
          </div>
        `;
      } else {
        content.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">⚠️</div>
            <h3>加载失败</h3>
            <p>${escapeHtml(error.message || '请稍后重试')}</p>
          </div>
        `;
      }
    }
  } finally {
    const loading = document.getElementById('loading');
    const content = document.getElementById('profile-content');
    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'block';
  }
}

function displayProfile(profile) {
  const avgRating = document.getElementById('avg-rating');
  const totalMovies = document.getElementById('total-movies');
  const watchTime = document.getElementById('watch-time');
  const diversity = document.getElementById('diversity');

  if (avgRating) avgRating.textContent = profile.avg_rating_level?.toFixed(1) || '-';
  if (totalMovies) totalMovies.textContent = Object.keys(profile.preferred_genres || {}).length;
  if (watchTime) watchTime.textContent = Math.round((profile.total_watch_time || 0) / 60);
  if (diversity) diversity.textContent = profile.genre_diversity?.toFixed(2) || '-';

  displayGenresChart(profile.preferred_genres);
  displayYearsChart(profile.preferred_years);
  displayList('actors-list', profile.preferred_actors, '👤');
  displayList('directors-list', profile.preferred_directors, '🎥');
  displayUserType(profile.user_type, profile.activity_level);
  displayRatingBehavior(profile.avg_rating_level, profile.rating_variance);
}

async function refreshProfile() {
  const loading = document.getElementById('loading');
  const content = document.getElementById('profile-content');
  if (loading) loading.style.display = 'flex';
  if (content) content.style.display = 'none';

  try {
    const data = await api('/api/user/profile/refresh', {
      method: 'POST',
      body: {}
    });

    if (data.success) {
      displayProfile(data.profile);
      alert('画像刷新成功！');
    } else {
      alert('画像刷新失败：' + (data.error || '请稍后重试'));
    }
  } catch (error) {
    console.error('刷新画像失败:', error);
    alert('刷新失败：' + (error.message || '请稍后重试'));
  } finally {
    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'block';
  }
}

window.addEventListener('resize', () => {
  if (genresChart) genresChart.resize();
  if (yearsChart) yearsChart.resize();
});

document.addEventListener('DOMContentLoaded', () => {
  const refreshButton = document.getElementById('refresh-profile-btn');
  if (refreshButton) {
    refreshButton.addEventListener('click', refreshProfile);
  }
  loadProfile();
});
