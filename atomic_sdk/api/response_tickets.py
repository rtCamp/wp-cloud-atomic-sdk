from typing import Dict, Any

from .base import ResourceClient

class ResponseTicketsClient(ResourceClient):
    """
    A client for retrieving the status and logs from response tickets.
    Response tickets are used to monitor asynchronous, multi-step operations
    like site migrations.
    """

    def get_summary(self, ticket_id: str) -> Dict[str, Any]:
        """
        Gets a summary of the response ticket, including its current status.
        The status is of special relevance, being one of "success", "failure", or "running".

        Args:
            ticket_id: The ID of the response ticket (matches "ResponseTicket.response_ticket_id").

        Returns:
            A dictionary containing the summary of the ticket.
        """
        endpoint = f"/response-ticket/get/summary/{ticket_id}"
        return self._get(endpoint)

    def get_full(self, ticket_id: str) -> Dict[str, Any]:
        """
        Gets the full data attached to a response ticket, which may include
        detailed logs and results.

        Args:
            ticket_id: The ID of the response ticket (matches "ResponseTicket.response_ticket_id").

        Returns:
            A dictionary containing the full details of the ticket.
        """
        endpoint = f"/response-ticket/get/full/{ticket_id}"
        return self._get(endpoint)
