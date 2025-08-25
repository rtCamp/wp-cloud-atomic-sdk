import os
import time
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
MIGRATION_ID_FILE = "migration_id.txt"

def poll_migration_status(client, migration_id):
    """Polls migration status until preflight completes, printing logs on failure."""

    if isinstance(migration_id, str):
        migration_id = int(migration_id)
    while True:
        migration_response = client.migrations.get(migration_id)

        # Access state directly from the Migration object
        state = migration_response.state
        print(f"⏳ Migration state: {state}")
        print(f"  - Polling migration {migration_id}... current state: {state}")

        if state == "preflight-succeeded":
            return "success"
        elif state == "preflight-failed":
            return "failure"

        time.sleep(10)

def main():
    if not API_KEY or not CLIENT_ID: return
    if not os.path.exists(MIGRATION_ID_FILE):
        print(f"Error: '{MIGRATION_ID_FILE}' not found. Please run the create_migration script first.")
        return

    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    with open(MIGRATION_ID_FILE, "r") as f:
        migration_id = int(f.read().strip())
    print(f"🔎 Found Migration ID: {migration_id}")

    try:
        print(f"🧪 Running preflight checks for migration {migration_id}...")
        ticket = client.migrations.run_preflight(migration_id=migration_id)
        print(f"⏳ Preflight started. Monitoring migration {migration_id}...")

        final_status = poll_migration_status(client, migration_id)

        if final_status == "success":
            print(f"\n✅ Success! Preflight checks passed for migration {migration_id}.")
            print("➡️ NEXT STEP:")
            print("Run '04_start_migration_and_monitor.py' to begin the actual migration.")
        else:
            print(f"\n❌ Failure. Please review the details above, update the migration if needed, and re-run this script.")

    except AtomicAPIError as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
