"""
agents/agent.py — Main Supervisor Agent

This is where all components are wired together into a runnable agent.

ARCHITECTURE RECAP:
┌─────────────────────────────────────────────────────┐
│                  SUPERVISOR AGENT                    │
│  Tools: write_todos, read_todos, ls, read_file,     │
│         write_file, think, task()                    │
│                                                      │
│  Responsibilities:                                   │
│    1. Plan research as a TODO list                   │
│    2. Delegate subtopics to researcher sub-agents    │
│    3. Read saved files after research completes      │
│    4. Synthesise final report                        │
└─────────────────────────────────────────────────────┘
         │ delegates via task()
         ▼
┌─────────────────────────────────────────────────────┐
│               RESEARCHER SUB-AGENT                   │
│  Tools: search, think, write_file                    │
│                                                      │
│  Responsibilities:                                   │
│    1. Search the web for its specific subtopic       │
│    2. Save findings to the virtual filesystem        │
│    3. Return a brief summary to the supervisor       │
└─────────────────────────────────────────────────────┘
"""

from datetime import datetime

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from researchmind.prompts import (
    FILE_USAGE_INSTRUCTIONS,
    RESEARCHER_SYSTEM_PROMPT,
    SUBAGENT_USAGE_INSTRUCTIONS,
    SUPERVISOR_SYSTEM_PROMPT,
    TODO_USAGE_INSTRUCTIONS,
)
from researchmind.state import DeepAgentState
from researchmind.tools.file_tools import ls, read_file, write_file
from researchmind.tools.search_tool import get_today_str, search, think
from researchmind.tools.task_tool import SubAgent, create_task_tool
from researchmind.tools.todo_tools import read_todos, write_todos


def build_research_agent(model_name: str = "openai:gpt-4.1-mini"):
    """
    Build and return the full research agent system.

    DESIGN DECISIONS:
    - gpt-4.1-mini: good balance of capability and cost for demos
    - temperature=0: deterministic outputs, easier to debug and demo
    - recursion_limit=30: supervisor may need many steps for complex topics
      (plan → delegate × N → read files × N → synthesise)

    Args:
        model_name: LangChain model string. Swap for "anthropic:claude-3-5-haiku-20241022"
                    or any other supported model.

    Returns:
        Compiled LangGraph agent ready for .invoke() or .stream()
    """
    today = get_today_str()

    # ── Shared LLM ────────────────────────────────────────────────────────────
    model = init_chat_model(model=model_name, temperature=0.0)

    # ── Researcher sub-agent definition ──────────────────────────────────────
    # The researcher gets search + think + write_file
    # It does NOT get todo tools (no planning needed — one focused task)
    # It does NOT get read_file (it writes, doesn't need to read others' work)
    researcher_tools = [search, think, write_file]

    researcher_subagent: SubAgent = {
        "name": "research-agent",
        "description": (
            "Delegate a focused research subtopic to this agent. "
            "It will search the web, save findings to a file, and return a summary. "
            "Give it ONE topic at a time with a specific filename to save to."
        ),
        "system_prompt": RESEARCHER_SYSTEM_PROMPT.format(date=today),
        "tools": researcher_tools,
    }

    # ── Task tool (wraps researcher as a callable tool) ───────────────────────
    task_tool = create_task_tool(
        subagents=[researcher_subagent],
        model=model,
        state_schema=DeepAgentState,
    )

    # ── Supervisor tools ──────────────────────────────────────────────────────
    supervisor_tools = [
        write_todos,   # planning
        read_todos,    # refresh plan awareness
        ls,            # check filesystem
        read_file,     # read researcher outputs
        write_file,    # save final report
        think,         # structured reasoning
        task_tool,     # delegate to researchers ← the key tool
    ]

    # ── Supervisor system prompt ──────────────────────────────────────────────
    supervisor_prompt = SUPERVISOR_SYSTEM_PROMPT.format(
        todo_instructions=TODO_USAGE_INSTRUCTIONS,
        file_instructions=FILE_USAGE_INSTRUCTIONS,
        subagent_instructions=SUBAGENT_USAGE_INSTRUCTIONS,
        date=today,
    )

    # ── Build and return the compiled agent graph ─────────────────────────────
    agent = create_agent(
        model,
        supervisor_tools,
        system_prompt=supervisor_prompt,
        state_schema=DeepAgentState,
    ).with_config({"recursion_limit": 30})

    return agent
