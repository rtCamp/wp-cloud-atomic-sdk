import os
import sys
import time
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError
from atomic_sdk.models import Job

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# This script is designed to clean up the site created by the previous examples.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN") # Use the same domain

def poll_job_until_complete(job: Job, timeout=600, poll_interval=15):
    """
    Polls the job status every `poll_interval` seconds until it completes or times out.
    Returns the final status string.
    """
    start = time.time()
    while True:
        status = job.status()
        print(f"🔄  - Job status: {status['_status']}")
        job_state = status["_status"] if isinstance(status, dict) and "_status" in status else status
        if job_state in ("success", "failed", "error"):
            return job_state
        if time.time() - start > timeout:
            print("⏰  - Timeout reached while waiting for job.")
            return job_state
        time.sleep(poll_interval)

def main():
    """
    Finds and deletes the example site to clean up the environment.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("⚠️ Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("🛠️ --- Initializing AtomicClient for Cleanup ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Find the site to delete ---
        print(f"\n🔍 --- Looking for site '{SITE_DOMAIN}' to delete ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"📄 Found site ID: {site_id}. Preparing for deletion.")

        # --- 2. User Confirmation ---
        # This is a critical safety measure for a destructive operation.
        confirm = input(f"Are you sure you want to delete site {site_id} ({SITE_DOMAIN})? [y/N]: ")
        if confirm.lower() != 'y':
            print("🚫 Deletion cancelled by user.")
            sys.exit(0)

        # --- 3. Execute Deletion Job ---
        print("\n📡 --- Sending deletion request ---")
        delete_job: Job = client.sites.delete(site_id=site_id)

        print(f"🚀   - Deletion job started with ID: {delete_job.job_id}")
        print("⏳   - Waiting for deletion to complete...")
        status = poll_job_until_complete(delete_job, timeout=300, poll_interval=5)

        if status == "success":
            print(f"✅   - Job completed successfully. Site '{SITE_DOMAIN}' has been deleted.")
        else:
            raise RuntimeError(f"Deletion job failed with status: {status}")

    except NotFoundError:
        print(f"❓ Site '{SITE_DOMAIN}' not found. It may have already been deleted.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\n❌ An error occurred during the site deletion: {e}")
    except (KeyboardInterrupt):
        print("\n🛑 Deletion process interrupted by user.")

if __name__ == "__main__":
    main()
