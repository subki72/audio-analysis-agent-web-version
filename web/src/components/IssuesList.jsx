import { IconSearch, IconCheckCircle, IconAlertTriangle } from './Icons'

/**
 * IssuesList — Daftar masalah yang terdeteksi dari analysis report.
 */
export default function IssuesList({ issues }) {
  if (!issues) return null

  return (
    <div className="fade-in">
      <div className="section-title">
        <IconSearch size={18} /> Masalah Terdeteksi
      </div>

      {issues.length === 0 ? (
        <div className="no-issues" id="no-issues">
          <IconCheckCircle size={18} />
          <span style={{ fontWeight: 600 }}>Tidak ada masalah signifikan yang terdeteksi. Audio berkualitas baik!</span>
        </div>
      ) : (
        <div className="issues-list" id="issues-list">
          {issues.map((issue, i) => (
            <div className="issue-item" key={i}>
              <span className="issue-icon"><IconAlertTriangle size={16} /></span>
              <span style={{ fontWeight: 500 }}>{issue}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
