// components/TopicInput.jsx

export function TopicInput({ value, onChange, onSubmit, disabled }) {
  const handleKey = (e) => {
    if (e.key === "Enter" && !disabled) onSubmit()
  }

  return (
    <div className="topic-input-wrap">
      <input
        className="topic-input"
        type="text"
        placeholder="Enter a research topic... e.g. 'What is quantum computing?'"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKey}
        disabled={disabled}
      />
      <button
        className="research-btn"
        onClick={onSubmit}
        disabled={disabled || !value.trim()}
      >
        {disabled ? (
          <span className="btn-spinner" />
        ) : (
          "Research →"
        )}
      </button>
    </div>
  )
}
