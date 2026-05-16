import axios from 'axios'

// Point to your backend. In dev = localhost. In prod = Railway URL.
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

// ── Video API ─────────────────────────────────────────────────────────

export const uploadVideo = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/api/video/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
    },
  })
}

export const getJobStatus = (jobId) =>
  api.get(`/api/video/status/${jobId}`)

export const listJobs = () =>
  api.get('/api/video/jobs')

// ── Analysis API ──────────────────────────────────────────────────────

export const getResults = (jobId) =>
  api.get(`/api/analysis/results/${jobId}`)

export const getAnomalies = (jobId) =>
  api.get(`/api/analysis/anomalies/${jobId}`)

export const getFrameData = (jobId, limit = 300) =>
  api.get(`/api/analysis/frames/${jobId}?limit=${limit}`)

export { BASE_URL }