"""
backend/main.py — FastAPI Backend with SSE Streaming
"""

import json
import sys
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# ── Path setup ────────────────────────────────────────────────────────────────
# backend/main.py is at: Deep Agent - Claude/researchmind-app/backend/main.py
# researchmind/   is at: Deep Agent - Claude/researchmind/
# .env            is at: Deep Agent - Claude/.env
#
# ROOT = two levels up from backend/
ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── Import agent (after path is set) ─────────────────────────────────────────
from researchmind.agents.agent import build_research_agent

app = FastAPI(title="ResearchMind API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174","http://localhost:5173", "http://localhost:3000","https://deep-agent-research-mind.vercel.app/"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = build_research_agent()


def parse_step(step: dict) -> dict | None:
    messages = step.get("messages", [])
    if not messages:
        return None

    last_msg = messages[-1]
    msg_type = type(last_msg).__name__

    if msg_type == "AIMessage":
        tool_calls = getattr(last_msg, "tool_calls", [])
        if tool_calls:
            tool_name = tool_calls[0]["name"]
            tool_args = tool_calls[0].get("args", {})

            if tool_name == "task":
                desc = tool_args.get("task_description", "")[:80]
                return {"type": "tool_call", "content": f"Delegating to researcher: {desc}...", "tool": tool_name}

            if tool_name == "write_todos":
                todos = tool_args.get("todos", [])
                return {"type": "todos", "content": f"Planning {len(todos)} research tasks", "tool": tool_name, "data": todos}

            return {"type": "tool_call", "content": f"Calling {tool_name}()", "tool": tool_name}

        if last_msg.content and isinstance(last_msg.content, str):
            return {"type": "final", "content": last_msg.content}

    if msg_type == "ToolMessage":
        content = str(last_msg.content)

        if "saved successfully" in content:
            filename = content.split("'")[1] if "'" in content else "file"
            return {"type": "files", "content": f"Saved {filename}", "data": list(step.get("files", {}).keys())}

        if "TODO list updated" in content:
            return {"type": "todos", "content": "TODO list updated", "data": step.get("todos", [])}

        if "Sub-agent" in content and "completed" in content:
            return {"type": "tool_result", "content": "Researcher completed — findings saved"}

        return {"type": "tool_result", "content": content[:120] + ("..." if len(content) > 120 else "")}

    return None


async def stream_research(topic: str) -> AsyncGenerator[str, None]:
    yield f"data: {json.dumps({'type': 'start', 'content': f'Starting research on: {topic}'})}\n\n"

    try:
        final_state = None

        for step in agent.stream(
            {"messages": [{"role": "user", "content": topic}], "todos": [], "files": {}},
            stream_mode="values",
        ):
            final_state = step
            event = parse_step(step)
            if event:
                yield f"data: {json.dumps(event)}\n\n"

        if final_state:
            todos = final_state.get("todos", [])
            files = final_state.get("files", {})

            if todos:
                yield f"data: {json.dumps({'type': 'todos', 'content': 'Research complete', 'data': todos})}\n\n"
            if files:
                yield f"data: {json.dumps({'type': 'files', 'content': 'All files saved', 'data': list(files.keys())})}\n\n"

            for msg in reversed(final_state.get("messages", [])):
                if hasattr(msg, "content") and isinstance(msg.content, str) and len(msg.content) > 200:
                    yield f"data: {json.dumps({'type': 'report', 'content': msg.content})}\n\n"
                    break

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    yield f"data: {json.dumps({'type': 'done', 'content': 'Research complete'})}\n\n"


@app.get("/research")
async def research(topic: str):
    return StreamingResponse(
        stream_research(topic),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "ready"}
