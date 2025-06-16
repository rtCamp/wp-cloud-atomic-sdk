import os
import time
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError
from atomic_sdk.models import Task

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

def main():
    """
    Demonstrates creating and monitoring a bulk 'software' task to install
    and activate a plugin across all client sites.
    """
    if not API_KEY or not CLIENT_ID:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    task_id = None

    try:
        # --- 1. Define the software task ---
        # This will install and activate the Hello Dolly plugin on all sites.
        software_actions = {"plugins/hello-dolly/latest": "activate"}

        print("\n--- [1/2] Creating a bulk software task ---")
        print(f"  - Action: Install and Activate 'hello-dolly' on all sites for client '{CLIENT_ID}'.")

        task_request: Task = client.tasks.create(
            task_type="software",
            software_actions=software_actions,
            send_webhook_for="failure" # Optional: get notified on failures
        )
        task_id = task_request.task_id
        print(f"  - ✅ Task created successfully with ID: {task_id}")

        # --- 2. Monitor the task's progress ---
        print(f"\n--- [2/2] Monitoring progress for task {task_id} ---")
        while True:
            task_status: Task = client.tasks.get(task_id=task_id)
            meta = task_status.meta
            print(f"  - Progress: {meta.get('success_count', 0)} succeeded, {meta.get('failure_count', 0)} failed.")

            if task_status.complete:
                print("\n  - ✅ Task finished!")
                print(f"  - Final Status: {meta.get('success_count')} succeeded, {meta.get('failure_count')} failed.")
                print(f"  - Total time taken: {meta.get('took')} ms")
                break

            print("  - Task is still running. Checking again in 5 seconds...")
            time.sleep(5)

    except AtomicAPIError as e:
        print(f"\nAn API error occurred: {e}")

if __name__ == "__main__":
    main()
