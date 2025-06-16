from typing import List, Optional, Dict, Any, Union, TYPE_CHECKING

from .base import ResourceClient
from ..models import Job

if TYPE_CHECKING:
    from ..client import AtomicClient


class AliasPKeyClient(ResourceClient):
    """
    A client for managing aliasable public keys (`alias-pkey`).
    These are named, reusable keys that can be updated in one place.
    """

    def set(self, category: str, name: str, public_key: str) -> Dict[str, Any]:
        """
        Creates or updates an aliasable public key. The address will be in the format:
        `pub://<your-client-id>/<category>?<name>`

        Args:
            category: A category to group keys (e.g., 'developers', 'automation').
            name: A unique name for the key within the category.
            public_key: The full, valid authorized_keys line (e.g., "ssh-ed25519 AAAA...").

        Returns:
            The API response dictionary.
        """
        endpoint = f"/alias-pkey/set/{self._client_id_or_name}/{category}/{name}"
        return self._post(endpoint, data={"pkey": public_key})

    def get(self, category: str, name: str) -> Dict[str, Any]:
        """
        Retrieves a single aliasable public key.

        Args:
            category: The key's category.
            name: The key's name.

        Returns:
            A dictionary containing the key details.
        """
        endpoint = f"/alias-pkey/get/{self._client_id_or_name}/{category}/{name}"
        return self._get(endpoint)

    def list(self, category: str, after: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Enumerates aliasable public keys within a category, 1000 at a time.

        Args:
            category: The category to list keys from.
            after: Optional key ID to begin enumeration after (for pagination).

        Returns:
            A list of key dictionaries.
        """
        endpoint = f"/alias-pkey/list/{self._client_id_or_name}/{category}"
        payload = {"after": after} if after else {}
        return self._post(endpoint, data=payload)

    def remove(self, category: str, name: str) -> Dict[str, Any]:
        """
        Deletes a single aliasable public key.

        Args:
            category: The key's category.
            name: The key's name.
        """
        endpoint = f"/alias-pkey/remove/{self._client_id_or_name}/{category}/{name}"
        return self._get(endpoint) # API uses GET for this action

    def list_categories(self) -> List[str]:
        """
        Enumerates all categories of aliasable keys for your client account.
        """
        endpoint = f"/alias-pkey/categories/{self._client_id_or_name}"
        return self._get(endpoint)


class SSHClient(ResourceClient):
    """
    A client for managing SSH access, users, and keys.
    """
    _client: 'AtomicClient' = None

    def __init__(self, *args, **kwargs):
        """Initializes the SSHClient and its sub-clients."""
        super().__init__(*args, **kwargs)
        # Attach the AliasPKeyClient as a sub-client
        self.alias_pkey = AliasPKeyClient(*args, **kwargs)

    # --- Site-Specific SSH User Management ---

    def list_users(self, site_id: Optional[int] = None, domain: Optional[str] = None) -> List[str]:
        """
        Lists SSH/SFTP users for a specific site.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A list of usernames.
        """
        service, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/ssh-user/{service}/{identifier}/list"
        return self._get(endpoint)

    def add_user(
        self,
        username: str,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        public_key: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Adds an SSH/SFTP user to a site.

        Args:
            username: The username to create.
            site_id: The Atomic site ID.
            domain: The domain name of the site.
            public_key: The user's authorized_keys line.
            password: The user's password. If omitted, a random one is generated.
                      If set to an empty string, password login is disabled.

        Returns:
            A dictionary containing the user and redacted password info.
        """
        service, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/ssh-user/{service}/{identifier}/add"

        payload = {"user": username}
        if public_key is not None:
            payload['pkey'] = public_key
        if password is not None:
            payload['pass'] = password

        return self._post(endpoint, data=payload)

    def remove_user(self, username: str, site_id: Optional[int] = None, domain: Optional[str] = None) -> Dict:
        """
        Removes an SSH/SFTP user from a site.

        Args:
            username: The username to remove.
            site_id: The Atomic site ID.
            domain: The domain name of the site.
        """
        service, identifier = self._get_service_and_identifier(site_id, domain)
        # This endpoint uses GET in the docs, which is unusual for a destructive action.
        # We will wrap it in a `_post` or similar if the API changes, but for now, follow docs.
        endpoint = f"/ssh-user/{service}/{identifier}/remove/{username}"
        return self._get(endpoint)

    def update_user(
        self,
        username: str,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        public_key: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict:
        """
        Updates an SSH/SFTP user's public key or password.

        Args:
            username: The username to update.
            site_id: The Atomic site ID.
            domain: The domain name of the site.
            public_key: The new authorized_keys line.
            password: The new password.
        """
        service, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/ssh-user/{service}/{identifier}/update/{username}"

        payload = {}
        if public_key is not None:
            payload['pkey'] = public_key
        if password is not None:
            payload['pass'] = password

        return self._post(endpoint, data=payload)

    def disconnect_all_users(self, site_id: Optional[int] = None, domain: Optional[str] = None) -> Job:
        """
        Queues a job to disconnect all active SSH/SFTP sessions for a site.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A Job object for the asynchronous task.
        """
        service, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/ssh-disconnect-all-users/{service}/{identifier}"
        response_data = self._get(endpoint)

        job = Job.parse_obj(response_data)
        job._client = self._client
        return job

    # --- Client-Wide (Host) SSH Key Management ---
    def list_client_keys(self) -> List[Dict[str, Any]]:
        """
        Lists authorized keys for the Client Service (`client-ssh.atomicsites.net`).
        These keys can access ALL sites on the client account.

        Returns:
            A list of key ID strings.
        """
        endpoint = f"/client-authorized-keys/{self._client_id_or_name}/list"
        return self._get(endpoint)

    def add_client_key(self, key_line: str, name: str) -> Dict:
        """
        Adds an authorized key for the Client Service.
        Connection format is: `<atomic_site_id>@client-ssh.atomicsites.net`.
        It is highly recommended to include a `from="..."` restriction in the key line.

        Args:
            key_line: The full authorized_keys line, preferably with a `from` restriction.
            name: A descriptive name for the key (e.g., 'CI/CD Automation Key').
        Returns:
            A dictionary containing the 'id' of the newly created key.
        """
        endpoint = f"/client-authorized-keys/{self._client_id_or_name}/add"
        payload = {"authorized_keys_line": key_line, "name": name}
        return self._post(endpoint, data=payload)

    def remove_client_key(self, key_id: Union[int, str]) -> Dict:
        """
        Removes a client-wide authorized key.

        Args:
            key_id: The ID of the key to remove.
        """
        endpoint = f"/client-authorized-keys/{self._client_id_or_name}/remove/{key_id}"
        # The API docs show GET for this, which we will follow.
        return self._get(endpoint)
