# ResearchMind — CLAUDE.md

## Project Overview

Deep Research Agent built with LangChain and LangGraph. A supervisor agent plans research tasks, delegates subtopics to isolated researcher sub-agents, and synthesises a structured final report.

## Run

```bash
pip install -r requirements.txt
python main.py "Your research topic here"
```

## Project Structure

```
files/
├── main.py                          # Entry point: run_research() + print_results()
├── requirements.txt
├── .env                             # API keys (OPENAI_API_KEY, TAVILY_API_KEY required)
└── researchmind/
    ├── state.py                     # DeepAgentState: todos + files (virtual filesystem)
    ├── prompts.py                   # All system prompts and tool descriptions
    ├── agents/
    │   └── agent.py                 # build_research_agent() — wires everything together
    └── tools/
        ├── todo_tools.py            # write_todos, read_todos
        ├── file_tools.py            # ls, read_file, write_file
        ├── search_tool.py           # search (Tavily), think
        └── task_tool.py             # create_task_tool() factory + SubAgent TypedDict
```

## Architecture

```
User topic
    │
    ▼
Supervisor Agent  (gpt-4.1-mini, temp=0, recursion_limit=30)
  Tools: write_todos, read_todos, ls, read_file, write_file, think, task()
  Flow:  plan TODOs → delegate subtopics → read files → synthesise report
    │
    │ task() — fresh isolated context per call
    ▼
Researcher Sub-Agent  (same model, recursion_limit=15)
  Tools: search, think, write_file
  Flow:  search web → save findings to .md file → return summary
```

## State Schema (`state.py`)

`DeepAgentState` extends LangGraph's `AgentState`:
- `messages` — inherited; full conversation history (append-only)
- `todos: list[Todo]` — task plan; full rewrite on each update (no reducer)
- `files: dict[str, str]` — virtual filesystem; merged via `file_reducer` (new files added, duplicate keys overwritten)

`Todo` has two fields: `content: str` and `status: Literal["pending", "in_progress", "completed"]`.

## Key Patterns

**InjectedState / InjectedToolCallId** — tools receive graph state and tool_call_id without exposing them to the LLM's tool schema. Used in all stateful tools.

**Command returns** — tools return `Command(update={...})` to update both `messages` and other state fields (e.g. `todos`, `files`) atomically in one operation.

**Tool factory** — `create_task_tool(subagents, model, state_schema)` compiles sub-agent graphs once and closes over them. Avoids rebuilding on every call.

**Context isolation** — `task()` invokes sub-agents with a fresh `messages` list containing only the task description. The supervisor's planning history is never passed down.

**Virtual filesystem** — raw search results are saved to `files` dict immediately; only read back during synthesis. Prevents context bloat.

**Prompts as source code** — all tool descriptions and system prompts live in `prompts.py`. Tool descriptions tell the LLM *when* to use a tool, not just what it does.

## Swapping the LLM

`build_research_agent()` in `agents/agent.py` accepts a `model_name` string:

```python
# Default
build_research_agent()  # "openai:gpt-4.1-mini"

# Use Claude
build_research_agent(model_name="anthropic:claude-sonnet-4-6")
```

Uses `langchain.chat_models.init_chat_model` — supports any LangChain-compatible provider string.

## API Keys

Required in `.env`:
- `OPENAI_API_KEY` — platform.openai.com
- `TAVILY_API_KEY` — tavily.com (free: 1000 searches/month)

Optional (LangSmith tracing):
- `LANGSMITH_API_KEY`
- `LANGSMITH_TRACING=true`
- `LANGSMITH_PROJECT=researchmind`

## Dependencies

```
langchain>=1.0.0
langchain-core>=0.3.0
langchain-openai>=0.3.0
langgraph>=0.5.0
tavily-python>=0.5.0
python-dotenv>=1.0.0
```
