// components/ReportPanel.jsx
// Displays the final synthesised report with basic markdown rendering

export function ReportPanel({ report, status, embedded = false }) {
  const handleCopy = () => {
    navigator.clipboard.writeText(report)
  }

  // Very lightweight markdown → HTML (no extra deps needed)
  const renderMarkdown = (text) => {
    return text
      .replace(/^# (.+)$/gm,   '<h1>$1</h1>')
      .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g,   '<em>$1</em>')
      .replace(/^- (.+)$/gm,   '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/^(?!<[hul])/gm, '')
  }

  if (embedded) {
    return (
      <div className="embedded-report">
        {!report && status === "running" && (
          <div className="report-placeholder">
            <div className="report-skeleton" style={{ width: "70%" }} />
            <div className="report-skeleton" style={{ width: "90%" }} />
            <div className="report-skeleton" style={{ width: "60%" }} />
            <div className="report-skeleton" style={{ width: "85%" }} />
            <div className="report-skeleton" style={{ width: "50%" }} />
          </div>
        )}
        {report && (
          <>
            <div className="embedded-report-header">
              <span className="panel-icon">◎</span>
              <span>Research Report</span>
              <button className="copy-btn" onClick={handleCopy}>Copy</button>
            </div>
            <div
              className="report-content"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(report) }}
            />
          </>
        )}
      </div>
    )
  }

  return (
    <div className="panel panel-tall">
      <div className="panel-header">
        <span className="panel-icon">◎</span>
        <span>Research Report</span>
        {report && (
          <button className="copy-btn" onClick={handleCopy}>Copy</button>
        )}
      </div>
      <div className="panel-body report-body">
        {!report && status !== "done" && (
          <div className="report-empty">
            <div className="report-placeholder">
              {status === "running" ? (
                <>
                  <div className="report-skeleton" style={{ width: "70%" }} />
                  <div className="report-skeleton" style={{ width: "90%" }} />
                  <div className="report-skeleton" style={{ width: "60%" }} />
                  <div className="report-skeleton" style={{ width: "85%" }} />
                  <div className="report-skeleton" style={{ width: "50%" }} />
                </>
              ) : (
                <p>Report will appear here when research is complete</p>
              )}
            </div>
          </div>
        )}
        {report && (
          <div
            className="report-content"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(report) }}
          />
        )}
      </div>
    </div>
  )
}
