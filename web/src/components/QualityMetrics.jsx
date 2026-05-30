import { IconBarChart, IconCheckCircle, IconAlertTriangle, IconClock } from './Icons'

/**
 * QualityMetrics — Kartu metrik audio_quality dari analysis report.
 */
export default function QualityMetrics({ quality, duration }) {
  if (!quality) return null

  const silencePct = (quality.silence_ratio * 100).toFixed(1)
  const silenceStatus = quality.silence_ratio > 0.3 ? 'danger' : quality.silence_ratio > 0.1 ? 'warn' : 'ok'

  const volDb = typeof quality.avg_volume_db === 'number' ? quality.avg_volume_db.toFixed(1) : '—'
  const volStatus = quality.avg_volume_db < -35 ? 'danger' : quality.avg_volume_db < -25 ? 'warn' : 'ok'

  const clipStatus = quality.clipping_detected ? 'danger' : 'ok'

  const formatDuration = (s) => {
    if (!s) return '—'
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`
  }

  const StatusIcon = ({ status }) => {
    if (status === 'ok') return <IconCheckCircle size={14} style={{ color: 'var(--success)' }} />
    return <IconAlertTriangle size={14} style={{ color: status === 'warn' ? 'var(--warning)' : 'var(--danger)' }} />
  }

  return (
    <div className="fade-in">
      <div className="section-title">
        <IconBarChart size={18} /> Metrik Kualitas Audio
      </div>
      <div className="metrics-grid" id="quality-metrics">

        <div className={`metric-card ${silenceStatus}`}>
          <div className="metric-label">Silence Ratio</div>
          <div className="metric-value">{silencePct}%</div>
          <div className="metric-sub">
            <StatusIcon status={silenceStatus} />
            {silenceStatus === 'ok' ? 'Normal' : silenceStatus === 'warn' ? 'Agak tinggi' : 'Sangat tinggi'}
          </div>
        </div>

        <div className={`metric-card ${volStatus}`}>
          <div className="metric-label">Volume Rata-rata</div>
          <div className="metric-value">{volDb} <span style={{ fontSize: '1rem', fontWeight: 600 }}>dB</span></div>
          <div className="metric-sub">
            <StatusIcon status={volStatus} />
            {volStatus === 'ok' ? 'Baik' : volStatus === 'warn' ? 'Agak rendah' : 'Sangat rendah'}
          </div>
        </div>

        <div className={`metric-card ${clipStatus}`}>
          <div className="metric-label">Clipping</div>
          <div className="metric-value">{quality.clipping_detected ? 'Ya' : 'Tidak'}</div>
          <div className="metric-sub">
            <StatusIcon status={clipStatus} />
            {quality.clipping_detected ? 'Distorsi terdeteksi' : 'Bersih'}
          </div>
        </div>

      </div>

      {duration != null && (
        <div style={{ textAlign: 'center', marginTop: 4 }}>
          <span className="badge badge-blue" style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
            <IconClock size={13} /> Durasi: {formatDuration(duration)}
          </span>
        </div>
      )}
    </div>
  )
}
