"""
state.py — Custom Agent State

WHY THIS EXISTS:
LangGraph agents are stateful graphs. Every node (tool call, LLM step) reads
from and writes to a shared State object. By extending the default AgentState,
we can carry extra data — like a TODO list and a virtual filesystem — across
every step of the agent's execution.

KEY CONCEPTS:
- AgentState: base state that holds the `messages` list (the conversation)
- Annotated + reducer: tells LangGraph HOW to merge updates to a field
  when multiple nodes write to it at the same time
- TypedDict: gives our state fields type safety
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict, NotRequired

from langchain.agents import AgentState  # base state with messages list


# ── Reducer functions ─────────────────────────────────────────────────────────

def file_reducer(left: dict | None, right: dict | None) -> dict:
    """
    Merge two file dictionaries.

    WHY: When a sub-agent writes a file, we want to ADD it to existing files,
    not replace the whole dictionary. Right-side values overwrite left on
    duplicate keys (latest write wins).
    """
    if not left:
        left = {}
    if not right:
        right = {}
    return {**left, **right}


# ── Data models ───────────────────────────────────────────────────────────────

class Todo(TypedDict):
    """
    A single task in the agent's TODO list.

    WHY: Long-running agents lose track of what they've done as the context
    window grows. A structured TODO list keeps the agent anchored to the plan.
    Inspired by how Claude Code and Manus manage multi-step tasks internally.
    """
    content: str                              # short description of the task
    status: Literal["pending", "in_progress", "completed"]


# ── Main state schema ─────────────────────────────────────────────────────────

class DeepAgentState(AgentState):
    """
    Extended state for the Deep Research Agent.

    Fields:
        messages  (inherited) — full conversation history; LangGraph appends to this
        todos     — the agent's current task plan; overwritten on each update
        files     — virtual filesystem: {filename: content}; merged by file_reducer
    """

    # No custom reducer: the agent rewrites the full list each time it replans.
    # This lets it reprioritise tasks dynamically as work progresses.
    todos: NotRequired[list[Todo]]

    # file_reducer merges new files into existing ones instead of replacing all.
    files: Annotated[dict[str, str], file_reducer]
