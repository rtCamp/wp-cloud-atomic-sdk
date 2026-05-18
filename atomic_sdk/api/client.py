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
        Updates a metadata value for the client account.

        This method calls the API's ``update`` operation and preserves the
        SDK's existing update/overwrite behavior. Use :meth:`add_meta` when
        you specifically want the API's create-if-absent semantics.

        Args:
            key: The metadata key to set (e.g., 'webhook_url').
            value: The new value for the key.

        Returns:
            The raw response from the API, typically an empty dictionary.
        """
        endpoint = f"/client-meta/{self._client_id_or_name}/{key}/update"
        return self._post(endpoint, data={"value": value})

    def add_meta(self, key: str, value: str) -> dict:
        """
        Adds a new metadata value for the client account.

        This method calls the API's ``add`` operation for callers that want
        the create/add API verb. Use :meth:`set_meta` when you explicitly want
        the API's update/overwrite operation.

        Args:
            key: The metadata key to add (e.g., 'webhook_url').
            value: The value for the new key.

        Returns:
            The raw response from the API, typically an empty dictionary.
        """
        endpoint = f"/client-meta/{self._client_id_or_name}/{key}/add"
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
