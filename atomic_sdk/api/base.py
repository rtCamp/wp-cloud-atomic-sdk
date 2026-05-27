import logging
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterator, Optional, Tuple, Union

import requests

from ..exceptions import AtomicAPIError, ConflictError, InvalidRequestError, NotFoundError, RateLimitError, ServerError


logger = logging.getLogger("atomic_sdk.retry")


RETRYABLE_REQUEST_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


class ResourceClient:
    """A base client for a group of API resources."""

    def __init__(
        self,
        session: requests.Session,
        base_url: str,
        client_id_or_name: str,
        max_retries: int = 3,
        backoff_base: float = 0.5,
    ):
        """
        Initializes the ResourceClient.

        Args:
            session: A requests.Session object configured with authentication.
            base_url: The base URL for the Atomic API.
            client_id_or_name: The client's identifier (name or ID).
            max_retries: Number of retries for 429, 5xx, and connection errors.
            backoff_base: Base delay in seconds for exponential backoff with jitter.
        """
        self._session = session
        self._base_url = base_url
        self._client_id_or_name = client_id_or_name
        self._max_retries = max_retries
        self._backoff_base = backoff_base

    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        Performs a GET request and handles the response.

        Args:
            endpoint: The API endpoint to request (e.g., '/get-sites/client-name').
            params: Optional dictionary of query parameters.

        Returns:
            The 'data' field from the JSON response.
        """
        response = self._request("GET", endpoint, params=params)
        return response.get("data", {})

    def _post(self, endpoint: str, data: Optional[dict | list[tuple[str, str]]] = None, json: Optional[dict] = None) -> dict:
        """
        Performs a POST request and handles the response.

        Args:
            endpoint: The API endpoint to request.
            data: Optional dictionary for form-encoded data.
            json: Optional dictionary for JSON-encoded data.

        Returns:
            The 'data' field from the JSON response.
        """
        response = self._request("POST", endpoint, data=data, json=json)
        return response.get("data", {})

    def _get_raw(self, endpoint: str, params: Optional[dict] = None) -> bytes:
        """
        Performs a GET request and returns the raw byte content.

        Args:
            endpoint: The API endpoint to request.
            params: Optional dictionary of query parameters.

        Returns:
            The raw response content as bytes.
        """
        url = self._base_url.rstrip('/') + endpoint
        attempt = 0
        while True:
            try:
                response = self._session.get(url, params=params, timeout=300) # Longer timeout for downloads
                response.raise_for_status()
                break
            except requests.exceptions.HTTPError as e:
                if self._retry_http_error(e, attempt):
                    attempt += 1
                    continue
                self._raise_for_http_error(e)
            except requests.exceptions.RequestException as e:
                if self._retry_request_exception(e, url, attempt):
                    attempt += 1
                    continue
                raise AtomicAPIError(f"Request failed for {url}: {e}") from e

        try:
            return response.content
        except requests.exceptions.RequestException as e:
            raise AtomicAPIError(f"Request failed for {url}: {e}") from e

    def _get_stream(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        *,
        chunk_size: int = 1 << 20,
        timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> Iterator[bytes]:
        """
        Performs a streaming GET request and yields raw byte chunks.

        Consumers must iterate the returned generator to completion, or close it,
        so the underlying HTTP connection can be released.

        Args:
            endpoint: The API endpoint to request.
            params: Optional dictionary of query parameters.
            chunk_size: Maximum chunk size yielded by requests.
            timeout: Optional request timeout passed through to requests.

        Yields:
            Raw response bytes.

        Raises:
            AtomicAPIError: For connection errors or non-2xx responses.
            NotFoundError: For 404 responses.
            InvalidRequestError: For other 4xx responses.
            ServerError: For 5xx responses.
        """
        url = self._base_url.rstrip('/') + endpoint
        try:
            with self._session.get(url, params=params, stream=True, timeout=timeout) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        yield chunk

        except requests.exceptions.HTTPError as e:
            self._raise_for_http_error(e)

        except requests.exceptions.RequestException as e:
            raise AtomicAPIError(f"Request failed for {url}: {e}") from e

    def _raise_for_http_error(self, error: requests.exceptions.HTTPError) -> None:
        """Translate a requests HTTPError into the SDK's public exceptions."""
        status_code = error.response.status_code
        try:
            error_data = error.response.json()
            message = error_data.get("message", error.response.text)
        except requests.exceptions.JSONDecodeError:
            message = error.response.text

        if status_code == 404:
            raise NotFoundError(message, status_code) from error
        if status_code == 429:
            raise RateLimitError(
                message,
                status_code,
                retry_after=self._parse_retry_after(error.response),
            ) from error
        if status_code == 409:
            raise ConflictError(message, status_code) from error
        if 400 <= status_code < 500:
            raise InvalidRequestError(message, status_code) from error
        if 500 <= status_code < 600:
            raise ServerError(message, status_code) from error

        raise AtomicAPIError(message, status_code) from error

    @staticmethod
    def _parse_retry_after(response: requests.Response) -> Optional[int]:
        """Parse a Retry-After header as seconds, or as an HTTP-date."""
        value = response.headers.get("Retry-After")
        if not value:
            return None

        try:
            return max(0, int(float(value)))
        except ValueError:
            pass

        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0, int((retry_at - datetime.now(timezone.utc)).total_seconds()))

    def _retry_http_error(self, error: requests.exceptions.HTTPError, attempt: int) -> bool:
        """Sleep and return True when an HTTP error should be retried."""
        status_code = error.response.status_code
        if status_code != 429 and not 500 <= status_code < 600:
            return False
        if attempt >= self._max_retries:
            return False

        retry_after = self._parse_retry_after(error.response) if status_code == 429 else None
        delay = retry_after if retry_after is not None else self._backoff_delay(attempt)

        if status_code == 429 and retry_after is not None:
            logger.warning(
                "429 Retry-After=%ss, retrying (attempt %s/%s)",
                retry_after,
                attempt + 1,
                self._max_retries,
            )
        else:
            logger.warning(
                "%s %s, backing off %.2fs (attempt %s/%s)",
                status_code,
                error.response.reason,
                delay,
                attempt + 1,
                self._max_retries,
            )
        time.sleep(delay)
        return True

    def _retry_request_exception(self, error: requests.exceptions.RequestException, url: str, attempt: int) -> bool:
        """Sleep and return True when a connection-level request error should be retried."""
        if not self._is_retryable_request_exception(error):
            return False
        if attempt >= self._max_retries:
            return False

        delay = self._backoff_delay(attempt)
        logger.warning(
            "Request failed for %s: %s, backing off %.2fs (attempt %s/%s)",
            url,
            error,
            delay,
            attempt + 1,
            self._max_retries,
        )
        time.sleep(delay)
        return True

    @staticmethod
    def _is_retryable_request_exception(error: requests.exceptions.RequestException) -> bool:
        return (
            type(error) is requests.exceptions.ConnectionError
            or isinstance(error, RETRYABLE_REQUEST_EXCEPTIONS)
        )

    def _backoff_delay(self, attempt: int) -> float:
        return random.uniform(0, self._backoff_base * (2 ** attempt))

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Makes an HTTP request to the specified endpoint and handles JSON response.

        Args:
            method: The HTTP method (e.g., 'GET', 'POST').
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to requests.request.

        Returns:
            The 'data' part of the API's JSON response.

        Raises:
            AtomicAPIError: For connection errors or non-2xx responses.
            InvalidRequestError: For 4xx client errors with a message.
        """
        url = self._base_url.rstrip('/') + endpoint
        attempt = 0
        while True:
            try:
                response = self._session.request(method, url, **kwargs)
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
                return response.json()

            except requests.exceptions.HTTPError as e:
                if self._retry_http_error(e, attempt):
                    attempt += 1
                    continue
                self._raise_for_http_error(e)

            except requests.exceptions.RequestException as e:
                if self._retry_request_exception(e, url, attempt):
                    attempt += 1
                    continue
                raise AtomicAPIError(f"Request failed for {url}: {e}") from e

    def _get_service_and_identifier(self, site_id: Optional[int], domain: Optional[str]) -> Tuple[str, Union[int, str]]:
        """
        Determines the correct service and identifier for site-based endpoints.

        The API uses a flexible pattern like `/endpoint/:service/:identifier/` where
        the service is either 'domain' (if looking up by domain) or the client's name
        (if looking up by Atomic site ID). This helper centralizes that logic.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A tuple of (service, identifier).

        Raises:
            ValueError: If neither site_id nor domain is provided.
        """
        if domain:
            return "domain", domain
        if site_id:
            return self._client_id_or_name, site_id

        raise ValueError("You must provide either a 'site_id' or a 'domain'.")
