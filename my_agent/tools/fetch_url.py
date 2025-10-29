"""URL content fetching tool using Trafilatura."""
import time
from typing import Dict, Any
import httpx

try:
    import trafilatura
except ImportError:
    trafilatura = None

from my_agent.utils.http_client import get_http_client, retry_with_backoff, fetch_rate_limiter
from my_agent.utils.logger import get_structured_logger

logger = get_structured_logger(__name__)


@retry_with_backoff(max_retries=2, base_delay=0.5)
def _fetch_url_content(url: str) -> tuple[str, int]:
    """
    Fetch URL content with retry logic.

    Args:
        url: URL to fetch

    Returns:
        Tuple of (html_content, status_code)

    Raises:
        httpx.HTTPStatusError: If request fails
    """
    # Rate limiting
    fetch_rate_limiter.wait_if_needed()

    client = get_http_client()
    response = client.get(url, timeout=20.0)
    response.raise_for_status()

    return response.text, response.status_code


def fetch_url(url: str) -> dict:
    """
    Fetches and extracts clean text content from a URL.

    This tool downloads a web page and extracts the main content (article text,
    publication date, author, etc.) while removing navigation, ads, and boilerplate.
    Uses Trafilatura for high-accuracy content extraction (95.8% F1 score).

    Args:
        url: The URL to fetch and extract content from

    Returns:
        dict: A dictionary containing:
            - url: The fetched URL
            - title: Page title (if available)
            - text: Extracted main text content
            - date: Publication date (if available)
            - author: Author name (if available)
            - success: Boolean indicating if fetch succeeded
            - error: Error message (if failed)
            - status_code: HTTP status code

    Example:
        >>> fetch_url("https://reuters.com/article/...")
        {
            "url": "https://reuters.com/article/...",
            "title": "Breaking News Title",
            "text": "Full article text content...",
            "date": "2024-01-15",
            "author": "John Doe",
            "success": True,
            "status_code": 200
        }
    """
    start_time = time.time()

    try:
        # Check if trafilatura is available
        if trafilatura is None:
            raise ImportError(
                "trafilatura package not installed. "
                "Install with: uv add trafilatura"
            )

        # Fetch URL content
        html_content, status_code = _fetch_url_content(url)

        # Extract content using Trafilatura
        # extract() returns clean text
        # metadata includes date, author, title
        extracted_text = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=False,
            no_fallback=False
        )

        # Extract metadata
        metadata = trafilatura.extract_metadata(html_content)

        # Build result
        result = {
            "url": url,
            "title": metadata.title if metadata and metadata.title else "",
            "text": extracted_text or "",
            "date": metadata.date if metadata and metadata.date else "",
            "author": metadata.author if metadata and metadata.author else "",
            "success": True,
            "status_code": status_code
        }

        # Log successful fetch
        latency_ms = (time.time() - start_time) * 1000
        logger.log_url_fetch(url, True, status_code, latency_ms)

        return result

    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_msg = ""

        # Detect paywalls and access errors
        if status_code == 403:
            error_msg = "Access forbidden (possibly paywall or blocked)"
        elif status_code == 404:
            error_msg = "Page not found"
        elif status_code == 429:
            error_msg = "Rate limited"
        elif status_code >= 500:
            error_msg = f"Server error ({status_code})"
        else:
            error_msg = f"HTTP error {status_code}"

        latency_ms = (time.time() - start_time) * 1000
        logger.log_url_fetch(url, False, status_code, latency_ms, error_msg)

        return {
            "url": url,
            "title": "",
            "text": "",
            "date": "",
            "author": "",
            "success": False,
            "status_code": status_code,
            "error": error_msg
        }

    except httpx.TimeoutException:
        error_msg = "Request timeout"
        latency_ms = (time.time() - start_time) * 1000
        logger.log_url_fetch(url, False, 0, latency_ms, error_msg)

        return {
            "url": url,
            "title": "",
            "text": "",
            "date": "",
            "author": "",
            "success": False,
            "status_code": 0,
            "error": error_msg
        }

    except Exception as e:
        error_msg = f"Fetch failed: {str(e)}"
        latency_ms = (time.time() - start_time) * 1000
        logger.log_url_fetch(url, False, 0, latency_ms, error_msg)

        return {
            "url": url,
            "title": "",
            "text": "",
            "date": "",
            "author": "",
            "success": False,
            "status_code": 0,
            "error": error_msg
        }
