import os
import time
from typing import Dict, Optional
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError
from atomic_sdk.models import Task, TaskCreationResponse

# --- Configuration ---
load_dotenv()
API_KEY: Optional[str] = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID: Optional[str] = os.environ.get("ATOMIC_CLIENT_ID")

# Search for recently added hello-dolly plugin file
FILE_PATTERN_TO_FIND: str = "wp-content/plugins/hello-dolly/hello.php"

def main() -> None:
    """
    Demonstrates creating and monitoring a bulk 'site-find-files' task using
    the dedicated `tasks.create_find_files()` method.
    """
    if not API_KEY or not CLIENT_ID:
        return
    client: AtomicClient = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    task_id: Optional[int] = None

    try:
        print("\n--- [1/2] Creating a bulk file search task ---")
        print(f"  - Searching for pattern: '{FILE_PATTERN_TO_FIND}'")

        task_request: TaskCreationResponse = client.tasks.create_find_files(
            file_pattern=FILE_PATTERN_TO_FIND,
        )
        task_id = task_request.task_id
        print(f"  - ✅ Task created successfully with ID: {task_id}")

        print(f"\n--- [2/2] Monitoring progress for task {task_id} ---")
        while True:
            task_status: Task = client.tasks.get(task_id=task_id)
            meta: Dict = task_status.meta
            print(f"  - Progress: {meta.get('success_count', 0)} sites checked, {meta.get('failure_count', 0)} failed.")

            if task_status.complete:
                print("\n  - ✅ Task finished!")
                print("  - Note: To see which sites matched the pattern, you would need to check")
                print("    the webhook notifications if `send_webhook_for` was configured.")
                break

            print("  - Task is still running. Checking again in 5 seconds...")
            time.sleep(5)

    except AtomicAPIError as e:
        print(f"\nAn API error occurred: {e}")

if __name__ == "__main__":
    main()
