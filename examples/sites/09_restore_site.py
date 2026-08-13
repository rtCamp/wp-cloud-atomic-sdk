"""
Example: restore a site from its own filesystem + database backup pair.

WARNING: ``client.sites.restore_site`` is DESTRUCTIVE. The site's current
files and database will be OVERWRITTEN by the selected backups. The site
must first allow restores (``allow_restore`` meta set to a recent unix
timestamp) and be suspended with a 503 status code; this script sets both,
runs the restore, polls the response ticket, then unsuspends the site.

Usage:
    python examples/sites/09_restore_site.py <site_domain>

Or set SITE_DOMAIN in your .env file. Set FS_BACKUP_ID and DB_BACKUP_ID to
restore from specific backups; any ID left unset is resolved to the site's
latest backup of that type.
"""

import os
import sys
import time
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv # type: ignore

from atomic_sdk import AtomicAPIError, AtomicClient

load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")
FS_BACKUP_ID = os.environ.get("FS_BACKUP_ID")
DB_BACKUP_ID = os.environ.get("DB_BACKUP_ID")

CONFIRM_TOKEN = "I-UNDERSTAND-THIS-WILL-OVERWRITE-THE-SITE"

POLL_INTERVAL_SECONDS = 10
POLL_TIMEOUT_SECONDS = 600


def main() -> None:
    if not API_KEY or not CLIENT_ID:
        print("Error: set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        sys.exit(1)

    if len(sys.argv) >= 2:
        domain = sys.argv[1]
    elif SITE_DOMAIN:
        domain = SITE_DOMAIN
    else:
        print("Usage: python examples/sites/09_restore_site.py <site_domain>")
        sys.exit(1)

    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        fs_backup_id = int(FS_BACKUP_ID) if FS_BACKUP_ID else None
        db_backup_id = int(DB_BACKUP_ID) if DB_BACKUP_ID else None
    except ValueError:
        print("Error: FS_BACKUP_ID and DB_BACKUP_ID must be numeric backup IDs.")
        sys.exit(1)

    if fs_backup_id is None or db_backup_id is None:
        print(f"\n--- Listing backups for '{domain}' to resolve the latest pair ---")
        try:
            backups = client.backups.list(domain=domain)
        except AtomicAPIError as exc:
            print(f"❌ API error while listing backups: {exc}")
            sys.exit(1)

        if fs_backup_id is None:
            fs_backups = [b for b in backups if b.type.endswith("fs")]
            if not fs_backups:
                print("Error: no filesystem backups found; set FS_BACKUP_ID or create one first.")
                sys.exit(1)
            latest_fs = max(fs_backups, key=lambda b: b.backup_timestamp)
            fs_backup_id = int(latest_fs.atomic_backup_id)

        if db_backup_id is None:
            db_backups = [b for b in backups if b.type.endswith("db")]
            if not db_backups:
                print("Error: no database backups found; set DB_BACKUP_ID or create one first.")
                sys.exit(1)
            latest_db = max(db_backups, key=lambda b: b.backup_timestamp)
            db_backup_id = int(latest_db.atomic_backup_id)

    print(f"\n  - Filesystem backup ID: {fs_backup_id}")
    print(f"  - Database backup ID:   {db_backup_id}")

    print(f"\n⚠️  This will OVERWRITE the current files and database of '{domain}'")
    print("    with the backups listed above. This action cannot be undone.\n")
    typed = input(f"Type {CONFIRM_TOKEN!r} to continue: ").strip()
    if typed != CONFIRM_TOKEN:
        print("Aborted: confirmation token did not match.")
        sys.exit(1)

    try:
        print("\n--- Allowing restore and suspending the site with a 503 status ---")
        client.sites.update_meta(key="allow_restore", value=int(datetime.now(timezone.utc).timestamp()), domain=domain)
        client.sites.update_meta(key="suspended", value=503, domain=domain)
    except AtomicAPIError as exc:
        print(f"❌ API error before the restore started: {exc}")
        try:
            client.sites.remove_meta(key="suspended", domain=domain)
            print("   The site was unsuspended since no restore ran.")
        except AtomicAPIError as unsuspend_exc:
            print(f"   Could not unsuspend the site, do so manually: {unsuspend_exc}")
        sys.exit(1)

    try:
        print("\n--- Starting the restore ---")
        result = client.sites.restore_site(
            restore_from_fs=fs_backup_id,
            restore_from_db=db_backup_id,
            domain=domain,
        )
    except AtomicAPIError as exc:
        print(f"❌ API error from the restore request: {exc}")
        print("   The restore may still have started; the site remains suspended.")
        print("   Verify the site state before unsuspending it manually.")
        sys.exit(1)

    job_id = result.get("atomic_job_id")
    ticket_id = result.get("response_ticket_id")
    print(f"  - Restore job queued. Job ID: {job_id}, Ticket ID: {ticket_id}")

    try:
        print("\n--- Polling the response ticket until the restore completes ---")
        status = "running"
        deadline = datetime.now(timezone.utc) + timedelta(seconds=POLL_TIMEOUT_SECONDS)
        while status == "running" and datetime.now(timezone.utc) < deadline:
            time.sleep(POLL_INTERVAL_SECONDS)
            summary = client.response_tickets.get_summary(ticket_id)
            if not summary:
                print("  - Ticket has no entries yet; restore still in progress.")
                continue
            status = summary.get("status", "running")
            print(f"  - Ticket status: {status}")

        if status == "success":
            print("\n--- Unsuspending the site ---")
            client.sites.remove_meta(key="suspended", domain=domain)
            print(f"✅ '{domain}' was restored and is back online.")
        elif status == "failure":
            print(f"❌ Restore failed. Inspect the full ticket with client.response_tickets.get_full({ticket_id!r}).")
            print("   The site is still suspended; unsuspend it manually once resolved.")
            sys.exit(1)
        else:
            print(f"⚠️  Restore still running after {POLL_TIMEOUT_SECONDS}s. Keep polling ticket {ticket_id!r}.")
            print("   The site remains suspended until the restore finishes.")
    except AtomicAPIError as exc:
        print(f"❌ API error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
