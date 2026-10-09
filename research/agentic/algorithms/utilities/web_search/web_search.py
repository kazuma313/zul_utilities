import logging

from langchain_core.tools import tool

from app.config.settings import settings

logger = logging.getLogger(__name__)


@tool
def web_search(query: str) -> str:
    """Search the web for current, up-to-date information.

    Use this when the user asks about recent events, news, live data,
    current prices, or anything that may have changed after your training cutoff.
    Do NOT use this for math or calculations.

    Args:
        query: A concise search query (2-10 words recommended).
    """
    logger.info("[TOOL] web_search called | query: %r", query)

    if not settings.TAVILY_API_KEY:
        logger.warning("[TOOL] web_search skipped — TAVILY_API_KEY not set")
        return "Web search is unavailable: TAVILY_API_KEY is not configured."

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(query=query, max_results=5)

        results = response.get("results", [])
        if not results:
            logger.info("[TOOL] web_search returned 0 results for: %r", query)
            return f"No results found for: {query}"

        logger.info("[TOOL] web_search returned %d results for: %r", len(results), query)

        lines = [f"Search results for: {query}\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "")
            content = r.get("content", "")[:300]
            lines.append(f"{i}. **{title}**\n   {url}\n   {content}\n")

        return "\n".join(lines)

    except Exception as e:
        logger.error("[TOOL] web_search error: %s", e)
        return f"Web search failed: {e}"
