async function api(path, options = {}) {
  const init = {
    method: options.method || 'GET',
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

  const res = await fetch(path, init);
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
