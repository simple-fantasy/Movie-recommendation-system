document.addEventListener('DOMContentLoaded', () => {
  const movieId = Number(document.querySelector('main')?.dataset.movieId || 0);
  const titleEl = document.getElementById('title');
  const metaEl = document.getElementById('meta');
  const movieIdEl = document.getElementById('movieId');
  const btnRate = document.getElementById('btnRate');
  const ratingInput = document.getElementById('rating');
  const rateMsg = document.getElementById('rateMsg');
  const btnLike = document.getElementById('btnLike');
  const btnDislike = document.getElementById('btnDislike');
  const fbMsg = document.getElementById('fbMsg');
  const whyEl = document.getElementById('why');
  const similarEl = document.getElementById('similar');

  async function init() {
    if (movieIdEl) {
      movieIdEl.textContent = movieId;
    }

    attachEvents();
    await loadMovieDetails();
  }

  function attachEvents() {
    if (btnRate && ratingInput) {
      btnRate.addEventListener('click', async () => {
        await rateMovie();
      });
    }

    if (btnLike) {
      btnLike.addEventListener('click', async () => {
        await sendFeedback('like');
      });
    }

    if (btnDislike) {
      btnDislike.addEventListener('click', async () => {
        await sendFeedback('dislike');
      });
    }
  }

  async function loadMovieDetails() {
    try {
      const [detail, whyData, similarData] = await Promise.all([
        api(`/api/movies/${movieId}`),
        api(`/api/recommendations/why/${movieId}`),
        api(`/api/movies/${movieId}/similar?n=8`),
      ]);

      renderDetail(detail);
      renderWhy(whyData);
      renderSimilar(similarData.similar || []);
    } catch (error) {
      if (titleEl) titleEl.textContent = '加载失败';
      if (metaEl) metaEl.textContent = error.message || '无法加载电影信息。';
      showToast(`电影详情加载失败：${error.message}`, 'error');
    }
  }

  function renderDetail(detail) {
    if (!detail) return;
    if (titleEl) titleEl.textContent = detail.title || '未知电影';
    if (metaEl) metaEl.textContent = `${detail.year || '未知年份'} · ${detail.genres || '未知类型'}`;
  }

  function renderWhy(data) {
    if (!whyEl) return;
    if (!data || !data.because || !data.because.length) {
      whyEl.textContent = '暂无推荐解释。';
      return;
    }

    whyEl.innerHTML = data.because.map((item) => `
      <div class="reason-pill">因为你喜欢：${escapeHtml(formatMovieTitle(item.title))}</div>
    `).join('');
  }

  function renderSimilar(similarItems) {
    if (!similarEl) return;
    if (!similarItems.length) {
      similarEl.innerHTML = '<div class="text-muted">暂无相似电影。</div>';
      return;
    }

    similarEl.innerHTML = similarItems.map((item) => `
      <a href="/movie/${item.movie_id}" class="list-group-item list-group-item-action">
        <strong>${escapeHtml(item.title)}</strong>
        <div class="small text-muted">${escapeHtml(item.genres || '未知类型')} · ${item.year || ''}</div>
      </a>
    `).join('');
  }

  async function rateMovie() {
    if (!ratingInput) return;
    const value = parseFloat(ratingInput.value);
    if (Number.isNaN(value) || value < 0.5 || value > 5) {
      showToast('评分必须在 0.5 到 5.0 之间', 'error');
      return;
    }

    try {
      await api('/api/ratings', { method: 'POST', body: { movie_id: movieId, rating: value } });
      if (rateMsg) {
        rateMsg.textContent = '评分提交成功。';
        rateMsg.className = 'mt-2 small-note text-success';
      }
      showToast('已提交评分', 'success');
    } catch (error) {
      if (rateMsg) {
        rateMsg.textContent = error.message || '评分提交失败。';
        rateMsg.className = 'mt-2 small-note text-danger';
      }
      showToast(`评分失败：${error.message}`, 'error');
    }
  }

  async function sendFeedback(feedback) {
    if (!btnLike || !btnDislike) return;
    if (btnLike.disabled || btnDislike.disabled) return;

    try {
      await api('/api/feedback', { method: 'POST', body: { movie_id: movieId, feedback, context: 'movie' } });
      btnLike.disabled = true;
      btnDislike.disabled = true;
      if (feedback === 'like') {
        btnLike.classList.remove('btn-outline-success');
        btnLike.classList.add('btn-success');
      } else {
        btnDislike.classList.remove('btn-outline-danger');
        btnDislike.classList.add('btn-danger');
      }
      if (fbMsg) {
        fbMsg.textContent = feedback === 'like' ? '已标记为有用' : '已标记为不相关';
        fbMsg.className = 'mt-2 small-note text-success';
      }
      showToast('反馈已提交', 'success');
    } catch (error) {
      if (fbMsg) {
        fbMsg.textContent = error.message || '反馈提交失败。';
        fbMsg.className = 'mt-2 small-note text-danger';
      }
      showToast(`反馈失败：${error.message}`, 'error');
    }
  }

  init();
});
