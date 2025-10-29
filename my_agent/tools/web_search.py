"""Web search tool using Serper.dev API."""
import os
import json
import time
from typing import Optional, List, Dict, Any
import httpx

from my_agent.utils.http_client import get_http_client, retry_with_backoff, serper_rate_limiter
from my_agent.utils.source_quality import rank_search_results
from my_agent.utils.date_parser import parse_date_to_iso
from my_agent.utils.logger import get_structured_logger

logger = get_structured_logger(__name__)


@retry_with_backoff(max_retries=3, base_delay=1.0)
def _call_serper_api(
    query: str,
    num_results: int,
    recency_days: Optional[int],
    sites: Optional[List[str]],
    blocked_sites: Optional[List[str]]
) -> Dict[str, Any]:
    """
    Call Serper API with retry logic.

    Args:
        query: Search query
        num_results: Maximum number of results
        recency_days: Filter to results from last N days (optional)
        sites: Limit to specific sites (optional)
        blocked_sites: Exclude specific sites (optional)

    Returns:
        Serper API response as dict

    Raises:
        httpx.HTTPStatusError: If API returns error status
        httpx.TimeoutException: If request times out
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError(
            "SERPER_API_KEY not found in environment. "
            "Please add it to my_agent/.env file."
        )

    # Rate limiting
    serper_rate_limiter.wait_if_needed()

    # Build query with site operators
    modified_query = query

    if sites:
        # Add site: operators (OR logic)
        site_filter = " OR ".join([f"site:{site}" for site in sites])
        modified_query = f"{query} ({site_filter})"

    if blocked_sites:
        # Add -site: operators
        block_filter = " ".join([f"-site:{site}" for site in blocked_sites])
        modified_query = f"{modified_query} {block_filter}"

    # Prepare Serper request
    payload = {
        "q": modified_query,
        "num": num_results,
        "gl": "us",  # Geographic location
        "hl": "en"   # Language
    }

    # Add recency filter if specified
    if recency_days is not None:
        # Serper date range format: "d" (day), "w" (week), "m" (month), "y" (year)
        if recency_days <= 1:
            payload["tbs"] = "qdr:d"  # Past day
        elif recency_days <= 7:
            payload["tbs"] = "qdr:w"  # Past week
        elif recency_days <= 30:
            payload["tbs"] = "qdr:m"  # Past month
        elif recency_days <= 365:
            payload["tbs"] = "qdr:y"  # Past year

    client = get_http_client()
    response = client.post(
        "https://google.serper.dev/search",
        json=payload,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
    )

    response.raise_for_status()
    return response.json()


def web_search(
    query: str,
    recency_days: Optional[int] = None,
    sites: Optional[str] = None,
    blocked_sites: Optional[str] = None,
    max_results: int = 10
) -> dict:
    """
    Performs a web search using Serper.dev API and returns ranked results.

    This tool searches the web for information and returns results ranked by
    source quality (government/standards > top journalism > other sources).
    Results include titles, URLs, snippets, and publication dates when available.

    Args:
        query: The search query string
        recency_days: Optional filter to results from last N days (e.g., 7 for past week)
        sites: Optional comma-separated list of domains to search within (e.g., "reuters.com,bloomberg.com")
        blocked_sites: Optional comma-separated list of domains to exclude (e.g., "pinterest.com,reddit.com")
        max_results: Maximum number of results to return (default: 10, max: 10)

    Returns:
        dict: A dictionary containing:
            - results: List of search results, each with:
                - title: Page title
                - link: URL
                - snippet: Brief description/snippet
                - date: Publication date (YYYY-MM-DD format, if available)
                - domain: Source domain
            - query_executed: The actual query executed (may include site operators)
            - num_results: Number of results returned

    Example:
        >>> web_search("latest AI regulations", recency_days=30, max_results=5)
        {
            "results": [
                {
                    "title": "EU AI Act Comes Into Effect",
                    "link": "https://ec.europa.eu/...",
                    "snippet": "New AI regulations...",
                    "date": "2024-01-15",
                    "domain": "ec.europa.eu"
                },
                ...
            ],
            "query_executed": "latest AI regulations",
            "num_results": 5
        }
    """
    start_time = time.time()

    try:
        # Parse site filters
        sites_list = [s.strip() for s in sites.split(",")] if sites else None
        blocked_list = [s.strip() for s in blocked_sites.split(",")] if blocked_sites else None

        # Clamp max_results
        max_results = min(max_results, 10)

        # Call Serper API
        response_data = _call_serper_api(
            query=query,
            num_results=max_results,
            recency_days=recency_days,
            sites=sites_list,
            blocked_sites=blocked_list
        )

        # Extract organic results
        organic_results = response_data.get("organic", [])

        # Transform to our format
        results = []
        for item in organic_results[:max_results]:
            result = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "date": parse_date_to_iso(item.get("date", "")),
                "domain": item.get("domain", "")
            }
            results.append(result)

        # Rank by source quality
        ranked_results = rank_search_results(results)

        # Log search execution
        latency_ms = (time.time() - start_time) * 1000
        logger.log_search_query(query, len(ranked_results), latency_ms)

        return {
            "results": ranked_results,
            "query_executed": query,
            "num_results": len(ranked_results)
        }

    except httpx.HTTPStatusError as e:
        error_msg = f"Serper API error: {e.response.status_code} - {e.response.text}"
        logger.log_event("search_error", {"query": query, "error": error_msg}, level="error")

        return {
            "results": [],
            "query_executed": query,
            "num_results": 0,
            "error": error_msg
        }

    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        logger.log_event("search_error", {"query": query, "error": error_msg}, level="error")

        return {
            "results": [],
            "query_executed": query,
            "num_results": 0,
            "error": error_msg
        }
