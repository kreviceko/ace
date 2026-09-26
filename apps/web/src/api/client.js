const BASE = import.meta.env.VITE_API_BASE || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  const contentType = res.headers.get('content-type') || ''
  const body = contentType.includes('application/json') ? await res.json() : await res.text()
  if (!res.ok) {
    const message = typeof body === 'object' ? body.detail || body.error || JSON.stringify(body) : body
    throw new Error(message || `HTTP ${res.status}`)
  }
  return body
}

export const api = {
  health: () => request('/api/health'),
  library: () => request('/api/library'),
  getSong: (id) => request(`/api/library/${id}`),
  formatLyrics: (payload) =>
    request('/api/lyrics/format', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  create: async (payload, files = {}) => {
    const form = new FormData()
    form.append('payload', JSON.stringify(payload))
    if (files.src_audio) form.append('src_audio', files.src_audio)
    if (files.reference_audio) form.append('reference_audio', files.reference_audio)
    return request('/api/create', { method: 'POST', body: form })
  },
  job: (id) => request(`/api/jobs/${id}`),
  audioUrl: (id) => `${BASE}/api/library/${id}/audio`,
}
