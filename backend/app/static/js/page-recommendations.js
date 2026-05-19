/* =========================================
   CineMatch Recommendations — Vue 3 Application
   ========================================= */

(function () {
  const { createApp } = Vue;
  const { MovieCard, SkeletonGrid } = window.CinemaComponents;

  const GENRE_MAP = window.GENRE_MAP || {};

  function formatGenre(g) {
    return GENRE_MAP[g] || g;
  }

  // ── RecommendationCard (local component) ────────────

  const RecommendationCard = {
    props: {
      movie: { type: Object, required: true },
      rank: { type: Number, default: 0 },
      feedbackState: { type: String, default: null },
      whyText: { type: String, default: null },
      whyLoading: { type: Boolean, default: false },
    },
    emits: ['click', 'feedback', 'watched', 'hover-why'],
    template: `
      <div class="rec-card h-100">
        <!-- Rank badge (top 3 only) -->
        <div v-if="rank <= 3 && rank >= 1" class="rec-rank" :class="'rec-rank-' + rank">#{{ rank }}</div>

        <!-- Match score badge -->
        <div v-if="matchScore != null" class="rec-match-badge" :class="matchLevel">
          <span class="rec-match-dot"></span>
          {{ matchScore }}% 匹配
        </div>

        <!-- Poster area -->
        <div class="rec-poster" @click="$emit('click', movie)">
          <img v-if="showPoster" :src="posterSrc"
               :alt="formatTitle(movie.title)" 
               @error="onPosterError" />
          <div v-else class="rec-poster-placeholder" :style="gradStyle">
            <span class="rec-placeholder-icon">🎬</span>
            <span class="rec-placeholder-initial">{{ initial }}</span>
          </div>
          <!-- Hover overlay -->
          <div class="rec-overlay">
            <button class="rec-action-btn" title="查看详情" @click.stop="$emit('click', movie)">
              <i class="ph ph-eye"></i>
            </button>
            <button class="rec-action-btn"
                    :class="{ active: feedbackState === 'like' }"
                    title="感兴趣" @click.stop="$emit('feedback', {movieId: movie.id, type: 'like'})">
              <i class="ph ph-thumbs-up"></i>
            </button>
            <button class="rec-action-btn"
                    :class="{ active: feedbackState === 'dislike' }"
                    title="不感兴趣" @click.stop="$emit('feedback', {movieId: movie.id, type: 'dislike'})">
              <i class="ph ph-thumbs-down"></i>
            </button>
            <button class="rec-action-btn"
                    :class="{ active: feedbackState === 'watched' }"
                    title="已看过" @click.stop="$emit('watched', movie.id)">
              <i class="ph ph-check-fat"></i>
            </button>
            <button class="rec-action-btn" title="推荐理由"
                    @click.stop="$emit('hover-why', movie.id)">
              <i class="ph ph-info"></i>
            </button>
          </div>
        </div>

        <!-- Movie title — always visible below poster -->
        <div class="rec-info">
          <h3 class="rec-title" @click="$emit('click', movie)">{{ formatTitle(movie.title) }}</h3>
          <div class="rec-meta">
            <span v-if="movie.year" class="rec-year">{{ movie.year }}</span>
            <span v-if="movie.avg_rating != null" class="rec-rating">
              <i class="ph ph-star"></i> {{ movie.avg_rating.toFixed(1) }}
            </span>
          </div>
          <div class="rec-genres" v-if="movie.genres">
            <span v-for="g in genreList" :key="g" class="rec-genre-tag">{{ formatGenre(g) }}</span>
          </div>
        </div>

        <!-- Why explanation (always visible when available) -->
        <div v-if="whyLoading" class="rec-why rec-why-loading">
          <i class="ph ph-spinner"></i> 分析中...
        </div>
        <div v-else-if="whyText" class="rec-why">
          <i class="ph ph-lightbulb" style="color:var(--cinema-accent);font-size:0.7rem;"></i>
          <span>{{ whyText }}</span>
        </div>
      </div>
    `,
    data() {
      return { posterFailed: false };
    },
    computed: {
      genreList() {
        if (!this.movie.genres) return [];
        return String(this.movie.genres).split('|').filter(Boolean).slice(0, 3);
      },
      posterSrc() {
        const url = this.movie.poster || this.movie.poster_url || null;
        return optimizePosterUrl(url, 'w342');
      },
      showPoster() {
        return !this.posterFailed && hasValidPoster(this.posterSrc);
      },
      gradStyle() {
        return posterGradientStyle(this.movie.title);
      },
      initial() {
        return posterInitial(this.movie.title);
      },
      matchScore() {
        const rating = this.movie.avg_rating;
        const count = this.movie.rating_count || 0;
        if (rating == null) return null;
        let score = (rating / 5) * 70 + Math.min(count / 500, 1) * 30;
        return Math.round(Math.min(score, 99));
      },
      matchLevel() {
        const s = this.matchScore;
        if (s == null) return '';
        if (s >= 85) return 'match-high';
        if (s >= 70) return 'match-mid';
        return 'match-ok';
      },
    },
    methods: {
      onPosterError() {
        this.posterFailed = true;
      },
      formatTitle(title) {
        return formatMovieTitle(title);
      },
      formatGenre(g) {
        return formatGenre(g);
      },
    },
  };

  // ── Vue App ─────────────────────────────────────────

  const recApp = createApp({
    components: { MovieCard, SkeletonGrid, RecommendationCard },

    data() {
      return {
        user: null,
        allMovies: [],          // full fetch (up to 50)
        displayCount: 24,       // how many to show
        loading: true,
        error: false,
        errorCode: null,        // 'MODEL_LOADING' | 'MODEL_NOT_AVAILABLE' | null
        errorMessage: '',
        retryTimer: null,
        retrySeconds: 0,

        currentStrategy: 'popular',
        strategies: [
          { key: 'popular', label: '热门高分', icon: 'ph-fire' },
          { key: 'itemcf', label: 'ItemCF', icon: 'ph-target' },
          { key: 'ncf', label: 'NCF', icon: 'ph-brain' },
          { key: 'hybrid', label: '混合推荐', icon: 'ph-lightning' },
        ],

        feedback: {},           // { movieId: 'like'|'dislike' }
        whyCache: {},           // { movieId: text }
        whyLoading: {},         // { movieId: true }

        // Filters
        filterGenre: null,
        filterGenres: [],
        showFilters: false,
      };
    },

    computed: {
      movies() {
        let list = this.allMovies;
        if (this.filterGenre) {
          list = list.filter((m) => {
            const genres = String(m.genres || '').toLowerCase();
            return genres.includes(this.filterGenre.toLowerCase());
          });
        }
        return list.slice(0, this.displayCount);
      },

      hasMore() {
        let list = this.allMovies;
        if (this.filterGenre) {
          list = list.filter((m) => {
            const genres = String(m.genres || '').toLowerCase();
            return genres.includes(this.filterGenre.toLowerCase());
          });
        }
        return this.displayCount < list.length;
      },

      availableGenres() {
        const set = new Set();
        this.allMovies.forEach((m) => {
          String(m.genres || '')
            .split('|')
            .filter(Boolean)
            .forEach((g) => set.add(g.trim()));
        });
        return Array.from(set).sort();
      },
    },

    async mounted() {
      await this.checkAuth();
      // Default to popular for guests, hybrid for logged-in
      if (!this.user) {
        this.currentStrategy = 'popular';
      } else {
        this.currentStrategy = 'hybrid';
      }
      this.loadRecommendations();
    },

    methods: {
      async checkAuth() {
        try {
          const me =
            window._authPromise ? await window._authPromise : await api('/api/me');
          this.user = me && me.authenticated ? me : null;
        } catch (e) {
          this.user = null;
        }
      },

      switchStrategy(key) {
        if (this.retryTimer) {
          clearInterval(this.retryTimer);
          this.retryTimer = null;
        }
        this.currentStrategy = key;
        this.allMovies = [];
        this.displayCount = 24;
        this.whyCache = {};
        this.whyLoading = {};
        this.filterGenre = null;
        this.showFilters = false;
        this.loadRecommendations();
      },

      async loadRecommendations() {
        this.loading = true;
        this.error = false;
        this.errorCode = null;
        this.errorMessage = '';

        try {
          let data;
          if (this.currentStrategy === 'popular') {
            // Use recommendation engine for fast loading (same as other strategies)
            data = await api('/api/recommendations?n=50&strategy=itemcf');
          } else {
            // Force login for personalized strategies
            if (!this.user) {
              showToast('请先登录以使用个性化推荐', 'error');
              this.currentStrategy = 'popular';
              data = await api('/api/recommendations?n=50&strategy=itemcf');
              return;
            }
            data = await api(
              '/api/recommendations?n=50&strategy=' + this.currentStrategy
            );
          }

          let list = Array.isArray(data) ? data : data.recommendations || [];
          this.allMovies = list.map(normalizeMovie);
          this.displayCount = 24;
          this.filterGenres = this.availableGenres;
          // Auto-fetch why explanations for first 6 cards
          if (this.user && this.allMovies.length) {
            this.$nextTick(() => {
              this.allMovies.slice(0, 6).forEach(m => this.fetchWhy(m.id));
            });
          }
        } catch (e) {
          console.error('Recommendations load failed', e);
          this.allMovies = [];

          // Parse 503 errors
          if (e.response && e.response.status === 503) {
            const msg =
              (e.data && (e.data.error || e.data.message)) || '';
            if (msg.includes('MODEL_LOADING') || msg.includes('loading')) {
              this.errorCode = 'MODEL_LOADING';
              this.errorMessage = '推荐模型正在加载中，请稍候...';
              this.startRetryCountdown(5);
            } else if (
              msg.includes('MODEL_NOT_AVAILABLE') ||
              msg.includes('not available')
            ) {
              this.errorCode = 'MODEL_NOT_AVAILABLE';
              this.errorMessage =
                '推荐模型暂不可用，已自动切换为热门推荐。';
              // Auto-fallback to popular
              setTimeout(() => {
                this.currentStrategy = 'popular';
                this.loadRecommendations();
              }, 2000);
            } else {
              this.error = true;
            }
          } else {
            this.error = true;
          }
        } finally {
          this.loading = false;
        }
      },

      startRetryCountdown(seconds) {
        this.retrySeconds = seconds;
        this.retryTimer = setInterval(() => {
          this.retrySeconds--;
          if (this.retrySeconds <= 0) {
            clearInterval(this.retryTimer);
            this.retryTimer = null;
            this.loadRecommendations();
          }
        }, 1000);
      },

      loadMore() {
        this.displayCount = Math.min(
          this.displayCount + 24,
          this.allMovies.length
        );
      },

      // ── Filters ──────────────────────────────────

      selectFilterGenre(genre) {
        if (this.filterGenre === genre) {
          this.filterGenre = null;
        } else {
          this.filterGenre = genre;
        }
        this.displayCount = 24;
      },

      // ── Why tooltip ──────────────────────────────

      async fetchWhy(movieId) {
        if (!this.user) return;
        if (this.whyCache[movieId] !== undefined) return;
        if (this.whyLoading[movieId]) return;

        this.whyLoading = { ...this.whyLoading, [movieId]: true };
        try {
          const data = await api('/api/recommendations/why/' + movieId);
          if (data && data.because && data.because.length) {
            const names = data.because
              .slice(0, 3)
              .map((b) => '《' + b.title + '》')
              .join('、');
            this.whyCache = {
              ...this.whyCache,
              [movieId]: '因为你喜欢 ' + names,
            };
          } else {
            this.whyCache = {
              ...this.whyCache,
              [movieId]: '基于你的观影偏好推荐',
            };
          }
        } catch (e) {
          this.whyCache = {
            ...this.whyCache,
            [movieId]: '推荐理由获取失败',
          };
        } finally {
          this.whyLoading = { ...this.whyLoading, [movieId]: false };
        }
      },

      // ── Feedback ─────────────────────────────────

      async sendFeedback(movieId, type) {
        if (!this.user) {
          showToast('请先登录', 'error');
          return;
        }
        // Optimistic update
        const prev = this.feedback[movieId];
        this.feedback = { ...this.feedback, [movieId]: type };
        try {
          await api('/api/feedback', {
            method: 'POST',
            body: { movie_id: movieId, feedback: type },
          });
          showToast(
            type === 'like' ? '感谢反馈！' : '已记录，将优化推荐',
            'success'
          );
        } catch (e) {
          // Revert
          this.feedback = { ...this.feedback, [movieId]: prev };
          showToast('反馈提交失败', 'error');
        }
      },

      async markWatched(movieId) {
        if (!this.user) {
          showToast('请先登录', 'error');
          return;
        }
        const prev = this.feedback[movieId];
        this.feedback = { ...this.feedback, [movieId]: 'watched' };
        try {
          await api('/api/ratings', {
            method: 'POST',
            body: { movie_id: movieId, rating: 3 },
          });
          showToast('已标记为看过', 'success');
          // Remove from list after short delay
          setTimeout(() => {
            this.allMovies = this.allMovies.filter(m => (m.id || m.movie_id) !== movieId);
          }, 500);
        } catch (e) {
          this.feedback = { ...this.feedback, [movieId]: prev };
          showToast('操作失败', 'error');
        }
      },

      // ── Navigation ───────────────────────────────

      goToMovie(movie) {
        const id = movie.id || movie.movie_id;
        if (id) window.location.href = '/movie/' + id;
      },

      // ── Helpers ───────────────────────────────────

      formatTitle(title) {
        return formatMovieTitle(title);
      },

      formatGenre(g) {
        return formatGenre(g);
      },

      rankStyle(idx) {
        if (idx === 0)
          return 'background:linear-gradient(135deg,#e5a00d,#f5b830);color:#0a0a0a;';
        if (idx === 1)
          return 'background:linear-gradient(135deg,#a3a3a3,#c0c0c0);color:#0a0a0a;';
        if (idx === 2)
          return 'background:linear-gradient(135deg,#cd7f32,#d48f50);color:#0a0a0a;';
        return '';
      },

      strategyColor(s) {
        const map = {
          itemcf: 'warning', ncf: 'info', hybrid: 'accent',
          popular: 'secondary', similarity: 'warning',
        };
        return map[s] || 'secondary';
      },

      strategyLabel(s) {
        const map = {
          itemcf: 'ItemCF', ncf: 'NCF', hybrid: '混合',
          popular: '热门', similarity: 'ItemCF',
        };
        return map[s] || s;
      },
    },
  });

  recApp.mount('#recApp');
})();
