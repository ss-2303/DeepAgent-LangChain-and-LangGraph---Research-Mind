"""
tools/search_tool.py — Web Search and Think Tools

SEARCH TOOL:
Uses Tavily API — designed specifically for LLM agents (returns clean,
structured results unlike raw Google HTML). Free tier: 1000 searches/month.

THINK TOOL:
A "scratchpad" tool that lets the agent reason step by step before acting.
The LLM calls think() with its reasoning, which gets recorded in messages.
This improves output quality on complex tasks — the model externalises
its chain-of-thought rather than trying to hold it all in one generation.

Inspired by: Anthropic's research showing extended thinking improves
performance on multi-step reasoning tasks.
"""

import os
from datetime import datetime

from langchain_core.tools import tool
from tavily import TavilyClient


def get_today_str() -> str:
    """Return today's date as a readable string."""
    return datetime.now().strftime("%B %d, %Y")


@tool
def search(query: str) -> str:
    """
    Search the web for current information on a topic.

    Use this to find up-to-date information beyond your training data.
    Returns a summary of the top search results.

    Args:
        query: A specific, focused search query. Be precise — good queries
               return better results. Example: "quantum computing qubit basics 2024"
               not just "quantum computing".
    """
    # Tavily is purpose-built for AI agents — returns clean summaries,
    # not raw HTML. Much better signal-to-noise than scraping Google.
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    response = client.search(
        query=query,
        max_results=5,           # top 5 sources
        search_depth="advanced", # deeper crawl for better quality
        include_answer=True,     # Tavily's own AI summary of results
    )

    # Format results for the LLM
    output_parts = []

    # Include Tavily's synthesised answer if available
    if response.get("answer"):
        output_parts.append(f"Summary: {response['answer']}\n")

    # Include individual source results
    for i, result in enumerate(response.get("results", []), 1):
        output_parts.append(
            f"[{i}] {result['title']}\n"
            f"    URL: {result['url']}\n"
            f"    {result['content'][:500]}...\n"  # truncate long content
        )

    return "\n".join(output_parts) if output_parts else "No results found."


@tool
def think(reasoning: str) -> str:
    """
    Use this tool to reason through a problem before acting.

    WHEN TO USE:
    - Before deciding which subtopics to research
    - When search results are ambiguous or conflicting
    - Before writing the final synthesis

    This is your scratchpad — think out loud here.

    Args:
        reasoning: Your step-by-step reasoning about the current situation.
    """
    # The reasoning is recorded in messages — visible in traces, useful for debugging
    return f"Reasoning recorded:\n{reasoning}"
