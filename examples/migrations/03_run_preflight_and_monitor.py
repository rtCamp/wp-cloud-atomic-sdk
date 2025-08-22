import os
import time
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
MIGRATION_ID_FILE = "migration_id.txt"

def poll_ticket_status(client, ticket_id):
    """Polls a response ticket until it completes, printing logs on failure."""
    while True:
        summary = client.response_tickets.get_summary(ticket_id=ticket_id)
        status = summary.get("status")
        print(f"  - Polling ticket {ticket_id}... current status: {status}")

        if status in ["success", "failure"]:
            if status == "failure":
                print("\n  - ❌ Preflight failed. Fetching full logs...")
                full_log = client.response_tickets.get_full(ticket_id=ticket_id)
                print("  - " + "="*20 + " BEGIN LOGS " + "="*20)
                print(full_log)
                print("  - " + "="*21 + " END LOGS " + "="*21)
            return status

        time.sleep(20)

def main():
    if not API_KEY or not CLIENT_ID: return
    if not os.path.exists(MIGRATION_ID_FILE):
        print(f"Error: '{MIGRATION_ID_FILE}' not found. Please run the create_migration script first.")
        return

    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    with open(MIGRATION_ID_FILE, "r") as f:
        migration_id = int(f.read().strip())
    print(f"--- Found Migration ID: {migration_id} ---")

    try:
        print(f"\n--- Running preflight checks for migration {migration_id} ---")
        ticket = client.migrations.run_preflight(migration_id=migration_id)
        ticket_id = ticket.response_ticket_id

        final_status = poll_ticket_status(client, ticket_id)

        if final_status == "success":
            print(f"\n✅ Success! Preflight checks passed for migration {migration_id}.")
            print("\n--- NEXT STEP ---")
            print("Run '04_start_migration_and_monitor.py' to begin the actual migration.")
        else:
            print(f"\n❌ Failure. Please review the logs above, update the migration if needed, and re-run this script.")

    except AtomicAPIError as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
