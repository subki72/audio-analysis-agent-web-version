import { useState, useRef, useCallback } from 'react'
import { IconUploadCloud, IconMusic, IconX } from './Icons'

const SUPPORTED = ['.mp3', '.wav', '.m4a', '.webm', '.ogg', '.flac', '.aac', '.wma']

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function UploadZone({ file, onFileSelect, disabled }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  const handleFile = useCallback((f) => {
    if (!f) return
    const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase()
    if (!SUPPORTED.includes(ext)) {
      alert(`Format "${ext}" tidak didukung.\nFormat yang diterima: ${SUPPORTED.join(', ')}`)
      return
    }
    onFileSelect(f)
  }, [onFileSelect])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer?.files?.[0]
    handleFile(f)
  }, [handleFile])

  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  const onClick = () => { if (!disabled) inputRef.current?.click() }

  const onInputChange = (e) => {
    handleFile(e.target.files?.[0])
    e.target.value = ''
  }

  return (
    <div className="fade-in">
      <div
        id="upload-zone"
        className={`upload-zone${dragging ? ' dragging' : ''}${disabled ? ' disabled' : ''}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={onClick}
        role="button"
        tabIndex={0}
        aria-label="Upload audio file"
      >
        <input
          ref={inputRef}
          type="file"
          accept={SUPPORTED.join(',')}
          onChange={onInputChange}
          disabled={disabled}
          style={{ display: 'none' }}
        />
        <div className="upload-icon">
          <IconUploadCloud size={56} />
        </div>
        <div className="upload-title">
          {dragging ? 'Lepaskan file di sini' : 'Drag & drop file audio'}
        </div>
        <div className="upload-subtitle">
          atau klik untuk memilih file dari komputer
        </div>
        <div className="upload-formats">
          {SUPPORTED.join(' · ')}
        </div>
      </div>

      {file && (
        <div className="file-selected fade-in" id="file-selected">
          <span className="file-icon"><IconMusic size={22} /></span>
          <div className="file-info">
            <div className="file-name">{file.name}</div>
            <div className="file-size">{formatSize(file.size)}</div>
          </div>
          <button
            className="file-remove"
            onClick={(e) => { e.stopPropagation(); onFileSelect(null) }}
            title="Hapus file"
            disabled={disabled}
          >
            <IconX size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
