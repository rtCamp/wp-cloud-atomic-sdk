import os
import time
from typing import List
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError
# Import both Backup and BackupJob models
from atomic_sdk.models import Backup, BackupJob

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")

def main():
    """
    Demonstrates listing existing backups and creating new on-demand backups.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        print(f"\n--- Looking for site '{SITE_DOMAIN}' to manage its backups ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site_id}.")

        print("\n--- Listing existing backups for the site ---")
        backups: List[Backup] = client.backups.list(site_id=site_id)

        if not backups:
            print("No existing backups found for this site.")
        else:
            print(f"Found {len(backups)} backup records. Showing the 5 most recent:")
            sorted_backups = sorted(backups, key=lambda b: b.backup_timestamp, reverse=True)
            for backup in sorted_backups[:5]:
                print(f"  - ID: {backup.atomic_backup_id}, Type: {backup.type.upper()}, Date: {backup.backup_timestamp}")

        print("\n--- Requesting a new on-demand DATABASE backup ---")
        db_creation_request: BackupJob = client.backups.create(site_id=site_id, backup_type="db")

        # Access .request_id instead of .job_id
        print(f"  - DB backup creation requested successfully. Request ID: {db_creation_request.request_id}")

        # print("\n--- Requesting a new on-demand FILESYSTEM backup ---")
        # fs_creation_request: BackupJob = client.backups.create(site_id=site_id, backup_type="fs")

        # # Access .request_id instead of .job_id
        # print(f"  - FS backup creation requested successfully. Request ID: {fs_creation_request.request_id}")

        # print("\nNOTE: The API does not support polling for backup job status.")
        # print("Wait a few minutes, then re-run this script to see the new backups appear in the list.")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Please run '01_create_and_get_site.py' first.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the backup management workflow: {e}")

if __name__ == "__main__":
    main()
