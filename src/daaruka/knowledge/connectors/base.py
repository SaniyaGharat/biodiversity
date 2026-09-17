"""Base HTTP client with timeouts, retry policies, and error handling."""

import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class BaseConnector:
    """Base HTTP client for environmental and geospatial REST APIs."""

    def __init__(self, base_url: str, timeout: float = 15.0, max_retries: int = 2):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    async def get_json(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Perform asynchronous GET request returning JSON with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        transport = httpx.AsyncHTTPTransport(retries=self.max_retries)
        async with httpx.AsyncClient(timeout=self.timeout, transport=transport) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} requesting {url}: {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Network request error accessing {url}: {str(e)}")
                raise

    def get_json_sync(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Perform synchronous GET request returning JSON with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        transport = httpx.HTTPTransport(retries=self.max_retries)
        with httpx.Client(timeout=self.timeout, transport=transport) as client:
            try:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} requesting {url}: {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Network request error accessing {url}: {str(e)}")
                raise
