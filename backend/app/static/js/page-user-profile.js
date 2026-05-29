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
      displayProfile(data.profile, data.total_ratings || 0, data.needs_more_data);
      if (data.needs_more_data) {
        const hint = document.getElementById('profile-hint');
        if (hint) {
          hint.textContent = data.message || '多评几部电影后就能看到个性化的偏好分析啦';
          hint.style.display = 'block';
        }
      }
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
    if (loading) loading.style.setProperty('display', 'none', 'important');
    if (content) content.style.setProperty('display', 'block', 'important');
  }
}

function displayProfile(profile, totalRatings, needsMoreData) {
  const avgRating = document.getElementById('avg-rating');
  const totalMovies = document.getElementById('total-movies');
  const watchTime = document.getElementById('watch-time');
  const diversity = document.getElementById('diversity');

  if (avgRating) avgRating.textContent = profile.avg_rating_level?.toFixed(1) || '-';
  if (totalMovies) totalMovies.textContent = totalRatings || 0;
  if (watchTime) watchTime.textContent = Math.round((profile.total_watch_time || 0) / 60);
  if (diversity) diversity.textContent = profile.genre_diversity?.toFixed(2) || '-';

  displayList('actors-list', profile.preferred_actors, '👤');
  displayList('directors-list', profile.preferred_directors, '🎥');
  displayUserType(profile.user_type, profile.activity_level);
  displayRatingBehavior(profile.avg_rating_level, profile.rating_variance);
}

async function refreshProfile() {
  const loading = document.getElementById('loading');
  const content = document.getElementById('profile-content');
  if (loading) loading.style.setProperty('display', 'flex', 'important');
  if (content) content.style.setProperty('display', 'none', 'important');

  try {
    const data = await api('/api/user/profile/refresh', {
      method: 'POST',
      body: {}
    });

    if (data.success) {
      displayProfile(data.profile, data.total_ratings || 0, data.needs_more_data);
      alert('画像刷新成功！');
    } else {
      alert('画像刷新失败：' + (data.error || '请稍后重试'));
    }
  } catch (error) {
    console.error('刷新画像失败:', error);
    alert('刷新失败：' + (error.message || '请稍后重试'));
  } finally {
    if (loading) loading.style.setProperty('display', 'none', 'important');
    if (content) content.style.setProperty('display', 'block', 'important');
  }
}

function initProfile() {
  var refreshButton = document.getElementById('refresh-profile-btn');
  if (refreshButton) {
    refreshButton.addEventListener('click', refreshProfile);
  }
  loadProfile();
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initProfile);
} else {
  initProfile();
}
