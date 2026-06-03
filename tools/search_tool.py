"""
search_tool.py — Tavily web search integration for Orrbit.

Used when RAG has no relevant context for a query.
Falls back gracefully if Tavily is unavailable.
"""

import os
from langchain_tavily import TavilySearch


def get_search_tool():
    """Returns a configured Tavily search tool."""
    return TavilySearch(
        max_results=5,
        topic="general",
        include_answer=True,
        include_raw_content=False,
        include_images=False,
    )


def web_search(query: str) -> str:
    """
    Search the web for a query and return formatted results.
    Returns empty string if search fails.
    """
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        print("[Search] No TAVILY_API_KEY found in .env")
        return ""

    try:
        tool = get_search_tool()
        results = tool.invoke({"query": query})

        if isinstance(results, str):
            return results

        if isinstance(results, dict):
            answer = ""

            # Direct AI summary from Tavily
            if results.get("answer"):
                answer = f"**Web Search Summary:**\n{results['answer']}\n\n"

            # Individual source results
            sources = results.get("results", [])
            if sources:
                answer += "**Sources:**\n"
                for i, src in enumerate(sources[:3], 1):
                    title   = src.get("title", "")
                    content = src.get("content", "")
                    url     = src.get("url", "")
                    answer += f"\n{i}. **{title}**\n{content}\nSource: {url}\n"

            return answer.strip()

        return str(results)

    except Exception as e:
        print(f"[Search] Web search failed: {e}")
        return ""


def web_search_node(state: dict) -> dict:
    """
    LangGraph node — performs web search and adds results to retrieved_context.
    Only triggers if RAG returned no context, saving Tavily credits.
    """
    existing_context = state.get("retrieved_context", "").strip()
    query = state.get("user_query", "")

    if existing_context:
        print("[Search] RAG context found — skipping web search")
        return state

    if not query:
        return state

    print(f"[Search] No RAG context — searching web for: '{query[:60]}'")
    web_context = web_search(query)

    if web_context:
        print("[Search] Web results found ✓")
        return {**state, "retrieved_context": web_context, "used_web_search": True}

    print("[Search] No web results — Groq will answer from training data")
    return state
