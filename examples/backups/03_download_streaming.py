import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")
BACKUP_ID = os.environ.get("BACKUP_ID")

# The local path where the backup file will be saved.
DOWNLOAD_PATH = os.environ.get("BACKUP_DOWNLOAD_PATH", "./backup-download.bin")


def main():
    """
    Demonstrates streaming a backup directly to disk without buffering it in RAM.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN or not BACKUP_ID:
        print("Error: Please set ATOMIC_API_KEY, ATOMIC_CLIENT_ID, SITE_DOMAIN, and BACKUP_ID.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        print(f"\n--- Streaming backup {BACKUP_ID} for {SITE_DOMAIN} ---")
        with open(DOWNLOAD_PATH, "wb") as dest:
            bytes_written = client.backups.download(
                backup_id=BACKUP_ID,
                dest=dest,
                domain=SITE_DOMAIN,
            )

        print(f"  - Download complete. Wrote {bytes_written} bytes to '{DOWNLOAD_PATH}'.")

    except NotFoundError:
        print(f"Error: Backup '{BACKUP_ID}' for site '{SITE_DOMAIN}' was not found.")
    except AtomicAPIError as e:
        print(f"\nAn API error occurred during the streaming download: {e}")


if __name__ == "__main__":
    main()
