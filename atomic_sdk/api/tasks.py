from typing import List, Optional, Dict, Any, Literal, TYPE_CHECKING
from .base import ResourceClient
from ..models import Task, TaskCreationResponse
from ..exceptions import InvalidRequestError

if TYPE_CHECKING:
    from ..client import AtomicClient

class TasksClient(ResourceClient):
    """
    A client for managing bulk tasks across multiple sites.
    """

    _client: 'AtomicClient' = None

    def create(
        self,
        task_type: Literal["software", "site-find-files", "run-wp-cli-command"],
        send_webhook_for: Literal["all", "success", "failure", "none"] = "none",
        software_actions: Optional[Dict[str, str]] = None,
        file_pattern: Optional[str] = None,
        wp_cli_args: Optional[List[str]] = None,
        site_count_limit: Optional[int] = None,
    ) -> TaskCreationResponse:
        """
        Creates a new task to iterate over all client sites.
        Args:
            task_type: The type of task. One of 'software', 'site-find-files',
                       or 'run-wp-cli-command'.
            send_webhook_for: Condition for sending webhooks ('all', 'success', 'failure', 'none').
            software_actions: Required for 'software' tasks. A dictionary of
                              software slugs and actions (e.g., {"plugins/akismet/latest": "activate"}).
            file_pattern: Required for 'site-find-files' tasks. The file pattern to search for.
            wp_cli_args: Required for 'run-wp-cli-command' tasks. A list of arguments
                         for the wp-cli command (e.g., ["db", "size"]).
            site_count_limit: Optional max number of sites to run the task on.

        Returns:
            An object with the task ID needed for monitoring.
        """
        endpoint = f"/task-create/{self._client_id_or_name}/{task_type}"

        payload_list = [("send_webhook_for", send_webhook_for)]
        if site_count_limit:
            payload_list.append(("site_count_limit", str(site_count_limit)))

        if task_type == "software":
            if not software_actions: raise ValueError("`software_actions` is required.")
            for slug, action in software_actions.items():
                payload_list.append((f"software[{slug}]", action))

        elif task_type == "site-find-files":
            if not file_pattern: raise ValueError("`file_pattern` is required.")
            payload_list.append(("pattern", file_pattern))

        elif task_type == "run-wp-cli-command":
            if not wp_cli_args: raise ValueError("`wp_cli_args` is required.")
            for arg in wp_cli_args:
                payload_list.append(("args[]", arg))

        # Send the payload as a list of tuples to ensure correct form encoding
        response_data = self._post(endpoint, data=payload_list)
        return TaskCreationResponse.parse_obj(response_data)

    def get(self, task_id: int) -> Task:
        """
        Retrieves the details and status of a specific task.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            A Task object with its current status and metadata.
        """
        endpoint = f"/task-get/{task_id}"
        response_data = self._post(endpoint)
        return Task.parse_obj(response_data)

    def interrupt(self, task_id: int) -> Dict:
        """
        Interrupts an incomplete task.

        Args:
            task_id: The ID of the task to interrupt.

        Returns:
            The raw response data from the API.
        """
        endpoint = f"/task-interrupt/{task_id}"
        return self._post(endpoint)
