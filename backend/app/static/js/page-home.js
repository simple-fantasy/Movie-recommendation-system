/* =========================================
   CineMatch Home Page — Vue 3 Application
   ========================================= */

(function () {
  const { createApp } = Vue;
  const { MovieRow, MovieCard, StarRating } = window.CinemaComponents;

  const GENRE_MAP = window.GENRE_MAP || {};

  function formatGenre(g) {
    return GENRE_MAP[g] || g;
  }

  // ── ECharts helper ──────────────────────────────────

  function initChart(containerId, builder) {
    const dom = document.getElementById(containerId);
    if (!dom) return null;
    let instance = echarts.getInstanceByDom(dom);
    if (instance) instance.dispose();
    instance = echarts.init(dom, 'dark');
    try {
      const option = builder();
      if (option) instance.setOption(option);
    } catch (e) {
      dom.innerHTML =
        '<div class="d-flex flex-column align-items-center justify-content-center h-100 text-muted"><span style="font-size:1.5rem;margin-bottom:0.5rem;">—</span><small>暂无足够数据生成图表</small></div>';
    }
    return instance;
  }

  // ── Vue App ─────────────────────────────────────────

  const cinemaApp = createApp({
    components: { MovieRow, MovieCard, StarRating },

    data() {
      return {
        user: null,

        // Hero
        heroMovie: null,
        heroLoading: true,
        heroError: false,
        heroPool: [],
        heroIndex: 0,

        // Sections
        recommendations: [],
        recsLoading: true,
        recsError: false,
        recsIsPersonalized: false,

        popular: [],
        popularLoading: true,
        popularError: false,

        myRatings: [],
        ratingsLoading: true,
        ratingsError: false,

        // Search
        searchQuery: '',
        searchResults: [],
        searchLoading: false,
        searched: false,

        // Genre discovery
        genrePills: [
          'Action', 'Comedy', 'Drama', 'Sci-Fi', 'Horror',
          'Romance', 'Thriller', 'Animation', 'Crime', 'Adventure',
        ],
        activeGenre: null,
        genreResults: [],
        genreLoading: false,

        // Quick-rate modal
        rateTarget: null,
        newRating: 0,
      };
    },

    created() {
      this._charts = [];
      this._doSearchDebounced = debounce(this.doSearch, 300);
    },

    async mounted() {
      await this.checkAuth();

      // Fire all independent data fetches in parallel
      this.loadHero();
      this.loadRecommendations();
      this.loadPopular();

      if (this.user) {
        this.loadMyRatings();
        this.$nextTick(() => {
          this.loadPersonaChart();
          this.loadTimelineChart();
        });
      }
    },

    methods: {
      // ── Auth ──────────────────────────────────────

      async checkAuth() {
        try {
          const me =
            window._authPromise ? await window._authPromise : await api('/api/me');
          this.user = me && me.authenticated ? me : null;
        } catch (e) {
          this.user = null;
        }
      },

      // ── Hero ──────────────────────────────────────

      async loadHero() {
        this.heroLoading = true;
        this.heroError = false;
        try {
          const movies = await api('/api/movies/popular?limit=5');
          if (movies && movies.length) {
            this.heroPool = movies.map(normalizeMovie);
            this.heroIndex = 0;
            this.heroMovie = this.heroPool[0];
            // Enrich with detail
            try {
              const detail = await api('/api/movies/' + this.heroMovie.id);
              if (detail) {
                this.heroMovie = { ...this.heroMovie, ...normalizeMovie(detail) };
              }
            } catch (e) { /* ignore detail failure */ }
          } else {
            this.heroMovie = {
              id: null, title: '欢迎来到 CineMatch', poster: '', backdrop: '',
              overview: '电影数据库正在准备中。', year: null, avg_rating: null,
            };
          }
        } catch (e) {
          console.error('Hero load failed', e);
          this.heroError = true;
          this.heroMovie = {
            id: null, title: '欢迎来到 CineMatch', poster: '', backdrop: '',
            overview: '加载失败，请刷新页面重试。', year: null, avg_rating: null,
          };
        } finally {
          this.heroLoading = false;
        }
      },

      nextHero() {
        if (!this.heroPool.length) return;
        this.heroIndex = (this.heroIndex + 1) % this.heroPool.length;
        const next = this.heroPool[this.heroIndex];
        this.heroMovie = next;
        // Try loading detail for this hero too
        api('/api/movies/' + next.id)
          .then((detail) => {
            if (detail) {
              this.heroMovie = { ...this.heroMovie, ...normalizeMovie(detail) };
            }
          })
          .catch(() => {});
      },

      // ── Recommendations ───────────────────────────

      async loadRecommendations() {
        this.recsLoading = true;
        this.recsError = false;
        try {
          let data;
          if (this.user) {
            data = await api('/api/recommendations?n=20&strategy=hybrid');
            this.recsIsPersonalized = true;
          } else {
            data = await api('/api/movies/popular?limit=20');
            this.recsIsPersonalized = false;
          }
          const list = Array.isArray(data) ? data : data.recommendations || [];
          this.recommendations = list.map(normalizeMovie);
        } catch (e) {
          this.recommendations = [];
          if (!(e.response && e.response.status === 401)) {
            this.recsError = true;
          }
        } finally {
          this.recsLoading = false;
        }
      },

      // ── Popular ───────────────────────────────────

      async loadPopular() {
        this.popularLoading = true;
        this.popularError = false;
        try {
          const movies = await api('/api/movies/popular?limit=20');
          this.popular = (movies || []).map(normalizeMovie);
        } catch (e) {
          this.popular = [];
          this.popularError = true;
        } finally {
          this.popularLoading = false;
        }
      },

      // ── My Ratings ────────────────────────────────

      async loadMyRatings() {
        if (!this.user) return;
        this.ratingsLoading = true;
        this.ratingsError = false;
        try {
          const list = await api('/api/my/ratings?limit=20');
          const ratings = Array.isArray(list) ? list : list.ratings || [];
          this.myRatings = ratings.map((r) => {
            const m = normalizeMovie(r);
            // Preserve the user's own rating from the response
            m.user_rating = r.rating ?? r.user_rating ?? null;
            return m;
          });
        } catch (e) {
          this.myRatings = [];
          this.ratingsError = true;
        } finally {
          this.ratingsLoading = false;
        }
      },

      // ── Search ────────────────────────────────────

      onSearchInput() {
        this.searched = true;
        this._doSearchDebounced();
      },

      async doSearch() {
        const q = this.searchQuery.trim();
        if (!q) {
          this.searchResults = [];
          this.searched = false;
          return;
        }
        this.searchLoading = true;
        try {
          const res = await api('/api/movies?q=' + encodeURIComponent(q) + '&limit=12');
          this.searchResults = (Array.isArray(res) ? res : res.movies || []).map(normalizeMovie);
        } catch (e) {
          this.searchResults = [];
          showToast('搜索失败，请稍后重试', 'error');
        } finally {
          this.searchLoading = false;
        }
      },

      // ── Genre Discovery ───────────────────────────

      async searchByGenre(genre) {
        if (this.activeGenre === genre) {
          this.activeGenre = null;
          this.genreResults = [];
          return;
        }
        this.activeGenre = genre;
        this.genreLoading = true;
        try {
          const res = await api('/api/movies?q=' + encodeURIComponent(genre) + '&limit=10');
          this.genreResults = (Array.isArray(res) ? res : res.movies || []).map(normalizeMovie);
        } catch (e) {
          this.genreResults = [];
          showToast('加载失败', 'error');
        } finally {
          this.genreLoading = false;
        }
      },

      // ── Navigation ────────────────────────────────

      goToMovie(movie) {
        const id = movie.id || movie.movie_id;
        if (id) window.location.href = '/movie/' + id;
      },

      // ── Rating ────────────────────────────────────

      onRate({ movie }) {
        if (!this.user) {
          showToast('请先登录', 'error');
          window.location.href = '/login';
          return;
        }
        this.rateTarget = normalizeMovie(movie);
        this.newRating = 0;
        const modal = bootstrap.Modal.getOrCreateInstance(
          document.getElementById('rateModal')
        );
        modal.show();
      },

      showRateModal(movie) {
        if (!this.user) {
          showToast('请先登录', 'error');
          window.location.href = '/login';
          return;
        }
        this.rateTarget = normalizeMovie(movie);
        this.newRating = 0;
        const modal = bootstrap.Modal.getOrCreateInstance(
          document.getElementById('rateModal')
        );
        modal.show();
      },

      async submitRating() {
        if (!this.rateTarget || !this.newRating) return;
        const movieId = this.rateTarget.id || this.rateTarget.movie_id;
        try {
          await api('/api/ratings', {
            method: 'POST',
            body: { movie_id: movieId, rating: this.newRating },
          });
          showToast('评分成功！', 'success');
          bootstrap.Modal.getInstance(document.getElementById('rateModal')).hide();
          if (this.user) {
            this.loadMyRatings();
            this.loadRecommendations();
          }
        } catch (e) {
          showToast(e.message || '评分失败，请稍后重试', 'error');
        }
      },

      // ── Charts ────────────────────────────────────

      async loadPersonaChart() {
        if (!this.user) return;
        const chart = initChart('chartPersona', () => {
          // placeholder — real option built after data
          return null;
        });
        if (!chart) return;
        this._charts.push(chart);

        try {
          const data = await api('/api/my/persona');
          const labels = data.labels || [];
          const values = data.values || [];
          if (!labels.length) throw new Error('empty');
          const maxV = Math.max(...values, 1);
          const normalized = values.map((v) => v / maxV);

          chart.setOption({
            backgroundColor: 'transparent',
            tooltip: { trigger: 'item' },
            radar: {
              indicator: labels.map((g) => ({ name: g, max: 1 })),
              axisName: { color: '#a3a3a3', fontSize: 11 },
              splitArea: {
                areaStyle: {
                  color: [
                    'rgba(255,255,255,0.02)',
                    'rgba(255,255,255,0.05)',
                  ],
                },
              },
              axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
              splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
            },
            series: [
              {
                type: 'radar',
                data: [
                  {
                    value: normalized,
                    name: '我的偏好',
                    areaStyle: { color: 'rgba(229,160,13,0.25)' },
                    lineStyle: { color: '#e5a00d', width: 2 },
                    itemStyle: { color: '#e5a00d' },
                  },
                ],
              },
            ],
          });
        } catch (e) {
          const dom = document.getElementById('chartPersona');
          if (dom) {
            dom.innerHTML =
              '<div class="d-flex flex-column align-items-center justify-content-center h-100 text-muted"><i class="ph ph-chart-radar" style="font-size:2rem;margin-bottom:0.5rem;"></i><span>评分更多电影来生成画像</span></div>';
          }
        }
      },

      async loadTimelineChart() {
        if (!this.user) return;
        const chart = initChart('chartTimeline', () => null);
        if (!chart) return;
        this._charts.push(chart);

        try {
          const data = await api('/api/my/timeline');
          const months = data.months || [];
          const counts = data.counts || [];
          const avgs = data.avg_ratings || [];
          if (!months.length) throw new Error('empty');

          chart.setOption({
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis' },
            legend: {
              data: ['评分次数', '平均评分'],
              textStyle: { color: '#a3a3a3' },
              bottom: 0,
            },
            grid: {
              left: '3%', right: '4%', bottom: '15%', top: '10%',
              containLabel: true,
            },
            xAxis: {
              type: 'category', data: months,
              axisLine: { lineStyle: { color: '#444' } },
              axisLabel: { color: '#888' },
            },
            yAxis: [
              {
                type: 'value', name: '次数',
                axisLine: { lineStyle: { color: '#444' } },
                splitLine: { lineStyle: { color: '#222' } },
                axisLabel: { color: '#888' },
              },
              {
                type: 'value', name: '均分', min: 0, max: 5,
                axisLine: { lineStyle: { color: '#444' } },
                splitLine: { show: false },
                axisLabel: { color: '#888' },
              },
            ],
            series: [
              {
                name: '评分次数', type: 'bar', data: counts,
                itemStyle: { color: '#e5a00d', borderRadius: [4, 4, 0, 0] },
              },
              {
                name: '平均评分', type: 'line', yAxisIndex: 1, data: avgs,
                itemStyle: { color: '#3b82f6' },
                smooth: true, symbol: 'circle', symbolSize: 6,
              },
            ],
          });
        } catch (e) {
          const dom = document.getElementById('chartTimeline');
          if (dom) {
            dom.innerHTML =
              '<div class="d-flex flex-column align-items-center justify-content-center h-100 text-muted"><i class="ph ph-calendar" style="font-size:2rem;margin-bottom:0.5rem;"></i><span>暂无时间线数据</span></div>';
          }
        }
      },

      // ── Helpers ───────────────────────────────────

      formatTitle(title) {
        return formatMovieTitle(title);
      },

      normalizeMovie(raw) {
        return normalizeMovie(raw);
      },

      formatGenre(g) {
        return formatGenre(g);
      },
    },
  });

  // ── Cleanup ─────────────────────────────────────────
  // Clean up ECharts instances when navigating away
  window.addEventListener('beforeunload', () => {
    cinemaApp._charts &&
      cinemaApp._charts.forEach((c) => {
        try { c.dispose(); } catch (e) { /* ignore */ }
      });
  });

  // Attach resize handler for charts
  window.addEventListener('resize', () => {
    cinemaApp._charts &&
      cinemaApp._charts.forEach((c) => {
        try { c.resize(); } catch (e) { /* ignore */ }
      });
  });

  cinemaApp.mount('#cinemaApp');
})();
