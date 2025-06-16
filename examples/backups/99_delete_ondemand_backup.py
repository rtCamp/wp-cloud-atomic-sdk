import os
import sys
from typing import List
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError
from atomic_sdk.models import Backup, BackupJob

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")

def main():
    """
    Finds and deletes the most recent on-demand DB backup for the example site.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient for Backup Cleanup ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Find the site ---
        print(f"\n--- Looking for site '{SITE_DOMAIN}' to find backups to delete ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site_id}.")

        # --- 2. Find a specific ON-DEMAND backup to delete ---
        print("\n--- Listing backups to find an on-demand DB backup ---")

        all_backups: List[Backup] = client.backups.list(site_id=site_id)

        # Then, filter the list in Python to only include on-demand backups
        ondemand_backups = [b for b in all_backups if b.type in ['ondemand-db', 'ondemand-fs']]

        if not ondemand_backups:
            print("No on-demand backups found to delete.")
            print("Please run '01_create_and_list_backups.py' to create one first.")
            return

        # Find the most recent on-demand backup to be safe
        backup_to_delete = sorted(ondemand_backups, key=lambda b: b.backup_timestamp, reverse=True)[0]
        backup_to_delete_id = backup_to_delete.atomic_backup_id
        print(f"Found on-demand backup to delete: ID={backup_to_delete_id}, Type={backup_to_delete.type}")

        # --- 3. User Confirmation ---
        confirm = input(f"Are you sure you want to delete on-demand backup {backup_to_delete_id}? [y/N]: ")
        if confirm.lower() != 'y':
            print("Deletion cancelled by user.")
            sys.exit(0)

        # --- 4. Execute the deletion request ---
        print("\n--- Sending deletion request ---")
        delete_request: BackupJob = client.backups.delete(
            site_id=site_id,
            backup_id=int(backup_to_delete_id)
        )

        print(f"  - ✅ Deletion requested successfully. Request ID: {delete_request.request_id}")
        print("  - NOTE: The backup will be removed from the system shortly.")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the backup deletion workflow: {e}")
    except KeyboardInterrupt:
        print("\nDeletion process interrupted by user.")

if __name__ == "__main__":
    main()
