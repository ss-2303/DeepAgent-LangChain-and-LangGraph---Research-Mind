"""
tools/file_tools.py — Virtual Filesystem Tools

WHY A VIRTUAL FILESYSTEM:
Agent context windows fill up fast. A researcher finding 3 web pages per
subtopic × 4 subtopics = 12 large tool results sitting in the context window.
This causes:
  - Context bloat: LLM spends attention on raw data instead of reasoning
  - Context confusion: mixing research results with planning messages
  - Higher cost: more tokens per call

The solution (used by Manus and other production agents): offload raw content
to files immediately after retrieval, and only read them back when needed
for synthesis. The context stays clean; information is never lost.

IMPLEMENTATION:
We use a plain Python dict in LangGraph state as our "filesystem":
    files = { "quantum_basics.md": "content...", "applications.md": "..." }

This gives us short-term, thread-scoped persistence — perfect for a single
research session. No disk I/O needed, no external storage.
"""

from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from researchmind.prompts import LS_DESCRIPTION, READ_FILE_DESCRIPTION, WRITE_FILE_DESCRIPTION
from researchmind.state import DeepAgentState


@tool(description=LS_DESCRIPTION)
def ls(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[DeepAgentState, InjectedState],
) -> Command:
    """
    List all files in the virtual filesystem.

    No arguments needed — reads directly from state via InjectedState.
    Returns filenames so the agent knows what's already been saved.
    """
    files = state.get("files", {})
    if not files:
        content = "No files saved yet."
    else:
        content = "Files in virtual filesystem:\n" + "\n".join(f"  - {k}" for k in files.keys())

    return Command(
        update={
            "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)]
        }
    )


@tool(description=READ_FILE_DESCRIPTION)
def read_file(
    filename: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[DeepAgentState, InjectedState],
) -> Command:
    """
    Read a file from the virtual filesystem.

    Args:
        filename: The name of the file to read (use ls() to see available files).

    ERROR HANDLING NOTE:
    Error messages here are written FOR THE LLM, not the user.
    In agentic systems, the LLM reads tool errors and can self-correct —
    e.g. "file not found" tells it to check ls() first.
    """
    files = state.get("files", {})

    if filename not in files:
        available = list(files.keys()) or ["none"]
        content = f"Error: '{filename}' not found. Available files: {available}"
    else:
        content = f"Contents of {filename}:\n\n{files[filename]}"

    return Command(
        update={
            "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)]
        }
    )


@tool(description=WRITE_FILE_DESCRIPTION)
def write_file(
    filename: str,
    content: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[DeepAgentState, InjectedState],
) -> Command:
    """
    Write content to a file in the virtual filesystem.

    Args:
        filename: Descriptive name ending in .md (e.g. "quantum_basics.md")
        content:  The research content to save

    WHY Command HERE:
    We need to update BOTH `files` in state AND append a ToolMessage to
    `messages`. Command lets us do both atomically in one return.

    The file_reducer in state.py handles merging — new files are added,
    existing filenames are overwritten (latest write wins).
    """
    return Command(
        update={
            # Update the files dict — file_reducer merges this with existing files
            "files": {filename: content},
            # Confirm to the LLM that the file was saved
            "messages": [
                ToolMessage(
                    content=f"File '{filename}' saved successfully ({len(content)} chars).",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )
