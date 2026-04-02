// components/TodoPanel.jsx

const STATUS_ICON = {
  completed:   "✓",
  in_progress: "◉",
  pending:     "○",
}

const STATUS_CLASS = {
  completed:   "todo-done",
  in_progress: "todo-active",
  pending:     "todo-pending",
}

export function TodoPanel({ todos, embedded = false }) {
  const list = todos.length === 0 ? (
    <p className="panel-empty">Waiting for agent to plan...</p>
  ) : (
    <ul className="todo-list">
      {todos.map((todo, i) => (
        <li key={i} className={`todo-item ${STATUS_CLASS[todo.status] || ""}`}>
          <span className="todo-icon">{STATUS_ICON[todo.status] || "○"}</span>
          <span className="todo-content">{todo.content}</span>
        </li>
      ))}
    </ul>
  )

  if (embedded) return <div>{list}</div>

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-icon">☰</span>
        <span>Task Plan</span>
        {todos.length > 0 && (
          <span className="panel-count">{todos.filter(t => t.status === "completed").length}/{todos.length}</span>
        )}
      </div>
      <div className="panel-body">{list}</div>
    </div>
  )
}
