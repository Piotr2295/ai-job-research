"""
Utility helpers for external API calls with retry logic and error handling.

Provides resilient API calls with exponential backoff, timeout handling,
and proper error classification.
"""

import httpx
import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
import asyncio
from app.exceptions import (
    APIAuthenticationError,
    APIRateLimitError,
    APITimeoutError,
    ExternalAPIError,
)

logger = logging.getLogger(__name__)


async def retry_async(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions_to_retry: tuple = (httpx.TimeoutException, httpx.NetworkError),
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions_to_retry: Tuple of exceptions that should trigger retry

    Returns:
        Result from successful function call

    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions_to_retry as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries + 1} attempts failed")

    raise last_exception


async def call_external_api(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    service_name: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
    max_retries: int = 2,
) -> httpx.Response:
    """
    Make a resilient external API call with proper error handling.

    Args:
        client: httpx AsyncClient instance
        method: HTTP method (GET, POST, etc.)
        url: Target URL
        service_name: Name of the service for error messages
        headers: Optional request headers
        params: Optional query parameters
        json_data: Optional JSON body
        timeout: Request timeout in seconds
        max_retries: Number of retry attempts

    Returns:
        httpx.Response object

    Raises:
        APIAuthenticationError: On 401/403 errors
        APIRateLimitError: On 429 errors
        APITimeoutError: On timeout
        ExternalAPIError: On other API errors
    """

    async def make_request():
        return await client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=timeout,
        )

    try:
        # Retry on network/timeout errors
        response = await retry_async(
            make_request,
            max_retries=max_retries,
            exceptions_to_retry=(httpx.TimeoutException, httpx.NetworkError),
        )

        # Handle HTTP error status codes
        if response.status_code == 401 or response.status_code == 403:
            raise APIAuthenticationError(service_name)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise APIRateLimitError(
                service_name,
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code >= 400:
            error_detail = f"Status {response.status_code}"
            try:
                error_body = response.json()
                error_detail += f": {error_body}"
            except Exception:  # noqa: E722
                error_detail += f": {response.text[:200]}"

            raise ExternalAPIError(
                service=service_name,
                message=f"API request failed: {error_detail}",
                status_code=response.status_code,
            )

        return response

    except httpx.TimeoutException:
        logger.error(f"{service_name} API timeout after {timeout}s")
        raise APITimeoutError(service_name, timeout)

    except (APIAuthenticationError, APIRateLimitError, ExternalAPIError):
        # Re-raise our custom exceptions
        raise

    except Exception as exc:
        logger.error(f"Unexpected error calling {service_name} API: {str(exc)}")
        raise ExternalAPIError(
            service=service_name,
            message=f"Unexpected error: {str(exc)}",
        )


async def call_github_api(
    endpoint: str,
    github_token: Optional[str] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """
    Call GitHub API with proper error handling.

    Args:
        endpoint: GitHub API endpoint (e.g., "users/username")
        github_token: Optional GitHub token for authentication
        timeout: Request timeout in seconds

    Returns:
        JSON response as dict
    """
    url = f"https://api.github.com/{endpoint}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    if github_token:
        headers["Authorization"] = f"token {github_token}"

    async with httpx.AsyncClient() as client:
        response = await call_external_api(
            client=client,
            method="GET",
            url=url,
            service_name="GitHub",
            headers=headers,
            timeout=timeout,
            max_retries=2,
        )

        return response.json()


async def call_job_search_api(
    keyword: str,
    location: str = "",
    rapidapi_key: Optional[str] = None,
    limit: int = 5,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """
    Call job search API (JSearch) with proper error handling.

    Args:
        keyword: Job search keyword
        location: Job location
        rapidapi_key: RapidAPI key
        limit: Maximum number of results
        timeout: Request timeout in seconds

    Returns:
        Job search results
    """
    if not rapidapi_key:
        raise ExternalAPIError(
            service="JSearch",
            message="Job search API key not configured",
            status_code=503,
            details={"configuration_required": True},
        )

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    params = {
        "query": f"{keyword} in {location}" if location else keyword,
        "page": "1",
        "num_pages": "1",
    }

    async with httpx.AsyncClient() as client:
        response = await call_external_api(
            client=client,
            method="GET",
            url=url,
            service_name="JSearch",
            headers=headers,
            params=params,
            timeout=timeout,
            max_retries=1,  # Don't retry too much for job search
        )

        return response.json()


def with_error_logging(func):
    """Decorator to add error logging to functions"""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                exc_info=True,
                extra={"function": func.__name__, "args": args, "kwargs": kwargs},
            )
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                exc_info=True,
                extra={"function": func.__name__, "args": args, "kwargs": kwargs},
            )
            raise

    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
