"""
main.py — Entry Point

Run the ResearchMind agent from the command line:
    python main.py "Explain transformer architecture in deep learning"
    python main.py "What is quantum computing and where is it used?"
    python main.py "Overview of reinforcement learning from human feedback"

Or import and use programmatically:
    from main import run_research
    result = run_research("Your topic here")
"""

import os
import sys

from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()


def run_research(topic: str, stream: bool = True) -> dict:
    """
    Run the research agent on a given topic.

    This function:
    1. Builds the full agent system (supervisor + researcher)
    2. Invokes it with the user's topic
    3. Prints the agent's steps as they happen (if stream=True)
    4. Returns the final state including the report and saved files

    Args:
        topic:  The research question or topic
        stream: If True, print each step live. If False, run silently.

    Returns:
        dict with keys: messages, todos, files
    """
    # Import here so env vars are loaded first
    from researchmind.agents.agent import build_research_agent

    print(f"\n{'='*60}")
    print(f"🔍 ResearchMind — Deep Research Agent")
    print(f"{'='*60}")
    print(f"Topic: {topic}\n")

    agent = build_research_agent()

    if stream:
        # Stream mode: print each step as it happens
        # This makes the demo compelling — you can see the agent think and plan
        print("Agent is working...\n")
        final_state = None

        for step in agent.stream(
            {
                "messages": [{"role": "user", "content": topic}],
                "todos": [],
                "files": {},
            },
            stream_mode="values",  # stream full state after each step
        ):
            final_state = step

            # Print the latest message from each step
            messages = step.get("messages", [])
            if messages:
                last_msg = messages[-1]
                msg_type = type(last_msg).__name__

                if msg_type == "AIMessage":
                    # LLM is reasoning or calling a tool
                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        tool_name = last_msg.tool_calls[0]["name"]
                        print(f"🤖 Agent → calling {tool_name}()")
                    elif last_msg.content:
                        print(f"🤖 Agent → {last_msg.content[:200]}...")

                elif msg_type == "ToolMessage":
                    # Tool returned a result
                    content_preview = str(last_msg.content)[:150]
                    print(f"   ✓ Tool result: {content_preview}...")
                    print()

        return final_state

    else:
        # Silent mode: run to completion, return state
        return agent.invoke(
            {
                "messages": [{"role": "user", "content": topic}],
                "todos": [],
                "files": {},
            }
        )


def print_results(state: dict):
    """Pretty-print the final results from the agent."""
    print(f"\n{'='*60}")
    print("📁 FILES SAVED TO VIRTUAL FILESYSTEM:")
    print(f"{'='*60}")
    files = state.get("files", {})
    if files:
        for filename in files:
            print(f"  📄 {filename}")
    else:
        print("  (none)")

    print(f"\n{'='*60}")
    print("✅ COMPLETED TODOs:")
    print(f"{'='*60}")
    todos = state.get("todos", [])
    for todo in todos:
        status_icon = "✅" if todo["status"] == "completed" else "⏳"
        print(f"  {status_icon} {todo['content']}")

    print(f"\n{'='*60}")
    print("📝 FINAL REPORT:")
    print(f"{'='*60}\n")
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and isinstance(msg.content, str) and len(msg.content) > 200:
            print(msg.content)
            break


if __name__ == "__main__":
    # Validate API keys
    missing = []
    if not os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    if not os.getenv("TAVILY_API_KEY"):
        missing.append("TAVILY_API_KEY")

    if missing:
        print(f"❌ Missing API keys in .env: {', '.join(missing)}")
        print("   Get Tavily free key at: https://tavily.com")
        sys.exit(1)

    # Get topic from command line or use default
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the Model Context Protocol (MCP)?"

    state = run_research(topic)
    print_results(state)
