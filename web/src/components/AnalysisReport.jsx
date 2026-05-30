import QualityMetrics from './QualityMetrics'
import IssuesList from './IssuesList'
import { IconClipboard, IconDownload, IconRotateCcw, IconBot } from './Icons'

/**
 * AnalysisReport — Tampilan lengkap hasil analisis audio.
 */
export default function AnalysisReport({ report, onReset }) {
  if (!report) return null

  const insights = report.llm_insights || {}
  const actions = insights.recommended_actions || []

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.original_filename || report.file_name || 'report'}_analysis.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fade-in" id="analysis-report">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            <IconClipboard size={22} /> Laporan Analisis
          </h2>
          <div className="text-sm" style={{ marginTop: 6, color: 'var(--text-secondary)', fontWeight: 500 }}>
            {report.original_filename || report.file_name}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={handleDownload} title="Download JSON">
            <IconDownload size={16} /> JSON
          </button>
          <button className="btn btn-ghost" onClick={onReset}>
            <IconRotateCcw size={16} /> Analisis Lain
          </button>
        </div>
      </div>

      {/* Quality Metrics */}
      <QualityMetrics quality={report.audio_quality} duration={report.duration_seconds} />

      <div className="divider" />

      {/* Issues */}
      <IssuesList issues={report.issues} />

      <div className="divider" />

      {/* LLM Insights */}
      {insights.summary && (
        <div className="insights-panel fade-in" id="llm-insights">
          <div className="section-title" style={{ color: 'var(--accent)', marginBottom: 16 }}>
            <IconBot size={18} /> AI Insights
          </div>
          <div className="insights-summary">{insights.summary}</div>

          {actions.length > 0 && (
            <>
              <div className="section-title" style={{ marginTop: 20, marginBottom: 12, fontSize: '0.78rem' }}>
                Rekomendasi Tindakan
              </div>
              <div className="insights-actions">
                {actions.map((action, i) => (
                  <div className="action-item" key={i}>
                    <span className="action-num">{i + 1}</span>
                    <span style={{ fontWeight: 500 }}>{action}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
