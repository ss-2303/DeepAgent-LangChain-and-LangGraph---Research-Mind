// components/StepsPanel.jsx
// Live feed of every agent step — tool calls, results, todos, files

import { useEffect, useRef } from "react"

const STEP_CONFIG = {
  start:       { icon: "◈", label: "Started",       cls: "step-start"  },
  tool_call:   { icon: "→", label: "Calling tool",  cls: "step-call"   },
  tool_result: { icon: "✓", label: "Result",        cls: "step-result" },
  todos:       { icon: "☰", label: "Plan updated",  cls: "step-todo"   },
  files:       { icon: "◫", label: "File saved",    cls: "step-file"   },
  thinking:    { icon: "◌", label: "Thinking",      cls: "step-think"  },
  error:       { icon: "✕", label: "Error",         cls: "step-error"  },
}

export function StepsPanel({ steps, status, embedded = false }) {
  const bottomRef = useRef(null)

  // Auto-scroll to latest step
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [steps])

  const stepsList = (
    <>
      {steps.map((step, i) => {
        const config = STEP_CONFIG[step.type] || STEP_CONFIG.tool_call
        return (
          <div key={i} className={`step-item ${config.cls}`}>
            <span className="step-icon">{config.icon}</span>
            <div className="step-body">
              <span className="step-label">{config.label}</span>
              <span className="step-content">{step.content}</span>
            </div>
          </div>
        )
      })}
      {status === "running" && (
        <div className="step-item step-loading">
          <span className="step-icon"><span className="dot-pulse" /></span>
          <span className="step-content">Agent is working...</span>
        </div>
      )}
      <div ref={bottomRef} />
    </>
  )

  if (embedded) {
    return <div className="steps-body">{stepsList}</div>
  }

  return (
    <div className="panel panel-tall">
      <div className="panel-header">
        <span className="panel-icon">⟳</span>
        <span>Agent Steps</span>
        {status === "running" && <span className="live-badge">LIVE</span>}
        {steps.length > 0 && <span className="panel-count">{steps.length}</span>}
      </div>
      <div className="panel-body steps-body">
        {steps.length === 0 ? (
          <div className="steps-empty">
            <p>Enter a topic above to start research</p>
            <p className="steps-hint">You'll see every agent decision here in real time</p>
          </div>
        ) : stepsList}
      </div>
    </div>
  )
}
