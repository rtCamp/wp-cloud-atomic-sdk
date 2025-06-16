from typing import Any, Literal

from .base import ResourceClient


class ClientClient(ResourceClient):
    """
    A client for managing client-wide account settings and metadata.
    """

    def get_meta(self, key: str) -> Any:
        """
        Retrieves a metadata value for the client account.

        Args:
            key: The metadata key to retrieve (e.g., 'webhook_url', 'max_space_quota').

        Returns:
            The value of the requested metadata key.
        """
        endpoint = f"/client-meta/{self._client_id_or_name}/{key}/get"
        return self._get(endpoint)

    def set_meta(self, key: str, value: Any) -> dict:
        """
        Sets or updates a metadata value for the client account.
        This method handles both 'add' and 'update' actions.

        Args:
            key: The metadata key to set (e.g., 'webhook_url').
            value: The new value for the key.

        Returns:
            The raw response from the API, typically an empty dictionary.
        """
        # The API uses 'add' for new keys and 'update' for existing ones.
        # For simplicity, we can try 'update' first and fall back to 'add',
        # or just abstract it away. The documentation implies 'update' can
        # also create, so we'll use that.
        endpoint = f"/client-meta/{self._client_id_or_name}/{key}/update"
        return self._post(endpoint, data={"value": value})

    def remove_meta(self, key: str) -> dict:
        """
        Removes a metadata value from the client account.

        Args:
            key: The metadata key to remove (e.g., 'webhook_url').

        Returns:
            The raw response from the API, typically an empty dictionary.
        """
        endpoint = f"/client-meta/{self._client_id_or_name}/{key}/remove"
        # This endpoint uses GET in the docs for a remove action.
        return self._get(endpoint)
