"""
tools/todo_tools.py — TODO List Management Tools

WHY THESE TOOLS EXIST:
Long-running agents lose focus as the context window fills up with tool calls,
search results, and intermediate reasoning. A TODO list gives the agent an
explicit, updatable plan it can refer back to at any point.

This pattern is used by Claude Code (TodoWrite tool) and Manus (~50 tool calls
per task on average). Without it, agents tend to repeat work or miss subtopics.

KEY LANGCHAIN/LANGGRAPH CONCEPTS DEMONSTRATED:
- @tool decorator: registers a function as an LLM-callable tool
- InjectedState: injects graph state into the tool WITHOUT exposing it to the LLM
  (the LLM doesn't see state in the tool's schema — LangGraph injects it after)
- InjectedToolCallId: injects the tool call ID for creating ToolMessage responses
- Command: used to update state AND return a message in one operation
"""

from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from researchmind.prompts import WRITE_TODOS_DESCRIPTION
from researchmind.state import DeepAgentState, Todo


@tool(description=WRITE_TODOS_DESCRIPTION, parse_docstring=True)
def write_todos(
    todos: list[Todo],
    tool_call_id: Annotated[str, InjectedToolCallId],  # ← injected, not sent to LLM
    state: Annotated[DeepAgentState, InjectedState],    # ← injected, not sent to LLM
) -> Command:
    """
    Write or update the TODO list.

    WHY Command INSTEAD OF a plain return:
    Normally a tool returns a string that becomes a ToolMessage in `messages`.
    Command lets us ALSO update other state fields (here: `todos`) in the same
    operation. Without Command, we could only update `messages`.

    Args:
        todos: Full list of Todo items (content + status) to write to state.
    """
    # Format todos as a readable string for the ToolMessage
    todo_str = "\n".join(
        f"[{t['status'].upper()}] {t['content']}" for t in todos
    )

    return Command(
        update={
            # 1. Update the todos field in state
            "todos": todos,
            # 2. Add a ToolMessage to messages so the LLM sees what was written
            "messages": [
                ToolMessage(
                    content=f"TODO list updated:\n{todo_str}",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


@tool
def read_todos(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[DeepAgentState, InjectedState],
) -> Command:
    """
    Read the current TODO list from state.

    WHEN TO USE:
    The LLM can call this to "refresh" its awareness of the plan — useful
    in very long conversations where the original write_todos call has
    scrolled far back in the context window.
    """
    todos = state.get("todos", [])

    if not todos:
        content = "No TODOs found. Use write_todos to create a plan first."
    else:
        content = "Current TODOs:\n" + "\n".join(
            f"[{t['status'].upper()}] {t['content']}" for t in todos
        )

    return Command(
        update={
            "messages": [
                ToolMessage(content=content, tool_call_id=tool_call_id)
            ]
        }
    )
