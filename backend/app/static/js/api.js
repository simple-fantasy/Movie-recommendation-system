const _pendingRequests = new Map();

async function api(path, options = {}) {
  const method = options.method || 'GET';
  // Deduplicate concurrent GET requests to the same URL
  if (method === 'GET' && !options.skipDedup) {
    const key = path;
    const pending = _pendingRequests.get(key);
    if (pending) return pending;
  }

  const init = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    credentials: 'include',
    ...options,
  };

  if (options.body !== undefined && options.body !== null && typeof options.body !== 'string') {
    init.body = JSON.stringify(options.body);
  }

  let promise;
  try {
    if (method === 'GET' && !options.skipDedup) {
      const key = path;
      promise = (async () => {
        const res = await fetch(path, init);
        return _parseResponse(res);
      })();
      _pendingRequests.set(key, promise);
    } else {
      promise = (async () => {
        const res = await fetch(path, init);
        return _parseResponse(res);
      })();
    }

    const data = await promise;
    return data;
  } finally {
    if (method === 'GET' && !options.skipDedup) {
      _pendingRequests.delete(path);
    }
  }
}

async function _parseResponse(res) {
  const contentType = res.headers.get('content-type') || '';
  let data;
  let isJson = contentType.includes('application/json');
  if (isJson) {
    data = await res.json();
  } else {
    data = await res.text();
  }

  if (!res.ok) {
    let message;
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      // JSON 对象 → 提取 error/message
      message = data.error || data.message || '';
    } else if (typeof data === 'string') {
      if (data.startsWith('{') || data.startsWith('[')) {
        // JSON 字符串但 contentType 不对，尝试解析
        try {
          const parsed = JSON.parse(data);
          message = (parsed && parsed.error) || (parsed && parsed.message) || '';
        } catch (e) { /* ignore parse error */ }
      }
      if (!message) {
        // HTML 错误页面或其他文本
        if (data.indexOf('<!DOCTYPE') === 0 || data.indexOf('<html') === 0) {
          if (res.status === 401 || res.status === 302) {
            message = '请先登录';
          } else if (res.status === 403) {
            message = '没有权限执行此操作';
          } else if (res.status === 404) {
            message = '请求的资源不存在';
          } else if (res.status >= 500) {
            message = '服务器内部错误，请稍后重试';
          }
        }
        if (!message) {
          // 非 HTML 的短文本直接使用，长文本截断
          message = data.length < 100 ? data : ('服务器返回异常 (' + res.status + ')');
        }
      }
    }
    if (!message) {
      message = '服务器错误 (' + res.status + ')';
    }
    const error = new Error(message);
    error.response = res;
    error.data = data;
    throw error;
  }

  // res.ok 但非 JSON → 可能被重定向到了登录页
  if (!isJson && typeof data === 'string') {
    if (data.indexOf('<!DOCTYPE') === 0 || data.indexOf('<html') === 0) {
      const error = new Error('请先登录');
      error.response = res;
      error.data = data;
      throw error;
    }
  }

  return data;
}
