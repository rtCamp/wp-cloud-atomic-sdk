import os
import time
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError
from atomic_sdk.models import Job

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# This example assumes the site from '01_create_and_get_site.py' exists.
# Make sure to run that script first.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN") # Use the same domain as the create script

def poll_job_until_complete(job: Job, timeout=600, poll_interval=15):
    """
    Polls the job status every `poll_interval` seconds until it completes or times out.
    Returns the final status string.
    """
    start = time.time()
    while True:
        status = job.status()
        print(f"  - Job status: {status["_status"]}")
        job_state = status["_status"] if isinstance(status, dict) and "_status" in status else status
        if job_state in ("success", "failed", "error"):
            return job_state
        if time.time() - start > timeout:
            print("  - Timeout reached while waiting for job.")
            return job_state
        time.sleep(poll_interval)

def main():
    """
    Demonstrates managing plugins and themes on an existing site.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Find the site to manage ---
        print(f"\n--- Looking for site '{SITE_DOMAIN}' to manage its software ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site_id}. Proceeding with software management.")

        # --- 2. Define Software Actions ---
        # We will install a new theme, activate a plugin, and remove another.
        software_actions = {
            "themes/twentytwenty/latest": "install",
            "plugins/woocommerce/latest": "install",
        }

        print("\n--- Sending request to install 'Twenty Twenty' theme and 'WooCommerce' plugin ---")

        # --- 3. Execute the Asynchronous Job ---
        install_job: Job = client.sites.manage_software(
            site_id=site_id,
            software_actions=software_actions
        )

        print(f"  - Software installation job started with ID: {install_job.job_id}")
        print("  - Waiting for job to complete...")
        status = poll_job_until_complete(install_job, timeout=300, poll_interval=2)

        if status != "success":
            raise RuntimeError(f"Installation job failed with status: {status}")

        print("  - Installation job finished successfully!")

        # --- 4. Activate the newly installed software ---
        print("\n--- Sending request to activate 'WooCommerce' plugin ---")

        activation_job: Job = client.sites.manage_software(
            site_id=site_id,
            software_actions={"plugins/woocommerce/latest": "activate"}
        )

        print(f"  - Activation job started with ID: {activation_job.job_id}")
        print("  - Waiting for job to complete...")
        status = poll_job_until_complete(activation_job, timeout=300, poll_interval=2)

        if status != "success":
            raise RuntimeError(f"Activation job failed with status: {status}")

        print("  - Activation job finished successfully!")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Please run '01_create_and_get_site.py' first.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the software management workflow: {e}")

if __name__ == "__main__":
    main()
