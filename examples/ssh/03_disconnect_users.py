import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError
from atomic_sdk.models import Job

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")


def main():
    """
    Demonstrates how to forcefully disconnect all active SSH/SFTP users from a site.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        print(f"\n--- Looking for site '{SITE_DOMAIN}' ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        print(f"Found site ID: {site.atomic_site_id}.")

        print(f"\n--- Sending request to disconnect all SSH users from site {site.atomic_site_id} ---")
        disconnect_job: Job = client.ssh.disconnect_all_users(site_id=site.atomic_site_id)

        print(f"  - Disconnect job started with ID: {disconnect_job.job_id}")
        # Note: Polling is not strictly necessary but confirms the command was processed.
        status = disconnect_job.wait(timeout=20)
        print(f"  - Job finished with status: {status}")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    main()
