"""
tools/task_tool.py — Sub-Agent Delegation Tool

WHY SUB-AGENTS:
When a supervisor agent handles all research itself, its context window
fills with mixed content: planning messages, search results, intermediate
reasoning. This causes "context clash" — the model gets confused by the
noise and produces worse outputs.

Solution: delegate each subtopic to a FRESH sub-agent with an ISOLATED
context window containing only:
  1. Its system prompt (what kind of agent it is)
  2. Its single task description
  3. Its own tool call history

The supervisor's context stays clean. Each researcher focuses deeply.
This is how Anthropic's multi-agent research system works.

DUAL ROLE OF SUB-AGENTS:
Sub-agents play two roles simultaneously:
  - As a TOOL: the supervisor calls task() like any other tool
  - As an AGENT: internally runs its own ReAct loop (think → search → save → return)

This nesting is what makes "deep agents" powerful — agents calling agents.
"""

from typing import Annotated, NotRequired
from typing_extensions import TypedDict

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langchain.agents import create_agent
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from researchmind.prompts import TASK_DESCRIPTION_PREFIX
from researchmind.state import DeepAgentState


# ── Sub-agent configuration schema ───────────────────────────────────────────

class SubAgent(TypedDict):
    """
    Configuration for a specialised sub-agent.

    name:          unique identifier used to route task() calls
    description:   shown to the supervisor LLM — explains WHEN to use this agent
    system_prompt: the sub-agent's own instructions (different from supervisor's)
    tools:         list of tool functions available to this sub-agent
    """
    name: str
    description: str
    system_prompt: str
    tools: NotRequired[list]


# ── Task tool factory ─────────────────────────────────────────────────────────

def create_task_tool(subagents: list[SubAgent], model, state_schema):
    """
    Factory function that builds the task() tool from a list of SubAgent configs.

    WHY A FACTORY:
    The task() tool needs to close over the compiled sub-agent graphs.
    We build those graphs once here and capture them in the tool's closure.
    This avoids rebuilding agents on every call.

    Args:
        subagents:    list of SubAgent configs defining available sub-agents
        model:        the LLM to use for sub-agents
        state_schema: state class so sub-agents share the same state shape
    """

    # Compile all sub-agents into runnable graphs, keyed by name
    compiled_agents = {}
    agent_descriptions = []

    for agent_config in subagents:
        agent_tools = agent_config.get("tools", [])

        compiled = create_agent(
            model,
            agent_tools,
            system_prompt=agent_config["system_prompt"],
            state_schema=state_schema,
        ).with_config({"recursion_limit": 15})

        compiled_agents[agent_config["name"]] = compiled

        # Build description string shown to supervisor LLM
        agent_descriptions.append(
            f"  - '{agent_config['name']}': {agent_config['description']}"
        )

    # Dynamic tool description listing available sub-agents
    available_agents_str = "\n".join(agent_descriptions)
    task_description = f"""{TASK_DESCRIPTION_PREFIX}

Available sub-agents:
{available_agents_str}

Args:
    subagent_name: name of the sub-agent to use (must match exactly)
    task_description: clear, specific description of what to research and where to save results
"""

    # ── The actual task tool ──────────────────────────────────────────────────
    from langchain_core.tools import tool

    @tool(description=task_description)
    def task(
        subagent_name: str,
        task_description: str,
        tool_call_id: Annotated[str, InjectedToolCallId],
        state: Annotated[DeepAgentState, InjectedState],
    ) -> Command:
        """
        Delegate a research task to a specialised sub-agent.

        HOW IT WORKS:
        1. Look up the compiled sub-agent graph by name
        2. Invoke it with a FRESH message list (isolated context)
           — only the task description, no supervisor history
        3. Pass the current `files` state so the sub-agent can write to
           the shared virtual filesystem
        4. Return the sub-agent's final response as a ToolMessage
        5. Merge any files the sub-agent created back into supervisor state

        Args:
            subagent_name:    which sub-agent to use
            task_description: what to research (be specific and include where to save)
        """
        if subagent_name not in compiled_agents:
            available = list(compiled_agents.keys())
            return Command(update={
                "messages": [ToolMessage(
                    content=f"Error: unknown sub-agent '{subagent_name}'. Available: {available}",
                    tool_call_id=tool_call_id,
                )]
            })

        agent = compiled_agents[subagent_name]

        # KEY: fresh message list = isolated context window
        # The sub-agent starts clean — no supervisor planning messages
        result = agent.invoke({
            "messages": [{"role": "user", "content": task_description}],
            "files": state.get("files", {}),  # share the filesystem
            "todos": [],
        })

        # Extract the sub-agent's final text response
        final_messages = result.get("messages", [])
        final_response = ""
        for msg in reversed(final_messages):
            if hasattr(msg, "content") and isinstance(msg.content, str):
                final_response = msg.content
                break

        # Files written by the sub-agent (merged back via file_reducer in state)
        subagent_files = result.get("files", {})

        return Command(
            update={
                # Merge sub-agent's files into supervisor's filesystem
                "files": subagent_files,
                # Report back to supervisor what the sub-agent found
                "messages": [
                    ToolMessage(
                        content=f"Sub-agent '{subagent_name}' completed.\n\n{final_response}",
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )

    return task
