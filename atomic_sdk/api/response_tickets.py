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
        endpoint = "/response-ticket/get/summary"
        return self._post(endpoint, data={"response-ticket-id": ticket_id})

    def get_full(self, ticket_id: str) -> Dict[str, Any]:
        """
        Gets the full data attached to a response ticket, which may include
        detailed logs and results.

        Args:
            ticket_id: The ID of the response ticket (matches "ResponseTicket.response_ticket_id").

        Returns:
            A dictionary containing the full details of the ticket.
        """
        endpoint = "/response-ticket/get/full"
        return self._post(endpoint, data={"response-ticket-id": ticket_id})

    def get_multi_status(self, ticket_ids: list[str]) -> Dict[str, Any]:
        """
        Gets the status of multiple response tickets in a single request.

        Args:
            ticket_ids: A list of response ticket IDs.

        Returns:
            A dictionary containing the status of multiple tickets.
        """
        endpoint = "/response-ticket/multi-status"
        return self._post(endpoint, data={"response-tickets[]": ticket_ids})