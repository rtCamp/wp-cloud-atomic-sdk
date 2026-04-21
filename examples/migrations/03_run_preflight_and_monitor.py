import os
import time
from dotenv import load_dotenv # type: ignore
from atomic_sdk import AtomicClient, AtomicAPIError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
MIGRATION_ID_FILE = "migration_id.txt"

# Bounded poll: preflight is generally fast (network probe + small SSH check).
POLL_INTERVAL_S = 20
POLL_TIMEOUT_S = 30 * 60   # 30 minutes


def poll_preflight_status(client, migration_id, ticket_id=None):
    """
    Poll the migration's ``state`` until preflight reaches a terminal value.

    Returns one of ``"success"``, ``"failure"`` or ``"timeout"``. On failure,
    the response ticket (if known) is fetched and printed for diagnostics.
    """
    if isinstance(migration_id, str):
        migration_id = int(migration_id)

    deadline = time.monotonic() + POLL_TIMEOUT_S
    last_state = None

    while time.monotonic() < deadline:
        migration = client.migrations.get(migration_id)
        state = migration.state
        if state != last_state:
            print(f"⏳ Migration {migration_id} state: {state}")
            last_state = state

        if state == "preflight-succeeded":
            return "success"
        if state == "preflight-failed":
            _print_failure_logs(client, ticket_id, label="Preflight")
            return "failure"

        time.sleep(POLL_INTERVAL_S)

    print(f"Timed out after {POLL_TIMEOUT_S}s waiting for preflight to finish.")
    _print_failure_logs(client, ticket_id, label="Preflight (timeout)")
    return "timeout"


def _print_failure_logs(client, ticket_id, *, label):
    """Best-effort dump of the response ticket payload to aid debugging."""
    if not ticket_id:
        return
    try:
        full = client.response_tickets.get_full(ticket_id=ticket_id)
    except AtomicAPIError as e:
        print(f"Could not fetch ticket {ticket_id} logs: {e}")
        return
    print(f"\n{label} response ticket {ticket_id} payload:")
    print(full)


def main():
    if not API_KEY or not CLIENT_ID:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your environment (or .env file).")
        return
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
        ticket_id = ticket.response_ticket_id
        print(f"🎫 Response Ticket ID: {ticket_id}")
        print(f"⏳ Preflight started. Monitoring migration {migration_id}...")

        final_status = poll_preflight_status(client, migration_id, ticket_id=ticket_id)

        if final_status == "success":
            print(f"\n✅ Success! Preflight checks passed for migration {migration_id}.")
            print("➡️ NEXT STEP:")
            print("Run '04_start_migration_and_monitor.py' to begin the actual migration.")
        else:
            print(f"\n❌ Preflight ended with status: {final_status}. "
                  "Please review the details above, update the migration if needed, and re-run this script.")

    except AtomicAPIError as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
