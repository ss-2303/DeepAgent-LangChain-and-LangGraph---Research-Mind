// components/FilesPanel.jsx

export function FilesPanel({ files }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-icon">◫</span>
        <span>Virtual Filesystem</span>
        {files.length > 0 && <span className="panel-count">{files.length}</span>}
      </div>
      <div className="panel-body">
        {files.length === 0 ? (
          <p className="panel-empty">No files saved yet...</p>
        ) : (
          <ul className="file-list">
            {files.map((filename, i) => (
              <li key={i} className="file-item">
                <span className="file-icon">◻</span>
                <span className="file-name">{filename}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
