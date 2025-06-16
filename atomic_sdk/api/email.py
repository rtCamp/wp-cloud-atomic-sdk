from typing import List, Dict, Any

from .base import ResourceClient


class EmailClient(ResourceClient):
    """
    A client for retrieving information about email deliverability.
    """

    def list_blocked_domains(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of domains associated with the client that have been
        blocked from sending email via the platform-provided mail service.

        The block type is always 'sasl_block' (domains blocked as a sender).

        Returns:
            A list of dictionaries, where each dictionary represents a
            blocked domain and includes the 'atomic_site_id', 'domain', 'reason',
            and 'expires_on' timestamp.
        """
        endpoint = f"/email-block/{self._client_id_or_name}/list/sasl_block"
        return self._get(endpoint)
