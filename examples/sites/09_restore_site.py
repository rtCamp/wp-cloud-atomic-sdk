"""
Example: restore a site from its own filesystem + database backup pair.

WARNING: ``client.sites.restore_site`` is DESTRUCTIVE. The site's current
files and database will be OVERWRITTEN by the selected backups. The site
must first allow restores (``allow_restore`` meta set to a recent unix
timestamp) and be suspended with a 503 status code; this script sets both,
runs the restore, polls the response ticket, then unsuspends the site.
If the site is already suspended before the run, the script refuses to
proceed so it never clears a suspension it did not set. WP Cloud removes
the ``allow_restore`` meta automatically after a successful restore, so
the script does not need to clean it up.

Usage:
    python examples/sites/09_restore_site.py <site_domain>

Or set SITE_DOMAIN in your .env file. Set FS_BACKUP_ID and DB_BACKUP_ID to
restore from specific backups; any ID left unset is resolved to the site's
latest backup of that type.
"""

import os
import sys
import time

from dotenv import load_dotenv  # type: ignore

from atomic_sdk import AtomicAPIError, AtomicClient, NotFoundError

load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")
FS_BACKUP_ID = os.environ.get("FS_BACKUP_ID")
DB_BACKUP_ID = os.environ.get("DB_BACKUP_ID")

CONFIRM_TOKEN = "I-UNDERSTAND-THIS-WILL-OVERWRITE-THE-SITE"

POLL_INTERVAL_SECONDS = 10
POLL_TIMEOUT_SECONDS = 6 * 60 * 60  # 6 hours
MAX_CONSECUTIVE_POLL_FAILURES = 6  # tolerate ~1 minute of transient API errors
BACKUP_SKEW_WARN_SECONDS = 24 * 60 * 60


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
    for env_id in (fs_backup_id, db_backup_id):
        if env_id is not None and env_id <= 0:
            print("Error: FS_BACKUP_ID and DB_BACKUP_ID must be positive backup IDs.")
            sys.exit(1)

    fs_backup = None
    db_backup = None

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
            fs_backup = max(fs_backups, key=lambda b: b.backup_timestamp)

        if db_backup_id is None:
            db_backups = [b for b in backups if b.type.endswith("db")]
            if not db_backups:
                print("Error: no database backups found; set DB_BACKUP_ID or create one first.")
                sys.exit(1)
            db_backup = max(db_backups, key=lambda b: b.backup_timestamp)

    # IDs supplied via env are verified against the site before anything
    # destructive happens: the backup must exist for this site and be of
    # the expected type.
    try:
        if fs_backup is None:
            fs_backup = client.backups.info(fs_backup_id, domain=domain)
        if db_backup is None:
            db_backup = client.backups.info(db_backup_id, domain=domain)
    except AtomicAPIError as exc:
        print(f"❌ Could not verify the selected backups against '{domain}': {exc}")
        sys.exit(1)

    if not fs_backup.type.endswith("fs"):
        print(f"Error: backup {fs_backup.atomic_backup_id} has type {fs_backup.type!r}; expected a filesystem backup.")
        sys.exit(1)
    if not db_backup.type.endswith("db"):
        print(f"Error: backup {db_backup.atomic_backup_id} has type {db_backup.type!r}; expected a database backup.")
        sys.exit(1)

    try:
        fs_backup_id = int(fs_backup.atomic_backup_id)
        db_backup_id = int(db_backup.atomic_backup_id)
    except ValueError:
        print("Error: the API returned a non-numeric backup ID "
              f"({fs_backup.atomic_backup_id!r} / {db_backup.atomic_backup_id!r}).")
        sys.exit(1)

    print(f"\n  - Filesystem backup: ID {fs_backup_id}, type {fs_backup.type}, taken {fs_backup.backup_timestamp}")
    print(f"  - Database backup:   ID {db_backup_id}, type {db_backup.type}, taken {db_backup.backup_timestamp}")
    skew_seconds = abs((fs_backup.backup_timestamp - db_backup.backup_timestamp).total_seconds())
    if skew_seconds > BACKUP_SKEW_WARN_SECONDS:
        print(f"\n⚠️  These backups were taken {skew_seconds / 3600:.1f} hours apart; restoring them")
        print("    together may leave the files and database inconsistent with each other.")

    print(f"\n⚠️  This will OVERWRITE the current files and database of '{domain}'")
    print("    with the backups listed above. This action cannot be undone.\n")
    typed = input(f"Type {CONFIRM_TOKEN!r} to continue: ").strip()
    if typed != CONFIRM_TOKEN:
        print("Aborted: confirmation token did not match.")
        sys.exit(1)

    print("\n--- Checking that the site is not already suspended ---")
    try:
        existing_suspended = client.sites.get_meta(key="suspended", domain=domain)
    except NotFoundError:
        existing_suspended = None
    except AtomicAPIError as exc:
        print(f"❌ API error while reading the 'suspended' meta: {exc}")
        sys.exit(1)
    if existing_suspended in ("", 0, "0"):
        existing_suspended = None
    if existing_suspended is not None:
        print(f"❌ '{domain}' is already suspended (suspended={existing_suspended!r}).")
        if str(existing_suspended) == "503":
            print("   This may be a leftover from a previous run of this script.")
            print("   Verify no restore is in flight (check its response ticket), then unsuspend with")
            print(f"   client.sites.remove_meta(key='suspended', domain={domain!r}).")
        else:
            print("   The suspension looks unrelated to this script; resolve it first.")
        print("   This script only removes a suspension it set itself.")
        sys.exit(1)

    suspended_by_run = False
    ticket_id = None
    try:
        print("\n--- Allowing restore and suspending the site with a 503 status ---")
        try:
            client.sites.update_meta(key="allow_restore", value=int(time.time()), domain=domain)
        except AtomicAPIError as exc:
            print(f"❌ API error while setting the 'allow_restore' meta: {exc}")
            print("   The site was not suspended and no restore was started by this run.")
            sys.exit(1)

        try:
            client.sites.update_meta(key="suspended", value=503, domain=domain)
        except AtomicAPIError as exc:
            print(f"❌ API error while suspending the site: {exc}")
            print("   The 'allow_restore' meta was already set by this run.")
            if exc.status_code is None:
                # Transport-level failure: the response was lost, so the
                # server may still have applied the write. Check.
                try:
                    current = client.sites.get_meta(key="suspended", domain=domain)
                except NotFoundError:
                    print("   Verified: the site is NOT suspended.")
                except AtomicAPIError:
                    print("   Could not verify the 'suspended' meta; check it manually before retrying.")
                else:
                    print(f"   The site IS suspended (suspended={current!r}); remove the meta to bring it back online.")
            else:
                print("   The server rejected the update; the site's suspension state was not changed.")
            sys.exit(1)
        suspended_by_run = True

        print("\n--- Starting the restore ---")
        try:
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
        raw_ticket = result.get("response_ticket_id")
        if not isinstance(raw_ticket, str) or not raw_ticket:
            print(f"❌ The restore request returned no response ticket. Raw response: {result!r}")
            print("   The restore may or may not have been queued; the site remains suspended.")
            print("   Check the site's response tickets manually and unsuspend once resolved.")
            sys.exit(1)
        ticket_id = raw_ticket
        print(f"  - Restore job queued. Job ID: {job_id}, Ticket ID: {ticket_id}")

        print("\n--- Polling the response ticket until the restore completes ---")
        status = "running"
        consecutive_failures = 0
        deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
        while status == "running" and time.monotonic() < deadline:
            time.sleep(POLL_INTERVAL_SECONDS)
            try:
                summary = client.response_tickets.get_summary(ticket_id)
            except AtomicAPIError as exc:
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_POLL_FAILURES:
                    print(f"❌ Polling failed {consecutive_failures} times in a row; last error: {exc}")
                    print(f"   The restore may still be running; keep polling ticket {ticket_id!r} manually.")
                    print("   The site remains suspended until the restore finishes.")
                    sys.exit(1)
                print(f"  - Transient API error while polling ({consecutive_failures}/{MAX_CONSECUTIVE_POLL_FAILURES}): {exc}")
                continue
            consecutive_failures = 0
            if not summary:
                print("  - Ticket has no entries yet; restore still in progress.")
                continue
            status = summary.get("status", "running")
            print(f"  - Ticket status: {status}")

        if status == "success":
            print("\n--- Unsuspending the site ---")
            try:
                try:
                    current = client.sites.get_meta(key="suspended", domain=domain)
                except NotFoundError:
                    current = None
                if current is None:
                    print(f"✅ '{domain}' was restored; the suspension was already cleared.")
                elif str(current) == "503":
                    client.sites.remove_meta(key="suspended", domain=domain)
                    print(f"✅ '{domain}' was restored and is back online.")
                else:
                    print(f"⚠️  Restore finished, but 'suspended' is now {current!r} — not the 503 this run set.")
                    print("   Leaving the suspension in place; it was changed by something else during the restore.")
                    sys.exit(1)
            except AtomicAPIError as exc:
                print(f"❌ API error while unsuspending the site: {exc}")
                print("   The restore completed but the site may still be suspended and serving 503.")
                print("   Check and remove the 'suspended' meta manually.")
                sys.exit(1)
        elif status == "failure":
            print(f"❌ Restore failed. Inspect the full ticket with client.response_tickets.get_full({ticket_id!r}).")
            print("   The site is still suspended; unsuspend it manually once resolved.")
            sys.exit(1)
        elif status == "running":
            print(f"⚠️  Restore still running after {POLL_TIMEOUT_SECONDS}s. Keep polling ticket {ticket_id!r}.")
            print("   The site remains suspended until the restore finishes.")
            sys.exit(1)
        else:
            print(f"⚠️  Unexpected ticket status {status!r}. Inspect ticket {ticket_id!r}.")
            print("   The site remains suspended; unsuspend it manually once resolved.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted.")
        if ticket_id:
            print(f"   The restore may still be running; keep polling ticket {ticket_id!r}.")
            print("   The site is suspended and serving 503 — unsuspend it only once the restore finishes.")
        elif suspended_by_run:
            print("   The site is suspended (503) and a restore may have been requested.")
            print("   Check the site's response tickets before unsuspending it manually.")
        else:
            print("   The 'allow_restore' and 'suspended' meta may or may not have been set;")
            print("   verify both before retrying. No restore was started by this run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
