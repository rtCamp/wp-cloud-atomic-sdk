import os
from typing import List
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError
from atomic_sdk.models import Backup

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# This example assumes the site from '01_create_and_get_site.py' exists.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN") # Use the same domain

# The local path where the backup file will be saved
DOWNLOAD_PATH = "./" # Current directory

def get_file_extension(backup_type: str) -> str:
    """Determines the correct file extension based on the backup type."""
    if backup_type in ("fs", "ondemand-fs"):
        return "tar.bz2"
    if backup_type in ("db", "ondemand-db"):
        return "sql"
    return "backup" # Fallback for unknown types

def main():
    """
    Demonstrates finding the latest backup, getting its info, and downloading it.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Find the site ---
        print(f"\n--- Looking for site '{SITE_DOMAIN}' to find a backup ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        print(f"Found site ID: {site.atomic_site_id}.")

        # --- 2. Find the most recent backup to download ---
        print("\n--- Listing backups to find the most recent one ---")
        backups = client.backups.list(site_id=site.atomic_site_id)
        if not backups:
            print("No backups found for this site. Please run '01_create_and_list_backups.py' first.")
            return

        # Sort by timestamp to find the latest backup
        latest_backup = sorted(backups, key=lambda b: b.backup_timestamp, reverse=True)[0]
        print(f"Found latest backup: ID={latest_backup.atomic_backup_id}, Type={latest_backup.type.upper()}")

        # --- 3. Get specific info for that backup ---
        print(f"\n--- Getting specific info for backup ID: {latest_backup.atomic_backup_id} ---")
        backup_info: Backup = client.backups.info(
            backup_id=latest_backup.atomic_backup_id,
            site_id=site.atomic_site_id
        )
        print(f"  - Confirmed Backup ID: {backup_info.atomic_backup_id}")
        print(f"  - Confirmed Type: {backup_info.type}")
        print(f"  - Confirmed Timestamp: {backup_info.backup_timestamp}")

        # --- 4. Download the backup file ---
        print(f"\n--- Downloading backup {backup_info.atomic_backup_id} ---")
        backup_content: bytes = client.backups.get(
            backup_id=backup_info.atomic_backup_id,
            site_id=site.atomic_site_id
        )

        # --- 5. Save the downloaded content to a local file ---
        file_extension = get_file_extension(backup_info.type)
        filename = f"{site.domain_name}_{backup_info.atomic_backup_id}.{file_extension}"
        full_path = os.path.join(DOWNLOAD_PATH, filename)

        print(f"  - Download complete. Saving {len(backup_content)} bytes to '{full_path}'...")
        with open(full_path, "wb") as f:
            f.write(backup_content)

        print(f"  - ✅ Backup file saved successfully.")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Please run '01_create_and_get_site.py' first.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the backup download workflow: {e}")

if __name__ == "__main__":
    main()
