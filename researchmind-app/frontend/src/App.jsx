// App.jsx — Chatbot Interface
import { useState, useEffect, useRef } from "react"
import { useAgentStream } from "./hooks/useAgentStream"
import { TopicInput } from "./components/TopicInput"
import { TodoPanel } from "./components/TodoPanel"
import { StepsPanel } from "./components/StepsPanel"
import { ReportPanel } from "./components/ReportPanel"
import "./index.css"

export default function App() {
  const { start, steps, todos, report, status } = useAgentStream()
  const [topic, setTopic] = useState("")
  const [submittedTopic, setSubmittedTopic] = useState("")
  const [taskPlanOpen, setTaskPlanOpen] = useState(false)
  const [stepsOpen, setStepsOpen] = useState(true)
  const chatBottomRef = useRef(null)

  const handleResearch = () => {
    if (topic.trim() && status !== "running") {
      const t = topic.trim()
      setSubmittedTopic(t)
      setTaskPlanOpen(false)
      setStepsOpen(true)
      start(t)
      setTopic("")
    }
  }

  // Auto-open task plan when todos arrive
  useEffect(() => {
    if (todos.length > 0) setTaskPlanOpen(true)
  }, [todos.length])

  // When done: collapse accordions so report is front and center
  useEffect(() => {
    if (status === "done") {
      setStepsOpen(false)
      setTaskPlanOpen(false)
    }
  }, [status])

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [steps.length, report])

  const doneTodos = todos.filter(t => t.status === "completed").length

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">◈</span>
            <span className="logo-text">ResearchMind</span>
          </div>
          <span className="logo-sub">Deep Research Agent</span>
        </div>
        {status !== "idle" && (
          <div className="status-badge" data-status={status}>
            {status === "running" && <span className="pulse" />}
            {status === "running" && "Researching..."}
            {status === "done"    && "Complete"}
            {status === "error"   && "Error"}
          </div>
        )}
      </header>

      {/* Chat area */}
      <div className="chat-area">
        {!submittedTopic ? (
          <div className="chat-welcome">
            <div className="welcome-icon">◈</div>
            <h2 className="welcome-title">What would you like to research?</h2>
            <p className="welcome-sub">Please allow up to 60 seconds on first use while the server wakes up.</p>
            <p className="welcome-sub">Enter a topic below and I'll conduct a comprehensive deep research analysis for you.</p>
            <div className="welcome-input">
              <TopicInput
                value={topic}
                onChange={setTopic}
                onSubmit={handleResearch}
                disabled={status === "running"}
              />
            </div>
          </div>
        ) : (
          <div className="chat-messages">
            {/* User message bubble */}
            <div className="chat-row chat-row-user">
              <div className="user-bubble">{submittedTopic}</div>
            </div>

            {/* Assistant response */}
            <div className="chat-row chat-row-assistant">
              <div className="chat-avatar">◈</div>
              <div className="chat-response">

                {/* Thinking dots before first step */}
                {status === "running" && steps.length === 0 && (
                  <div className="chat-thinking">
                    <span className="dot-pulse" />
                    <span className="dot-pulse" style={{ animationDelay: "0.25s" }} />
                    <span className="dot-pulse" style={{ animationDelay: "0.5s" }} />
                  </div>
                )}

                {/* Collapsible: Task Plan */}
                {todos.length > 0 && (
                  <div className="accordion">
                    <button className="accordion-header" onClick={() => setTaskPlanOpen(o => !o)}>
                      <span className="acc-icon" style={{ color: "var(--amber)" }}>☰</span>
                      <span>Task Plan</span>
                      <span className="accordion-badge">{doneTodos}/{todos.length}</span>
                      <span className="accordion-chevron">{taskPlanOpen ? "▲" : "▼"}</span>
                    </button>
                    {taskPlanOpen && (
                      <div className="accordion-body">
                        <TodoPanel todos={todos} embedded />
                      </div>
                    )}
                  </div>
                )}

                {/* Collapsible: Agent Steps */}
                {steps.length > 0 && (
                  <div className="accordion">
                    <button className="accordion-header" onClick={() => setStepsOpen(o => !o)}>
                      <span className="acc-icon" style={{ color: "var(--blue)" }}>⟳</span>
                      <span>Agent Steps</span>
                      <span className="accordion-badge">{steps.length}</span>
                      {status === "running" && <span className="live-badge">LIVE</span>}
                      <span className="accordion-chevron">{stepsOpen ? "▲" : "▼"}</span>
                    </button>
                    {stepsOpen && (
                      <div className="accordion-body accordion-steps-body">
                        <StepsPanel steps={steps} status={status} embedded />
                      </div>
                    )}
                  </div>
                )}

                {/* Report — skeleton while agent works, full content when ready */}
                {(report || (status === "running" && steps.length > 3) || status === "done") && (
                  <ReportPanel report={report} status={status} embedded />
                )}
              </div>
            </div>
          </div>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Input bar — only shown after research starts */}
      {submittedTopic && (
        <div className="input-bar">
          <TopicInput
            value={topic}
            onChange={setTopic}
            onSubmit={handleResearch}
            disabled={status === "running"}
          />
        </div>
      )}
    </div>
  )
}
