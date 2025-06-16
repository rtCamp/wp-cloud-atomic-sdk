from typing import Optional, Any, Dict

from .base import ResourceClient


class UtilityClient(ResourceClient):
    """
    A client for utility and testing endpoints.
    """

    def test_status(
        self,
        status_code: Optional[int] = 200,
        message: Optional[str] = "OK",
        post_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calls the test-status endpoint to verify API interaction.

        This can be used to test authentication and to simulate specific
        API responses by requesting a certain HTTP status and message.

        Args:
            status_code: The HTTP status code to request in the response. Defaults to 200.
            message: The message to request in the response. Defaults to "OK".
            post_data: Optional dictionary of data to send in a POST request,
                       which will be echoed back in the response. If None, a GET
                       request will be made.

        Returns:
            A dictionary containing the response from the test endpoint.
        """
        endpoint = f"/test-status/{status_code}/{message}"

        if post_data is not None:
            return self._request("POST", endpoint, data=post_data)
        else:
            return self._request("GET", endpoint)
