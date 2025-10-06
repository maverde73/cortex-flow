"""
Web research tools for gathering information from the internet.
"""

from langchain_core.tools import tool
from typing import Optional
from config_legacy import settings


@tool
def tavily_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using Tavily API for up-to-date information.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)

    Returns:
        A formatted string containing search results with titles, URLs, and snippets
    """
    try:
        from tavily import TavilyClient

        if not settings.tavily_api_key:
            return (
                "Error: Tavily API key not configured. "
                "Please set TAVILY_API_KEY in your .env file."
            )

        client = TavilyClient(api_key=settings.tavily_api_key)

        # Perform the search
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )

        # Format the results
        if not response.get("results"):
            return f"No results found for query: {query}"

        formatted_results = [f"Search results for: {query}\n"]

        for idx, result in enumerate(response["results"], 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            content = result.get("content", "No content available")

            formatted_results.append(
                f"\n{idx}. {title}\n"
                f"   URL: {url}\n"
                f"   Summary: {content}\n"
            )

        return "\n".join(formatted_results)

    except ImportError:
        return (
            "Error: tavily-python package not installed. "
            "Install it with: pip install tavily-python"
        )
    except Exception as e:
        return f"Error performing web search: {str(e)}"


# For future expansion: other search providers
@tool
def search_web_duckduckgo(query: str, max_results: int = 5) -> str:
    """
    Alternative search using DuckDuckGo (no API key required).

    Args:
        query: The search query string
        max_results: Maximum number of results to return

    Returns:
        Formatted search results
    """
    # TODO: Implement DuckDuckGo search as a fallback
    return "DuckDuckGo search not yet implemented. Use tavily_search instead."
