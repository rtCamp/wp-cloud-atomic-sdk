import requests
from typing import Optional, Tuple, Union

from ..exceptions import AtomicAPIError, InvalidRequestError, NotFoundError, ServerError


class ResourceClient:
    """A base client for a group of API resources."""

    def __init__(self, session: requests.Session, base_url: str, client_id_or_name: str):
        """
        Initializes the ResourceClient.

        Args:
            session: A requests.Session object configured with authentication.
            base_url: The base URL for the Atomic API.
            client_id_or_name: The client's identifier (name or ID).
        """
        self._session = session
        self._base_url = base_url
        self._client_id_or_name = client_id_or_name

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

    def _post(self, endpoint: str, data: Optional[dict] = None, json: Optional[dict] = None) -> dict:
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
        try:
            response = self._session.get(url, params=params, timeout=300) # Longer timeout for downloads
            response.raise_for_status()
            return response.content
        except requests.exceptions.HTTPError as e:
            # Re-raise with a more specific custom exception if needed
            raise AtomicAPIError(f"HTTP Error for {url}: {e.response.status_code} {e.response.text}") from e
        except requests.exceptions.RequestException as e:
            raise AtomicAPIError(f"Request failed for {url}: {e}") from e

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
        try:
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            try:
                error_data = e.response.json()
                message = error_data.get("message", e.response.text)
            except requests.exceptions.JSONDecodeError:
                message = e.response.text

            # Raise the correct specific exception based on status code.
            if status_code == 404:
                raise NotFoundError(message, status_code) from e
            if 400 <= status_code < 500:
                raise InvalidRequestError(message, status_code) from e
            if 500 <= status_code < 600:
                raise ServerError(message, status_code) from e

            # Fallback for any other HTTP error
            raise AtomicAPIError(message, status_code) from e

        except requests.exceptions.RequestException as e:
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
