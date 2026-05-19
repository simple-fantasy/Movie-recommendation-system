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
  if (contentType.includes('application/json')) {
    data = await res.json();
  } else {
    data = await res.text();
  }
  if (!res.ok) {
    const message = data && data.error ? data.error : (typeof data === 'string' ? data : JSON.stringify(data));
    const error = new Error(message || `${res.status} ${res.statusText}`);
    error.response = res;
    error.data = data;
    throw error;
  }
  return data;
}
