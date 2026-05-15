document.addEventListener('DOMContentLoaded', () => {
  const state = {
    currentStrategy: 'popular',
    isLoggedIn: false,
    username: '',
    feedbackState: new Map(),
  };

  const recommendationsEl = document.getElementById('recommendations');
  const strategyCards = Array.from(document.querySelectorAll('.strategy-card'));
  const authStatus = document.getElementById('authStatus');
  const btnLogin = document.getElementById('btnLoginPage');
  const btnLogout = document.getElementById('btnLogout');

  async function init() {
    try {
      const me = await api('/api/me');
      state.isLoggedIn = Boolean(me.authenticated);
      state.username = me.username || '';
      setAuthUI(state.isLoggedIn, state.username);
    } catch (error) {
      state.isLoggedIn = false;
      setAuthUI(false, '');
    }

    attachStrategyListeners();
    attachLogoutListener();
    attachRecommendationActions();
    loadRecommendations('popular');
  }

  function setAuthUI(loggedIn, username) {
    if (!authStatus || !btnLogin || !btnLogout) return;
    authStatus.textContent = loggedIn ? `已登录：${username}` : '未登录';
    btnLogin.style.display = loggedIn ? 'none' : 'inline-block';
    btnLogout.style.display = loggedIn ? 'inline-block' : 'none';
  }

  function attachStrategyListeners() {
    strategyCards.forEach(card => {
      card.addEventListener('click', () => {
        strategyCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        state.currentStrategy = card.dataset.strategy || 'popular';
        loadRecommendations(state.currentStrategy);
      });
    });
  }

  function attachLogoutListener() {
    if (!btnLogout) return;
    btnLogout.addEventListener('click', async (event) => {
      event.preventDefault();
      try {
        await api('/api/auth/logout', { method: 'POST', body: {} });
        state.isLoggedIn = false;
        setAuthUI(false, '');
        loadRecommendations(state.currentStrategy);
      } catch (error) {
        showToast(`退出失败：${error.message}`, 'error');
      }
    });
  }

  function attachRecommendationActions() {
    if (!recommendationsEl) return;
    recommendationsEl.addEventListener('click', (event) => {
      const retryButton = event.target.closest('[data-action="reload-recommendations"]');
      if (retryButton) {
        loadRecommendations(state.currentStrategy);
      }
    });
  }

  function renderSkeletons() {
    if (!recommendationsEl) return;
    recommendationsEl.innerHTML = Array.from({ length: 6 }).map(() => '<div class="loading-skeleton"></div>').join('');
  }

  async function loadRecommendations(strategy) {
    if (!recommendationsEl) return;
    recommendationsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    renderSkeletons();

    try {
      let recs = [];

      if (strategy === 'popular') {
        const items = await api('/api/movies/popular?limit=20&min_count=50');
        recs = items.map(item => ({
          movie_id: item.id,
          title: item.title,
          year: item.year,
          genres: item.genres,
          score: item.avg_rating || 0,
          rating_count: item.rating_count || 0,
          reason: 'popular',
          because: [],
        }));
      } else {
        if (!state.isLoggedIn) {
          renderStateMessage(recommendationsEl, 'info', '需要登录', '个性化推荐需要登录后才能获取。', '<a href="/login" class="btn btn-primary">去登录</a>');
          return;
        }

        const data = await api(`/api/recommendations?n=12&strategy=${encodeURIComponent(strategy)}`);
        if (!Array.isArray(data)) {
          throw new Error('推荐结果格式异常');
        }
        recs = data.map(item => ({
          movie_id: item.movie_id,
          title: item.title,
          year: item.year,
          genres: item.genres,
          score: item.score || 0,
          rating_count: item.rating_count || 0,
          reason: item.reason || 'recommend',
          because: item.because || [],
        }));
      }

      renderRecommendations(recs, strategy);
    } catch (error) {
      renderStateMessage(recommendationsEl, 'error', '加载失败', error.message || '无法获取推荐结果。', '<button type="button" class="btn btn-outline-primary" data-action="reload-recommendations">重试</button>');
    }
  }

  function renderRecommendations(recs, strategy) {
    if (!recommendationsEl) return;
    if (!recs.length) {
      renderStateMessage(recommendationsEl, 'info', '暂无推荐', strategy === 'popular' ? '暂无热门电影数据。' : '请先评分几部电影，让我们了解你的喜好。', '<a href="/app" class="btn btn-primary">去评分</a>');
      return;
    }

    recommendationsEl.innerHTML = '';

    recs.forEach(rec => {
      const card = document.createElement('div');
      card.className = 'movie-card';

      const badgeClass = rec.reason === 'hybrid' ? 'badge-hybrid' : rec.reason === 'ncf' ? 'badge-ncf' : rec.reason === 'popular' ? 'badge-popular' : 'badge-itemcf';
      const badgeText = rec.reason === 'hybrid' ? '混合推荐' : rec.reason === 'ncf' ? 'NCF' : rec.reason === 'popular' ? '热门' : 'ItemCF';
      const formattedTitle = formatMovieTitle(rec.title);
      const displayScore = rec.rating_count ? `均分 ${Number(rec.score).toFixed(1)} · ${rec.rating_count}人评分` : `推荐分 ${Number(rec.score).toFixed(3)}`;
      const reasonHtml = rec.because && rec.because.length ? `<div class="movie-reason">${rec.because.slice(0, 3).map(item => `<span class="reason-pill">因为你喜欢：${escapeHtml(formatMovieTitle(item.title))}</span>`).join('')}</div>` : '';
      const feedback = state.feedbackState.get(rec.movie_id);
      const likeClass = feedback === 'like' ? 'active' : '';
      const dislikeClass = feedback === 'dislike' ? 'active' : '';
      const disabled = feedback ? 'disabled' : '';

      card.innerHTML = `
        <div class="movie-header">
          <a href="/movie/${rec.movie_id}" class="movie-title">${escapeHtml(formattedTitle)}</a>
          <span class="movie-badge ${badgeClass}">${badgeText}</span>
        </div>
        <div class="movie-meta">${rec.year ? `${rec.year} · ` : ''}${escapeHtml(rec.genres || '未知类型')}</div>
        <div class="movie-score">⭐ ${escapeHtml(displayScore)}</div>
        ${reasonHtml}
        <div class="feedback-bar">
          <button type="button" class="btn btn-sm btn-feedback btn-outline-success ${likeClass}" ${disabled} data-movie="${rec.movie_id}" data-type="like">👍 有用</button>
          <button type="button" class="btn btn-sm btn-feedback btn-outline-danger ${dislikeClass}" ${disabled} data-movie="${rec.movie_id}" data-type="dislike">👎 不相关</button>
        </div>
      `;

      card.querySelectorAll('.btn-feedback').forEach(button => {
        button.addEventListener('click', async (event) => {
          event.preventDefault();
          const movieId = Number(button.dataset.movie);
          const feedbackType = button.dataset.type;
          await sendFeedback(movieId, feedbackType, card);
        });
      });

      recommendationsEl.appendChild(card);
    });
  }

  async function sendFeedback(movieId, feedback, cardElement) {
    if (!state.isLoggedIn) {
      showToast('请先登录后再提交反馈', 'error');
      return;
    }

    try {
      await api('/api/feedback', { method: 'POST', body: { movie_id: movieId, feedback, context: 'recommend' } });
      state.feedbackState.set(movieId, feedback);
      cardElement.querySelectorAll('.btn-feedback').forEach(button => {
        button.disabled = true;
        if (button.dataset.type === feedback) {
          button.classList.add('active');
        }
      });
      showToast(feedback === 'like' ? '已标记为有用 👍' : '已标记为不相关 👎', 'success');
    } catch (error) {
      showToast(`反馈提交失败：${error.message}`, 'error');
    }
  }

  init();
});
