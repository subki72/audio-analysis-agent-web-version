import { useState, useEffect, useCallback } from 'react'
import { checkHealth, analyzeAudio, transcribeAudio } from './api/voicescript'
import { IconMicrophone, IconWaveform, IconFileText, IconZap } from './components/Icons'
import UploadZone from './components/UploadZone'
import ProgressBar from './components/ProgressBar'
import AnalysisReport from './components/AnalysisReport'
import TranscriptView from './components/TranscriptView'
import './index.css'

function App() {
  // ── State ──────────────────────────────────────────
  const [mode, setMode] = useState('analyze')
  const [file, setFile] = useState(null)
  const [phase, setPhase] = useState('idle')
  const [uploadPct, setUploadPct] = useState(0)
  const [errorMsg, setErrorMsg] = useState('')
  const [report, setReport] = useState(null)
  const [transcript, setTranscript] = useState(null)
  const [apiOnline, setApiOnline] = useState(null)

  // Transcription options
  const [language, setLanguage] = useState('id')
  const [outputFormat, setOutputFormat] = useState('txt')

  // ── Health Check ────────────────────────────────────
  useEffect(() => {
    let cancelled = false
    const check = () => {
      checkHealth()
        .then(() => { if (!cancelled) setApiOnline(true) })
        .catch(() => { if (!cancelled) setApiOnline(false) })
    }
    check()
    const id = setInterval(check, 30_000)
    return () => { cancelled = true; clearInterval(id) }
  }, [])

  // ── Reset ───────────────────────────────────────────
  const reset = useCallback(() => {
    setFile(null)
    setPhase('idle')
    setUploadPct(0)
    setErrorMsg('')
    setReport(null)
    setTranscript(null)
  }, [])

  // ── Submit ──────────────────────────────────────────
  const handleSubmit = useCallback(async () => {
    if (!file) return
    setPhase('uploading')
    setUploadPct(0)
    setErrorMsg('')

    try {
      if (mode === 'analyze') {
        const data = await analyzeAudio(file, (pct) => {
          setUploadPct(pct)
          if (pct >= 100) setPhase('processing')
        })
        setReport(data)
        setPhase('done')
      } else {
        const data = await transcribeAudio(
          file,
          { language, output_format: outputFormat },
          (pct) => {
            setUploadPct(pct)
            if (pct >= 100) setPhase('processing')
          }
        )
        setTranscript(data)
        setPhase('done')
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Terjadi kesalahan tidak dikenal'
      setErrorMsg(msg)
      setPhase('error')
    }
  }, [file, mode, language, outputFormat])

  // ── Derived ─────────────────────────────────────────
  const isProcessing = phase === 'uploading' || phase === 'processing'
  const showResult = phase === 'done'

  return (
    <div className="app-shell">
      {/* ── Navbar ──────────────────────────────────── */}
      <nav className="navbar" id="navbar">
        <div className="container navbar-inner">
          <a href="/" className="navbar-brand" onClick={(e) => { e.preventDefault(); reset() }}>
            <span className="brand-icon"><IconMicrophone size={18} /></span>
            <span style={{ fontWeight: 800 }}>Vocalis</span>
          </a>
          <div className="navbar-status" id="api-status">
            <span className={`status-dot ${apiOnline === true ? 'online' : apiOnline === false ? 'offline' : ''}`} />
            <span style={{ fontWeight: 600 }}>
              {apiOnline === true ? 'API Online' : apiOnline === false ? 'API Offline' : 'Menghubungi…'}
            </span>
          </div>
        </div>
      </nav>

      {/* ── Main Content ───────────────────────────── */}
      <main className="container" style={{ flex: 1, paddingTop: 48, paddingBottom: 60 }}>

        {/* Hero — only when idle */}
        {!showResult && (
          <div className="fade-in" style={{ textAlign: 'center', marginBottom: 40 }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 12 }}>
              Audio Analysis & Transcription
            </h1>
            <p style={{ color: 'var(--text-secondary)', maxWidth: 600, margin: '0 auto', fontSize: '1.05rem', fontWeight: 400, lineHeight: 1.7 }}>
              Upload file audio untuk analisis kualitas menggunakan AI, atau transkripsi otomatis dengan Groq Whisper.
            </p>
          </div>
        )}

        {/* Mode Tabs — only when not showing result */}
        {!showResult && (
          <div className="tabs fade-in" style={{ maxWidth: 420, margin: '0 auto 32px' }} id="mode-tabs">
            <button
              className={`tab ${mode === 'analyze' ? 'active' : ''}`}
              onClick={() => { setMode('analyze'); reset() }}
              disabled={isProcessing}
              style={{ fontWeight: mode === 'analyze' ? 700 : 500, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
            >
              <IconWaveform size={16} /> Analisis
            </button>
            <button
              className={`tab ${mode === 'transcribe' ? 'active' : ''}`}
              onClick={() => { setMode('transcribe'); reset() }}
              disabled={isProcessing}
              style={{ fontWeight: mode === 'transcribe' ? 700 : 500, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
            >
              <IconFileText size={16} /> Transkripsi
            </button>
          </div>
        )}

        {/* Upload Form */}
        {!showResult && (
          <div className="card fade-in" id="upload-card">

            <UploadZone file={file} onFileSelect={setFile} disabled={isProcessing} />

            {/* Transcription Options */}
            {mode === 'transcribe' && file && !isProcessing && (
              <div className="fade-in" style={{ marginTop: 24, display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 180 }}>
                  <label className="text-sm" htmlFor="lang-select" style={{ display: 'block', marginBottom: 8, fontWeight: 700, color: 'var(--text-secondary)' }}>
                    Bahasa
                  </label>
                  <select
                    id="lang-select"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    style={{
                      width: '100%', padding: '10px 14px',
                      background: 'var(--bg-surface)', color: 'var(--text-primary)',
                      border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                      fontFamily: 'inherit', fontSize: '0.9rem', fontWeight: 500,
                    }}
                  >
                    <option value="id">Indonesia</option>
                    <option value="en">English</option>
                    <option value="ja">Japanese</option>
                    <option value="ko">Korean</option>
                    <option value="zh">Chinese</option>
                    <option value="ar">Arabic</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                  </select>
                </div>
                <div style={{ flex: 1, minWidth: 180 }}>
                  <label className="text-sm" htmlFor="format-select" style={{ display: 'block', marginBottom: 8, fontWeight: 700, color: 'var(--text-secondary)' }}>
                    Format Output
                  </label>
                  <select
                    id="format-select"
                    value={outputFormat}
                    onChange={(e) => setOutputFormat(e.target.value)}
                    style={{
                      width: '100%', padding: '10px 14px',
                      background: 'var(--bg-surface)', color: 'var(--text-primary)',
                      border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                      fontFamily: 'inherit', fontSize: '0.9rem', fontWeight: 500,
                    }}
                  >
                    <option value="txt">TXT — Plain text</option>
                    <option value="srt">SRT — Subtitle</option>
                    <option value="vtt">VTT — WebVTT</option>
                    <option value="json">JSON — Verbose</option>
                  </select>
                </div>
              </div>
            )}

            {/* Progress Bar */}
            <ProgressBar phase={phase} percent={uploadPct} message={phase === 'error' ? errorMsg : undefined} />

            {/* Submit / Reset Buttons */}
            {phase !== 'error' && !isProcessing && (
              <div style={{ marginTop: 24, textAlign: 'center' }}>
                <button
                  className="btn btn-primary"
                  id="submit-btn"
                  onClick={handleSubmit}
                  disabled={!file || apiOnline !== true}
                  style={{ minWidth: 240, padding: '12px 28px', fontSize: '0.95rem', fontWeight: 700 }}
                >
                  <IconZap size={18} />
                  {mode === 'analyze' ? 'Mulai Analisis' : 'Mulai Transkripsi'}
                </button>
              </div>
            )}

            {phase === 'error' && (
              <div style={{ marginTop: 20, textAlign: 'center' }}>
                <button className="btn btn-ghost" onClick={reset} style={{ fontWeight: 600 }}>
                  Coba Lagi
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── Results ──────────────────────────────── */}
        {showResult && mode === 'analyze' && report && (
          <div className="card">
            <AnalysisReport report={report} onReset={reset} />
          </div>
        )}

        {showResult && mode === 'transcribe' && transcript && (
          <div className="card">
            <TranscriptView result={transcript} onReset={reset} />
          </div>
        )}
      </main>

      {/* ── Footer ─────────────────────────────────── */}
      <footer style={{ textAlign: 'center', padding: '24px 0', borderTop: '1px solid var(--border)' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 500 }}>
          Vocalis v1.0 · Powered by Groq & FFmpeg
        </span>
      </footer>
    </div>
  )
}

export default App
