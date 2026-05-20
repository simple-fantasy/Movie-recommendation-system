document.addEventListener('DOMContentLoaded', function () {
    var step1 = document.getElementById('step1');
    var step2 = document.getElementById('step2');
    var successBox = document.getElementById('successBox');
    var msg = document.getElementById('message');
    var stepLabel = document.getElementById('stepLabel');
    var dot1 = document.getElementById('dot1');
    var dot2 = document.getElementById('dot2');

    var usernameInput = document.getElementById('usernameInput');
    var questionDisplay = document.getElementById('questionDisplay');
    var answerInput = document.getElementById('answerInput');
    var newPasswordInput = document.getElementById('newPasswordInput');
    var confirmPasswordInput = document.getElementById('confirmPasswordInput');
    var btnCheck = document.getElementById('btnCheck');
    var btnReset = document.getElementById('btnReset');
    var btnBack = document.getElementById('btnBack');

    var currentUsername = '';

    function showMsg(text, type) {
        msg.textContent = text;
        msg.className = 'message ' + type;
    }

    function hideMsg() {
        msg.className = 'message';
    }

    function showStep1() {
        step1.style.display = '';
        step2.style.display = 'none';
        successBox.style.display = 'none';
        stepLabel.textContent = '第一步：输入用户名';
        dot1.className = 'step-dot active';
        dot2.className = 'step-dot';
        hideMsg();
    }

    function showStep2() {
        step1.style.display = 'none';
        step2.style.display = '';
        successBox.style.display = 'none';
        stepLabel.textContent = '第二步：验证身份并重置密码';
        dot1.className = 'step-dot done';
        dot2.className = 'step-dot active';
        hideMsg();
    }

    function showSuccess() {
        step1.style.display = 'none';
        step2.style.display = 'none';
        successBox.style.display = '';
        dot1.className = 'step-dot done';
        dot2.className = 'step-dot done';
        stepLabel.textContent = '';
        hideMsg();

        var seconds = 3;
        var cd = document.getElementById('countdown');
        var timer = setInterval(function () {
            seconds--;
            cd.textContent = seconds;
            if (seconds <= 0) {
                clearInterval(timer);
                window.location.href = '/login';
            }
        }, 1000);
    }

    // Step 1: Check username
    btnCheck.addEventListener('click', function () {
        var username = usernameInput.value.trim();
        if (!username) {
            showMsg('请输入用户名', 'error');
            return;
        }
        hideMsg();
        btnCheck.disabled = true;
        btnCheck.textContent = '查询中...';

        api('/api/auth/forgot-password/check', {
            method: 'POST',
            body: JSON.stringify({ username: username })
        }).then(function (res) {
            if (res.question) {
                currentUsername = res.username;
                questionDisplay.textContent = '密保问题：' + res.question;
                showStep2();
            } else {
                showMsg(res.error || '无法处理该请求', 'error');
            }
        }).catch(function (err) {
            showMsg(err.message || '请求失败，请重试', 'error');
        }).finally(function () {
            btnCheck.disabled = false;
            btnCheck.textContent = '下一步';
        });
    });

    // Enter key for step 1
    usernameInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') btnCheck.click();
    });

    // Step 2: Reset password
    btnReset.addEventListener('click', function () {
        var answer = answerInput.value.trim();
        var newPw = newPasswordInput.value;
        var confirmPw = confirmPasswordInput.value;

        if (!answer) {
            showMsg('请输入密保答案', 'error');
            return;
        }
        if (!newPw) {
            showMsg('请输入新密码', 'error');
            return;
        }
        if (newPw.length < 6) {
            showMsg('新密码至少需要6个字符', 'error');
            return;
        }
        if (newPw !== confirmPw) {
            showMsg('两次输入的密码不一致', 'error');
            return;
        }

        hideMsg();
        btnReset.disabled = true;
        btnReset.textContent = '重置中...';

        api('/api/auth/forgot-password/reset', {
            method: 'POST',
            body: JSON.stringify({
                username: currentUsername,
                answer: answer,
                new_password: newPw
            })
        }).then(function (res) {
            if (res.success) {
                showSuccess();
            } else {
                showMsg(res.error || '重置失败', 'error');
            }
        }).catch(function (err) {
            showMsg(err.message || '请求失败，请重试', 'error');
        }).finally(function () {
            btnReset.disabled = false;
            btnReset.textContent = '重置密码';
        });
    });

    // Back to step 1
    btnBack.addEventListener('click', function () {
        showStep1();
    });
});
