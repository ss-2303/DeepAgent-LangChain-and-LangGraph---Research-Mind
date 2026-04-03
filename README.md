# ResearchMind 🔍

A **Deep Research Agent** built with LangChain and LangGraph that autonomously
plans, researches, and synthesises structured reports on any topic.

## What it does

Give it a topic. It produces a comprehensive, sourced research report by:

1. **Planning** — writes a structured TODO list before acting
2. **Delegating** — spins up isolated researcher sub-agents per subtopic
3. **Offloading** — saves raw findings to a virtual filesystem (not the context window)
4. **Synthesising** — reads all saved files and writes a final structured report

## Architecture

```
User: "Explain transformer architecture"
         │
         ▼
┌─────────────────────┐
│  SUPERVISOR AGENT   │  Plans TODOs → delegates → reads files → writes report
│  Tools:             │
│    write_todos      │  ← task planning
│    read_todos       │  ← refresh awareness
│    ls / read_file   │  ← context management
│    write_file       │  ← save final report
│    think            │  ← structured reasoning
│    task()           │  ← delegate to sub-agents
└─────────────────────┘
         │ task()
         ▼
┌─────────────────────┐
│  RESEARCHER AGENT   │  Searches web → saves findings → returns summary
│  Tools:             │
│    search           │  ← Tavily web search
│    think            │  ← structured reasoning
│    write_file       │  ← saves to shared filesystem
└─────────────────────┘
```

## Key Concepts Demonstrated

| Concept | Where | Why It Matters |
|---|---|---|
| **ReAct Loop** | Both agents | Think → Act → Observe → repeat |
| **Custom State** | `state.py` | Carry todos + files across all steps |
| **InjectedState** | All tools | Share state without exposing it to the LLM |
| **Command updates** | All tools | Update state AND messages in one operation |
| **TODO Planning** | `todo_tools.py` | Keeps long-running agents on track |
| **Virtual Filesystem** | `file_tools.py` | Offload context to prevent bloat |
| **Sub-agent Delegation** | `task_tool.py` | Isolate context per subtopic |
| **Tool Factories** | `task_tool.py` | Build tools dynamically from config |

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add API keys
cp .env.example .env
# Edit .env with your keys:
#   OPENAI_API_KEY  — https://platform.openai.com
#   TAVILY_API_KEY  — https://tavily.com (free: 1000 searches/month)

# 3. Run
python main.py "What is quantum computing and where is it used today?"
```

## Example Output

```
============================================================
🔍 ResearchMind — Deep Research Agent
============================================================
Topic: What is quantum computing and where is it used today?

🤖 Agent → calling write_todos()
   ✓ TODO list updated:
     [PENDING] research quantum computing fundamentals
     [PENDING] research real-world applications
     [PENDING] research current limitations and timeline
     [PENDING] synthesise findings into final report

🤖 Agent → calling task()
   ✓ Sub-agent 'research-agent' completed. Found information on qubits...

🤖 Agent → calling task()
   ✓ Sub-agent 'research-agent' completed. Found applications in...

...

📝 FINAL REPORT:
# Quantum Computing: Current State and Applications

## Overview
Quantum computing leverages quantum mechanical phenomena...
```

## Project Structure

```
researchmind/
├── state.py              # Custom AgentState with todos + virtual filesystem
├── prompts.py            # All system prompts in one place
├── agents/
│   └── agent.py          # Supervisor agent — wires everything together
├── tools/
│   ├── todo_tools.py     # write_todos, read_todos
│   ├── file_tools.py     # ls, read_file, write_file
│   ├── search_tool.py    # Tavily web search + think tool
│   └── task_tool.py      # Sub-agent delegation tool factory
├── main.py               # Entry point
├── requirements.txt
└── .env.example
```

## Optional: LangSmith Tracing

Add to `.env` to see step-by-step agent traces:
```
LANGSMITH_API_KEY=lsv2_...
LANGCHAIN_TRACING_V2=true
```

Then visit https://smith.langchain.com to watch every tool call, LLM decision,
and sub-agent invocation in a visual timeline.
