document.addEventListener('DOMContentLoaded', () => {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const formTitle = document.querySelector('.form-title');
  const messageEl = document.getElementById('message');
  let isSubmitting = false;
  const SUBMIT_DELAY = 1000;

  function showMessage(text, type) {
    if (!messageEl) return;
    messageEl.innerHTML = text;
    messageEl.className = `message ${type} show`;
  }

  function hideMessage() {
    if (!messageEl) return;
    messageEl.classList.remove('show');
  }

  function getFriendlyErrorMessage(status, data) {
    const code = data && data.code;
    const msg = data && data.error;

    if (code === 'MODEL_LOADING') return '🔄 NCF模型正在加载中，请5秒后再试';
    if (code === 'MODEL_NOT_AVAILABLE') return '⚠️ 推荐模型未就绪，请联系管理员';
    if (code === 'UNAUTHORIZED') return '🔒 请先登录';
    if (code === 'NOT_FOUND') return '❓ 请求的资源不存在';
    if (code === 'BAD_REQUEST') return '⚠️ 请求参数错误';
    if (code === 'INVALID_PARAM') return '⚠️ ' + (msg || '参数格式不正确');
    if (status === 401) return '🔒 用户名或密码错误';
    if (status === 409) return '⚠️ 用户名已存在';
    if (status === 429) return '⏳ 请求太频繁，请稍后再试';
    if (status === 503) return msg || '🔧 服务暂时不可用';
    if (status >= 500) return '🔧 服务器繁忙，请稍后重试';

    return msg || `请求失败 (${status})`;
  }

  function toggleTab(tab) {
    tabBtns.forEach((btn) => btn.classList.toggle('active', btn.dataset.tab === tab));
    if (loginForm && registerForm) {
      loginForm.style.display = tab === 'login' ? 'block' : 'none';
      registerForm.style.display = tab === 'register' ? 'block' : 'none';
    }
    if (formTitle) {
      formTitle.textContent = tab === 'login' ? '欢迎回来' : '创建账户';
    }
    hideMessage();
  }

  function setupTabs() {
    tabBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        if (tab) toggleTab(tab);
      });
    });
  }

  function setupPasswordToggle() {
    document.querySelectorAll('.password-toggle').forEach((btn) => {
      btn.addEventListener('click', () => {
        const targetId = btn.dataset.target;
        const input = document.getElementById(targetId);
        if (!input) return;
        if (input.type === 'password') {
          input.type = 'text';
          btn.textContent = '🙈';
        } else {
          input.type = 'password';
          btn.textContent = '👁️';
        }
      });
    });
  }

  async function withSubmitLock(form, submitFn) {
    if (isSubmitting) return;
    isSubmitting = true;

    const btn = form.querySelector('.btn-submit');
    if (btn) {
      btn.classList.add('loading');
      btn.disabled = true;
    }

    try {
      await submitFn();
    } finally {
      setTimeout(() => {
        if (btn) {
          btn.classList.remove('loading');
          btn.disabled = false;
        }
        isSubmitting = false;
      }, SUBMIT_DELAY);
    }
  }

  async function handleLogin(event) {
    event.preventDefault();
    if (!loginForm) return;

    await withSubmitLock(loginForm, async () => {
      const username = document.getElementById('loginUsername').value.trim();
      const password = document.getElementById('loginPassword').value;

      if (!username) {
        showMessage('⚠️ 请输入用户名', 'error');
        throw new Error('请输入用户名');
      }
      if (!password) {
        showMessage('⚠️ 请输入密码', 'error');
        throw new Error('请输入密码');
      }

      try {
        const data = await api('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({ username, password }),
        });
        showMessage(`🎉 登录成功！欢迎 ${data.username}`, 'success');
        setTimeout(() => {
          window.location.href = '/app';
        }, 1000);
      } catch (err) {
        const message = err.message || '登录失败，请稍后重试';
        showMessage(message, 'error');
        throw err;
      }
    });
  }

  async function handleRegister(event) {
    event.preventDefault();
    if (!registerForm) return;

    await withSubmitLock(registerForm, async () => {
      const username = document.getElementById('registerUsername').value.trim();
      const password = document.getElementById('registerPassword').value;

      if (!username || username.length < 2) {
        showMessage('⚠️ 用户名至少需要2个字符', 'error');
        throw new Error('用户名太短');
      }
      if (!password || password.length < 6) {
        showMessage('⚠️ 密码至少需要6个字符', 'error');
        throw new Error('密码太短');
      }

      try {
        const data = await api('/api/auth/register', {
          method: 'POST',
          body: JSON.stringify({ username, password }),
        });
        showMessage(`🎉 注册成功！欢迎 ${data.username}，请登录`, 'success');
        setTimeout(() => {
          toggleTab('login');
          const loginUsername = document.getElementById('loginUsername');
          if (loginUsername) loginUsername.value = username;
        }, 1000);
      } catch (err) {
        const message = err.message || '注册失败，请稍后重试';
        showMessage(message, 'error');
        throw err;
      }
    });
  }

  async function checkAuth() {
    try {
      const data = await api('/api/me');
      if (data.authenticated) {
        window.location.href = '/app';
      }
    } catch (e) {
      // 未登录，继续显示登录页
    }
  }

  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
  if (registerForm) {
    registerForm.addEventListener('submit', handleRegister);
  }

  setupTabs();
  setupPasswordToggle();
  checkAuth();
});