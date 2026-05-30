import { IconLoader, IconCheckCircle, IconAlertTriangle } from './Icons'

/**
 * ProgressBar — Menampilkan status upload dan processing.
 */
export default function ProgressBar({ phase, percent = 0, message }) {
  if (phase === 'idle') return null

  const labels = {
    uploading: 'Mengunggah file…',
    processing: 'Menganalisis audio…',
    done: 'Selesai!',
    error: 'Terjadi kesalahan',
  }

  const displayPercent = phase === 'uploading' ? percent : 100

  return (
    <div className="progress-wrap fade-in" id="progress-bar">
      <div className="progress-label">
        <span style={{ fontWeight: 600 }}>{message || labels[phase] || phase}</span>
        {phase === 'uploading' && <span style={{ fontWeight: 700 }}>{percent}%</span>}
        {phase === 'processing' && <IconLoader size={16} />}
        {phase === 'done' && <IconCheckCircle size={16} style={{ color: 'var(--success)' }} />}
        {phase === 'error' && <IconAlertTriangle size={16} style={{ color: 'var(--danger)' }} />}
      </div>
      <div className="progress-track">
        <div
          className="progress-bar"
          style={{
            width: `${displayPercent}%`,
            background: phase === 'error'
              ? 'var(--danger)'
              : phase === 'done'
                ? 'var(--success)'
                : undefined,
          }}
        />
      </div>
    </div>
  )
}
