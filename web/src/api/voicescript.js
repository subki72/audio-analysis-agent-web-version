import axios from 'axios'

// Development: Vite proxy (/api → localhost:8000)
// Production : VITE_API_URL mengarah ke backend Render (https://xxx.onrender.com/api)
const BASE = import.meta.env.VITE_API_URL || '/api'

const API = axios.create({ baseURL: BASE })

/**
 * Cek status API backend.
 * @returns {{ status, llm_model, transcription_model, supported_formats }}
 */
export const checkHealth = () => API.get('/health').then(r => r.data)

/**
 * Upload dan analisis kualitas audio.
 * @param {File} file
 * @param {(pct: number) => void} onProgress
 * @returns Promise<AnalysisReport>
 */
export const analyzeAudio = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return API.post('/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => {
      if (onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  }).then(r => r.data)
}

/**
 * Upload dan transkripsi file audio.
 * @param {File} file
 * @param {{ language: string, output_format: string }} opts
 * @param {(pct: number) => void} onProgress
 * @returns Promise<TranscriptResult>
 */
export const transcribeAudio = (file, opts = {}, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  form.append('language', opts.language || 'id')
  form.append('output_format', opts.output_format || 'txt')
  return API.post('/transcribe', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => {
      if (onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  }).then(r => r.data)
}
