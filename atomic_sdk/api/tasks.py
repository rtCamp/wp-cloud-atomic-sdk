from typing import List, Optional, Dict, Literal, Tuple, TYPE_CHECKING

from typing_extensions import deprecated

from .base import ResourceClient
from ..models import Task, TaskCreationResponse

if TYPE_CHECKING:
    from ..client import AtomicClient


WebhookCondition = Literal["all", "success", "failure", "none"]
TaskType = Literal["software", "site-find-files", "run-wp-cli-command", "wpcloud-scan"]


class TasksClient(ResourceClient):
    """
    A client for managing bulk tasks across multiple sites.
    """

    _client: 'AtomicClient' = None

    @deprecated("Please use the more specific `create_software`, `create_find_files`, or `create_wp_cli` methods instead of `create`.")
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
        return TaskCreationResponse.model_validate(response_data)

    @staticmethod
    def _build_common_payload(
        send_webhook_for: WebhookCondition,
        site_count_limit: Optional[int],
        site_run_list: Optional[List[int]] = None,
    ) -> List[Tuple[str, str]]:
        """
        Builds the list of form-encoded entries that every task-create call needs.

        Args:
            send_webhook_for: Condition for sending webhooks ('all', 'success', 'failure', 'none').
            site_count_limit: Optional max number of sites to run the task on.
            site_run_list: Optional list of site IDs to restrict the task to.
                           Each ID is sent as `site_run_list[]=<id>`.

        Returns:
            A list of (key, value) tuples suitable for form encoding.
        """
        payload: List[Tuple[str, str]] = [("send_webhook_for", send_webhook_for)]
        if site_count_limit is not None:
            payload.append(("site_count_limit", str(site_count_limit)))
        if site_run_list:
            for site_id in site_run_list:
                payload.append(("site_run_list[]", str(site_id)))
        return payload

    def _create_task(
        self,
        task_type: TaskType,
        type_specific_payload: List[Tuple[str, str]],
        send_webhook_for: WebhookCondition,
        site_count_limit: Optional[int],
        site_run_list: Optional[List[int]] = None,
    ) -> TaskCreationResponse:
        """
        Posts a task-create request for the given task type with a pre-built
        type-specific payload. Common params are added here so per-type methods
        only need to encode their own fields.

        Args:
            task_type: The task type slug used in the endpoint URL.
            type_specific_payload: Form entries unique to this task type.
            send_webhook_for: Condition for sending webhooks.
            site_count_limit: Optional max number of sites to run the task on.
            site_run_list: Optional list of site IDs to restrict the task to.

        Returns:
            A TaskCreationResponse with the task ID needed for monitoring.
        """
        payload: List[Tuple[str, str]] = self._build_common_payload(
            send_webhook_for=send_webhook_for,
            site_count_limit=site_count_limit,
            site_run_list=site_run_list,
        )
        payload.extend(type_specific_payload)

        endpoint = f"/task-create/{self._client_id_or_name}/{task_type}"
        response_data = self._post(endpoint, data=payload)
        return TaskCreationResponse.model_validate(response_data)

    def create_software(
        self,
        software_actions: Dict[str, str],
        *,
        site_run_list: Optional[List[int]] = None,
        site_count_limit: Optional[int] = None,
        send_webhook_for: WebhookCondition = "all",
    ) -> TaskCreationResponse:
        """
        Creates a bulk 'software' task that applies plugin/theme actions across
        all client sites.

        Args:
            software_actions: A dictionary of software slugs to actions.
                              e.g., `{"plugins/akismet/latest": "activate"}`.
            site_run_list: Optional list of site IDs to restrict the task to.
                           Each ID is sent as `site_run_list[]=<id>`.
            site_count_limit: Optional max number of sites to run the task on.
            send_webhook_for: Condition for sending webhooks ('all', 'success', 'failure', 'none').

        Returns:
            A TaskCreationResponse with the task ID needed for monitoring.
        """
        if not software_actions:
            raise ValueError("`software_actions` is required.")

        type_payload: List[Tuple[str, str]] = [
            (f"software[{slug}]", action)
            for slug, action in software_actions.items()
        ]
        return self._create_task(
            task_type="software",
            type_specific_payload=type_payload,
            send_webhook_for=send_webhook_for,
            site_count_limit=site_count_limit,
            site_run_list=site_run_list,
        )

    def create_find_files(
        self,
        file_pattern: str,
        *,
        site_run_list: Optional[List[int]] = None,
        site_count_limit: Optional[int] = None,
        send_webhook_for: WebhookCondition = "all",
    ) -> TaskCreationResponse:
        """
        Creates a bulk 'site-find-files' task that searches every client site
        for files matching the given pattern.

        Args:
            file_pattern: The file pattern to search for
                          (e.g., "wp-content/plugins/hello-dolly/hello.php").
            site_run_list: Optional list of site IDs to restrict the task to.
                           Each ID is sent as `site_run_list[]=<id>`.
            site_count_limit: Optional max number of sites to run the task on.
            send_webhook_for: Condition for sending webhooks ('all', 'success', 'failure', 'none').

        Returns:
            A TaskCreationResponse with the task ID needed for monitoring.
        """
        if not file_pattern:
            raise ValueError("`file_pattern` is required.")

        type_payload: List[Tuple[str, str]] = [("pattern", file_pattern)]
        return self._create_task(
            task_type="site-find-files",
            type_specific_payload=type_payload,
            send_webhook_for=send_webhook_for,
            site_count_limit=site_count_limit,
            site_run_list=site_run_list,
        )

    def create_wp_cli(
        self,
        wp_cli_args: List[str],
        *,
        site_run_list: Optional[List[int]] = None,
        site_count_limit: Optional[int] = None,
        send_webhook_for: WebhookCondition = "all",
    ) -> TaskCreationResponse:
        """
        Creates a bulk 'run-wp-cli-command' task that runs a WP-CLI command on
        every client site.

        Args:
            wp_cli_args: A list of arguments for the wp-cli command
                         (e.g., ["plugin", "list", "--format=json"]).
            site_run_list: Optional list of site IDs to restrict the task to.
                           Each ID is sent as `site_run_list[]=<id>`.
            site_count_limit: Optional max number of sites to run the task on.
            send_webhook_for: Condition for sending webhooks ('all', 'success', 'failure', 'none').

        Returns:
            A TaskCreationResponse with the task ID needed for monitoring.
        """
        if not wp_cli_args:
            raise ValueError("`wp_cli_args` is required.")

        type_payload: List[Tuple[str, str]] = [("args[]", arg) for arg in wp_cli_args]
        return self._create_task(
            task_type="run-wp-cli-command",
            type_specific_payload=type_payload,
            send_webhook_for=send_webhook_for,
            site_count_limit=site_count_limit,
            site_run_list=site_run_list,
        )


    def create_wpcloud_scan(
        self,
        scan_type: Literal["wpscan", "pnt-versions"],
        *,
        site_run_list: Optional[List[int]] = None,
        site_count_limit: Optional[int] = None,
        send_webhook_for: WebhookCondition = "all",
    ) -> TaskCreationResponse:
        """
        Creates a bulk 'wpcloud-scan' task that runs a WPCloud scan on
        every client site.

        Args:
            scan_type: The type of WPCloud scan to run ('wpscan' or 'pnt-versions').
            site_run_list: Optional list of site IDs to restrict the task to.
                           Each ID is sent as `site_run_list[]=<id>`.
            site_count_limit: Optional max number of sites to run the task on.
            send_webhook_for: Condition for sending webhooks ('all', 'success', 'failure', 'none').

        Returns:
            A TaskCreationResponse with the task ID needed for monitoring.
        """
        type_payload: List[Tuple[str, str]] = [("scan_type", scan_type)]
        return self._create_task(
            task_type="wpcloud-scan",
            type_specific_payload=type_payload,
            send_webhook_for=send_webhook_for,
            site_count_limit=site_count_limit,
            site_run_list=site_run_list,
        )

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
        return Task.model_validate(response_data)

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
