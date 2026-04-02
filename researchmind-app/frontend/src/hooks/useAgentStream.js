// hooks/useAgentStream.js
//
// Custom hook that connects to the FastAPI SSE endpoint and manages
// all agent state: steps, todos, files, report, and status.
//
// WHY SSE OVER FETCH:
// Regular fetch waits for the full response. SSE (EventSource) receives
// each event as it's pushed by the server — perfect for live agent updates.
//
// USAGE:
//   const { start, steps, todos, files, report, status } = useAgentStream()
//   start("quantum computing")  // kicks off research

import { useState, useCallback, useRef } from "react"

export function useAgentStream() {
  const [steps, setSteps]   = useState([])   // live agent step log
  const [todos, setTodos]   = useState([])   // current TODO list
  const [files, setFiles]   = useState([])   // saved filenames
  const [report, setReport] = useState("")   // final markdown report
  const [status, setStatus] = useState("idle") // idle | running | done | error
  const sourceRef = useRef(null)

  const start = useCallback((topic) => {
    // Reset all state for new research run
    setSteps([])
    setTodos([])
    setFiles([])
    setReport("")
    setStatus("running")

    // Close any existing stream
    if (sourceRef.current) sourceRef.current.close()

    // Open SSE connection to backend
    const url = `http://localhost:8000/research?topic=${encodeURIComponent(topic)}`
    const source = new EventSource(url)
    sourceRef.current = source

    source.onmessage = (e) => {
      const event = JSON.parse(e.data)

      switch (event.type) {
        case "start":
          setSteps(prev => [...prev, { type: "start", content: event.content, ts: Date.now() }])
          break

        case "tool_call":
          setSteps(prev => [...prev, { type: "tool_call", content: event.content, tool: event.tool, ts: Date.now() }])
          break

        case "tool_result":
          setSteps(prev => [...prev, { type: "tool_result", content: event.content, ts: Date.now() }])
          break

        case "todos":
          // Update the TODO sidebar panel
          if (event.data) setTodos(event.data)
          setSteps(prev => [...prev, { type: "todos", content: event.content, ts: Date.now() }])
          break

        case "files":
          // Update the files sidebar panel
          if (event.data) setFiles(event.data)
          setSteps(prev => [...prev, { type: "files", content: event.content, ts: Date.now() }])
          break

        case "final":
          setSteps(prev => [...prev, { type: "thinking", content: event.content.slice(0, 100) + "...", ts: Date.now() }])
          break

        case "report":
          // Final synthesised report
          setReport(event.content)
          break

        case "error":
          setStatus("error")
          setSteps(prev => [...prev, { type: "error", content: event.content, ts: Date.now() }])
          source.close()
          break

        case "done":
          setStatus("done")
          source.close()
          break
      }
    }

    source.onerror = () => {
      setStatus("error")
      setSteps(prev => [...prev, { type: "error", content: "Connection lost", ts: Date.now() }])
      source.close()
    }
  }, [])

  return { start, steps, todos, files, report, status }
}
