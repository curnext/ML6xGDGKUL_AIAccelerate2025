"""HTTP client with connection pooling, retry logic, and rate limiting."""
import time
import httpx
from typing import Optional
from functools import wraps

# Global HTTP client for connection pooling
_http_client: Optional[httpx.Client] = None


def get_http_client() -> httpx.Client:
    """Get or create the global HTTP client with connection pooling."""
    global _http_client

    if _http_client is None:
        _http_client = httpx.Client(
            timeout=httpx.Timeout(20.0, connect=10.0),  # Reduced from 30s to 20s for faster failures
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    return _http_client


def close_http_client():
    """Close the global HTTP client."""
    global _http_client
    if _http_client is not None:
        _http_client.close()
        _http_client = None


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for retry logic with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                    continue
                except httpx.HTTPStatusError as e:
                    # Don't retry 4xx errors (except 429 rate limit)
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        raise
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                    continue

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0.0

    def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()


# Global rate limiters
serper_rate_limiter = RateLimiter(requests_per_minute=60)  # Serper limit
fetch_rate_limiter = RateLimiter(requests_per_minute=60)  # Conservative fetch limit
