/* =========================================
   CineMatch Vue 3 Components (Global Build)
   ========================================= */

const { createApp } = Vue;

/* ---------- StarRating ---------- */
const StarRating = {
  props: {
    modelValue: { type: Number, default: 0 },
    max: { type: Number, default: 5 },
    readonly: { type: Boolean, default: false },
    size: { type: String, default: '1.25rem' }
  },
  emits: ['update:modelValue', 'rate'],
  template: `
    <div class="star-rating" :style="{fontSize: size}">
      <span v-for="n in max" :key="n"
            class="star"
            :class="{active: n <= hoverValue}"
            @mouseenter="readonly ? null : hoverValue = n"
            @mouseleave="readonly ? null : hoverValue = modelValue || 0"
            @click="readonly ? null : onClick(n)">
        ★
      </span>
    </div>
  `,
  data() {
    return { hoverValue: this.modelValue || 0 };
  },
  watch: {
    modelValue(val) { this.hoverValue = val || 0; }
  },
  methods: {
    onClick(n) {
      // Ripple animation
      this.$el.querySelectorAll('.star')[n - 1]?.classList.add('star-ripple');
      setTimeout(() => {
        this.$el.querySelectorAll('.star')[n - 1]?.classList.remove('star-ripple');
      }, 400);
      this.$emit('update:modelValue', n);
      this.$emit('rate', n);
    }
  }
};

/* ---------- MovieCard ---------- */
const MovieCard = {
  props: {
    movie: { type: Object, required: true },
    showRating: { type: Boolean, default: false },
    showActions: { type: Boolean, default: true }
  },
  emits: ['click', 'rate', 'collect'],
  components: { StarRating },
  template: `
    <div class="movie-card" @click="onCardClick">
      <img v-if="showPoster" :src="posterUrl" :alt="displayTitle"
           @error="onPosterError">
      <div v-else class="poster-gradient" :style="gradStyle">
        <span class="poster-initial">{{ initial }}</span>
      </div>
      <div class="overlay">
        <div class="title">{{ displayTitle }}</div>
        <div class="meta">
          <span v-if="movie.year">{{ movie.year }}</span>
          <span v-if="ratingDisplay" style="color: var(--cinema-accent)">★ {{ ratingDisplay }}</span>
        </div>
        <star-rating v-if="showRating && movie.user_rating !== undefined"
                     :model-value="Math.round(movie.user_rating)"
                     size="0.85rem"
                     @rate="$emit('rate', {movie, rating: $event})">
        </star-rating>
        <div v-if="showActions && !showRating" class="actions">
          <button class="action-btn" title="查看详情" @click.stop="goToDetail">
            <i class="ph ph-eye"></i>
          </button>
          <button class="action-btn" title="评分" @click.stop="quickRate">
            <i class="ph ph-star"></i>
          </button>
        </div>
      </div>
    </div>
  `,
  data() {
    return { posterFailed: false };
  },
  computed: {
    displayTitle() {
      return formatMovieTitle(this.movie.title || this.movie.name || '未知电影');
    },
    posterUrl() {
      const url = this.movie.poster || this.movie.poster_url || null;
      return optimizePosterUrl(url, 'w342');
    },
    showPoster() {
      return !this.posterFailed && hasValidPoster(this.posterUrl);
    },
    gradStyle() {
      return posterGradientStyle(this.displayTitle);
    },
    initial() {
      return posterInitial(this.displayTitle);
    },
    ratingDisplay() {
      const val = this.movie.avg_rating ?? this.movie.score ?? this.movie.rating;
      if (val == null || isNaN(val)) return null;
      return Number(val).toFixed(1);
    }
  },
  methods: {
    onCardClick() {
      this.$emit('click', this.movie);
    },
    onImgLoad(e) {
      e.target.classList.add('loaded');
    },
    onPosterError(e) {
      this.posterFailed = true;
      if (e.target) e.target.classList.add('loaded');
    },
    goToDetail() {
      window.location.href = '/movie/' + this.movie.id;
    },
    quickRate() {
      this.$emit('rate', { movie: this.movie, rating: 0 });
    }
  }
};

/* ---------- MovieRow ---------- */
const MovieRow = {
  props: {
    title: { type: String, required: true },
    movies: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    icon: { type: String, default: 'ph-film-strip' },
    emptyText: { type: String, default: '暂无电影' },
    emptySubtext: { type: String, default: '去评分一些电影来获取推荐吧' }
  },
  emits: ['movieClick', 'movieRate'],
  components: { MovieCard },
  template: `
    <section class="movie-row mb-5">
      <h2 class="row-title">
        <i :class="'ph ' + icon" style="color: var(--cinema-accent);"></i>
        {{ title }}
      </h2>
      <div v-if="loading" class="d-flex gap-3">
        <div v-for="n in 6" :key="n" class="loading-skeleton" style="width: 200px; height: 300px; flex-shrink: 0;"></div>
      </div>
      <div v-else-if="!movies || movies.length === 0" class="empty-state py-5">
        <div class="empty-icon">🎬</div>
        <h5>{{ emptyText }}</h5>
        <p>{{ emptySubtext }}</p>
      </div>
      <div v-else class="scroll-container" ref="scrollContainer">
        <movie-card v-for="movie in movies" :key="movie.id"
                    :movie="movie" show-rating
                    @click="$emit('movieClick', $event)"
                    @rate="$emit('movieRate', $event)">
        </movie-card>
      </div>
    </section>
  `,
  methods: {
    scrollLeft() {
      this.$refs.scrollContainer?.scrollBy({ left: -600, behavior: 'smooth' });
    },
    scrollRight() {
      this.$refs.scrollContainer?.scrollBy({ left: 600, behavior: 'smooth' });
    }
  }
};

/* ---------- CinemaToast ---------- */
const CinemaToast = {
  props: {
    message: String,
    type: { type: String, default: 'success' }
  },
  template: `
    <div class="toast-custom" :class="'toast-' + type"
         style="opacity:1; transform:none; display:inline-flex; gap:0.5rem; align-items:center;">
      <i :class="type === 'error' ? 'ph ph-warning-circle' : 'ph ph-check-circle'" style="font-size:1.25rem;"></i>
      <span>{{ message }}</span>
    </div>
  `
};

/* ---------- SearchBox ---------- */
const SearchBox = {
  props: {
    modelValue: { type: String, default: '' },
    placeholder: { type: String, default: '搜索电影...' },
    loading: { type: Boolean, default: false }
  },
  emits: ['search', 'focus', 'blur', 'update:modelValue'],
  template: `
    <div class="cinema-search">
      <i class="ph ph-magnifying-glass search-icon"></i>
      <input
        type="text"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        @keyup.enter="$emit('search')"
        @focus="$emit('focus')"
        @blur="$emit('blur')"
        :placeholder="placeholder"
      />
      <div v-if="loading" class="spinner-border spinner-border-sm text-accent position-absolute"
           style="right: 1rem; top: 50%; transform: translateY(-50%); color: var(--cinema-accent) !important;" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
  `
};

/* ---------- SkeletonGrid ---------- */
const SkeletonGrid = {
  props: { count: { type: Number, default: 6 }, columns: { type: Number, default: 6 } },
  template: `
    <div class="row g-3">
      <div v-for="n in count" :key="n" class="col-6 col-md-4 col-lg-3" :class="'col-xl-' + (12/columns)">
        <div class="loading-skeleton" style="aspect-ratio: 2/3;"></div>
      </div>
    </div>
  `
};

// Expose components globally
window.CinemaComponents = {
  StarRating,
  MovieCard,
  MovieRow,
  CinemaToast,
  SearchBox,
  SkeletonGrid
};
