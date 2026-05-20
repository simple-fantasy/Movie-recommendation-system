Vue.createApp({
    data: function () {
        return {
            activeTab: 'upload',
            toast: { visible: false, type: 'success', message: '' },
            form: {
                title: '',
                year: null,
                director: '',
                genres: '',
                actors: '',
                description: '',
                runtime: null,
                tagline: '',
                language: '',
                country: '',
                poster_url: '',
                backdrop_url: '',
                trailer_url: ''
            },
            submitting: false,
            submissions: [],
            subPage: 1,
            subPages: 1,
            subTotal: 0,
            subLoading: false
        };
    },
    methods: {
        showToast: function (message, type) {
            var self = this;
            self.toast.message = message;
            self.toast.type = type || 'success';
            self.toast.visible = true;
            setTimeout(function () { self.toast.visible = false; }, 4000);
        },
        resetForm: function () {
            this.form = {
                title: '', year: null, director: '', genres: '', actors: '',
                description: '', runtime: null, tagline: '', language: '',
                country: '', poster_url: '', backdrop_url: '', trailer_url: ''
            };
        },
        submitMovie: function () {
            var self = this;
            if (!self.form.title.trim()) {
                self.showToast('电影名称不能为空', 'error');
                return;
            }

            var body = {
                title: self.form.title.trim()
            };
            if (self.form.year) body.year = parseInt(self.form.year);
            if (self.form.director.trim()) body.director = self.form.director.trim();
            if (self.form.genres.trim()) body.genres = self.form.genres.trim();
            if (self.form.actors.trim()) body.actors = self.form.actors.trim();
            if (self.form.description.trim()) body.description = self.form.description.trim();
            if (self.form.runtime) body.runtime = parseInt(self.form.runtime);
            if (self.form.tagline.trim()) body.tagline = self.form.tagline.trim();
            if (self.form.language.trim()) body.language = self.form.language.trim();
            if (self.form.country.trim()) body.country = self.form.country.trim();
            if (self.form.poster_url.trim()) body.poster_url = self.form.poster_url.trim();
            if (self.form.backdrop_url.trim()) body.backdrop_url = self.form.backdrop_url.trim();
            if (self.form.trailer_url.trim()) body.trailer_url = self.form.trailer_url.trim();

            self.submitting = true;
            api('/api/movies/submit', {
                method: 'POST',
                body: JSON.stringify(body)
            }).then(function (res) {
                if (res.success) {
                    self.showToast(res.message, 'success');
                    self.resetForm();
                } else {
                    self.showToast(res.error || '提交失败', 'error');
                }
            }).catch(function (err) {
                self.showToast(err.message || '请求失败，请重试', 'error');
            }).finally(function () {
                self.submitting = false;
            });
        },
        loadSubmissions: function (page) {
            var self = this;
            page = page || 1;
            self.subLoading = true;
            api('/api/my/submitted-movies?page=' + page).then(function (res) {
                self.submissions = res.movies || [];
                self.subPage = page;
                self.subPages = res.pages || 1;
                self.subTotal = res.total || 0;
            }).catch(function (err) {
                self.showToast(err.message || '加载失败', 'error');
            }).finally(function () {
                self.subLoading = false;
            });
        }
    }
}).mount('#uploadApp');
