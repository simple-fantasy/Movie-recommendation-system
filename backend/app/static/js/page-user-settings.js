Vue.createApp({
    data: function () {
        return {
            activeTab: 'security',
            toast: { visible: false, type: 'success', message: '' },
            sqQuestion: '',
            sqCustomQuestion: '',
            sqAnswer: '',
            sqSaving: false,
            cpCurrent: '',
            cpNew: '',
            cpConfirm: '',
            cpSaving: false
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
        onQuestionChange: function () {
            if (this.sqQuestion !== '__custom__') {
                this.sqCustomQuestion = '';
            }
        },
        saveSecurityQuestion: function () {
            var self = this;
            var question = self.sqQuestion === '__custom__' ? self.sqCustomQuestion.trim() : self.sqQuestion.trim();
            var answer = self.sqAnswer.trim();

            if (!question) {
                self.showToast('请选择或输入密保问题', 'error');
                return;
            }
            if (!answer) {
                self.showToast('请输入答案', 'error');
                return;
            }
            if (answer.length < 2) {
                self.showToast('答案至少需要2个字符', 'error');
                return;
            }

            self.sqSaving = true;
            api('/api/user/security-question', {
                method: 'POST',
                body: JSON.stringify({ question: question, answer: answer })
            }).then(function (res) {
                if (res.success) {
                    self.showToast('密保问题设置成功', 'success');
                } else {
                    self.showToast(res.error || '设置失败', 'error');
                }
            }).catch(function (err) {
                self.showToast(err.message || '请求失败', 'error');
            }).finally(function () {
                self.sqSaving = false;
            });
        },
        changePassword: function () {
            var self = this;
            if (!self.cpCurrent) {
                self.showToast('请输入当前密码', 'error');
                return;
            }
            if (!self.cpNew) {
                self.showToast('请输入新密码', 'error');
                return;
            }
            if (self.cpNew.length < 6) {
                self.showToast('新密码至少需要6个字符', 'error');
                return;
            }
            if (self.cpNew !== self.cpConfirm) {
                self.showToast('两次输入的密码不一致', 'error');
                return;
            }

            self.cpSaving = true;
            api('/api/user/change-password', {
                method: 'POST',
                body: JSON.stringify({
                    current_password: self.cpCurrent,
                    new_password: self.cpNew
                })
            }).then(function (res) {
                if (res.success) {
                    self.showToast('密码修改成功', 'success');
                    self.cpCurrent = '';
                    self.cpNew = '';
                    self.cpConfirm = '';
                } else {
                    self.showToast(res.error || '修改失败', 'error');
                }
            }).catch(function (err) {
                self.showToast(err.message || '请求失败', 'error');
            }).finally(function () {
                self.cpSaving = false;
            });
        }
    }
}).mount('#settingsApp');
