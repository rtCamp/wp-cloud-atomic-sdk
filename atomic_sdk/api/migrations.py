from typing import Optional, Dict, Any, Union

from .base import ResourceClient
from ..models import Migration, MigrationCreationResponse, ResponseTicket

class MigrationsClient(ResourceClient):
    """
    A client for managing site migrations from a remote host to WP Cloud.
    """

    def create(
        self,
        remote_host: str,
        remote_user: str,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        remote_pass: Optional[str] = None,
        remote_domain: Optional[str] = None,
        ssh_id: Optional[str] = None,
        ssh_id_pass: Optional[str] = None,
    ) -> MigrationCreationResponse:
        """
        Initiates a new site migration for a destination site on WP Cloud.

        Args:
            remote_host: The hostname/IP of the source server to connect to via SSH.
            remote_user: The username for SSH authentication on the source server.
            site_id: The Atomic site ID of the destination site.
            domain: The domain of the destination site.
            remote_pass: Password for SSH authentication (if not using a key).
            remote_domain: The domain of the source site, if different from the destination.
            ssh_id: The private SSH key (identity file content) for authentication.
            ssh_id_pass: The passphrase for the private SSH key, if encrypted.

        Returns:
            A MigrationCreationResponse object containing the new migration_id and
            potentially a public key to install on the source server.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/migration/create/{identifier}"

        payload = {
            "remote-host": remote_host,
            "remote-user": remote_user,
        }
        if remote_pass: payload["remote-pass"] = remote_pass
        if remote_domain: payload["remote-domain"] = remote_domain
        if ssh_id: payload["ssh-id"] = ssh_id
        if ssh_id_pass: payload["ssh-id-pass"] = ssh_id_pass

        response_data = self._post(endpoint, data=payload)
        return MigrationCreationResponse.parse_obj(response_data)

    def get(self, migration_id: int) -> Migration:
        """
        Retrieves the details of a specific migration.
        Sensitive details like passwords and keys will be redacted.

        Args:
            migration_id: The ID of the migration to retrieve.

        Returns:
            A Migration object with the migration's details.
        """
        endpoint = f"/migration/get/{migration_id}"
        response_data = self._get(endpoint)
        return Migration.parse_obj(response_data)

    def update(self, migration_id: int, **kwargs: Any) -> Dict[str, Any]:
        """
        Updates the details for an existing migration.
        A migration cannot be updated while it is actively running.

        Args:
            migration_id: The ID of the migration to update.
            **kwargs: Optional fields to update, such as:
                - `remote_host` (str)
                - `remote_user` (str)
                - `remote_pass` (str)
                - `remote_domain` (str)
                - `ssh_id` (str)
                - `ssh_id_pass` (str)

        Returns:
            The raw response from the API.
        """
        endpoint = f"/migration/update/{migration_id}"
        # Rename kwargs to match the API's expected snake-case-with-hyphens
        payload = {key.replace('_', '-'): value for key, value in kwargs.items()}
        return self._post(endpoint, data=payload)

    def run_preflight(self, migration_id: int) -> ResponseTicket:
        """
        Initiates preflight checks on a migration to validate settings.

        Args:
            migration_id: The ID of the migration to check.

        Returns:
            A ResponseTicket object containing the ID for monitoring the check.
        """
        endpoint = f"/migration/preflight/{migration_id}"
        response_data = self._get(endpoint)
        return ResponseTicket.parse_obj(response_data)

    def set_ready(self, migration_id: int) -> ResponseTicket:
        """
        Sets a migration's status to 'ready', signaling it can proceed with the actual migration.

        Args:
            migration_id: The ID of the migration to start.

        Returns:
            A ResponseTicket object containing the ID for monitoring the migration.
        """
        endpoint = f"/migration/ready/{migration_id}"
        response_data = self._get(endpoint)
        return ResponseTicket.parse_obj(response_data)
