import os
import time
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError
from atomic_sdk.models import Job

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# Details for the new, empty site that will be the destination for the migration
DESTINATION_DOMAIN = "dest-sdk-site-12345.yourdomain.com"
ADMIN_USER = "dest_admin"
ADMIN_EMAIL = "admin@example.com"

def poll_job_until_complete(job: Job, timeout=600, poll_interval=5):
    """
    Polls the job status every `poll_interval` seconds until it completes or times out.
    Returns the final status string.
    """
    start = time.time()
    while True:
        status = job.status()
        job_state = status.get("_status") if isinstance(status, dict) else status
        print(f"⏳ Job status: {job_state}")
        if job_state in ("success", "failed", "error"):
            return job_state
        if time.time() - start > timeout:
            print("⚠️ Timeout reached while waiting for job.")
            return job_state
        time.sleep(poll_interval)

def main():
    """
    Step 1: Creates a new, empty site flagged for migration.
    This site will serve as the destination for the migrated content.
    """
    if not API_KEY or not CLIENT_ID:
        print("Error: Please set credentials in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- Check if the site already exists ---
        print(f"\n--- Checking for existing destination site '{DESTINATION_DOMAIN}' ---")
        try:
            site = client.sites.get(domain=DESTINATION_DOMAIN)
            print(f"Site '{DESTINATION_DOMAIN}' already exists with ID: {site.atomic_site_id}.")
            print("To re-run this example, please delete it first or change the DESTINATION_DOMAIN.")
            return
        except NotFoundError:
            print("Destination site does not exist. Proceeding with creation.")

        # --- Create the site with the special migration flag ---
        print(f"\n--- Creating destination site '{DESTINATION_DOMAIN}' with migration flag set to true ---")
        creation_job: Job = client.sites.create(
            domain_name=DESTINATION_DOMAIN,
            admin_user=ADMIN_USER,
            admin_email=ADMIN_EMAIL,
            # This meta key is required to mark the site as a migration target
            meta={"allow_site_migration": "true"}
        )
        print(f"Site creation job started with ID: {creation_job.job_id}")
        print("⏳ Waiting for job to complete (this can take several minutes)...")
        final_status = poll_job_until_complete(creation_job, timeout=600, poll_interval=5)

        if final_status != "success":
            raise RuntimeError(f"❌ Site creation failed with status: {final_status}")

        site_id = creation_job.atomic_site_id
        print(f"\n✅ Success! Destination site created with ID: {site_id}")
        print("\n--- NEXT STEP ---")
        print("Run '02_create_migration_with_new_key.py' to initiate the migration.")

    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
