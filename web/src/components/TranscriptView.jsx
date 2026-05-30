import { useState } from 'react'
import { IconFileText, IconCopy, IconCheckCircle, IconDownload, IconRotateCcw } from './Icons'

/**
 * TranscriptView — Tampilan hasil transkripsi audio.
 */
export default function TranscriptView({ result, onReset }) {
  const [copied, setCopied] = useState(false)

  if (!result) return null

  const text = typeof result.transcript === 'string'
    ? result.transcript
    : JSON.stringify(result.transcript, null, 2)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDownload = () => {
    const ext = result.output_format || 'txt'
    const mime = ext === 'json' ? 'application/json' : 'text/plain'
    const blob = new Blob([text], { type: mime })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${result.original_filename || 'transcript'}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fade-in" id="transcript-view">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            <IconFileText size={22} /> Hasil Transkripsi
          </h2>
          <div className="text-sm" style={{ marginTop: 6, color: 'var(--text-secondary)', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 8 }}>
            {result.original_filename}
            <span className="badge badge-blue">{result.language?.toUpperCase()}</span>
            <span className="badge badge-green">{result.output_format?.toUpperCase()}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={handleCopy}>
            {copied ? <><IconCheckCircle size={16} /> Disalin!</> : <><IconCopy size={16} /> Salin</>}
          </button>
          <button className="btn btn-ghost" onClick={handleDownload}>
            <IconDownload size={16} /> Download
          </button>
          <button className="btn btn-ghost" onClick={onReset}>
            <IconRotateCcw size={16} /> Transkripsi Lain
          </button>
        </div>
      </div>

      {/* Transcript Content */}
      <div className="transcript-box" id="transcript-content">
        {text || '(Tidak ada teks yang dihasilkan)'}
      </div>
    </div>
  )
}
