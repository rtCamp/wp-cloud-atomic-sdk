import os
import json
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError
from atomic_sdk.models import Job, Site

# --- Configuration ---
# Load environment variables from a .env file in the project root
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# --- Example Site Details ---
# IMPORTANT: Use a domain you control or a test subdomain for this example.
# This script is designed to be run multiple times; it won't delete the site.
# Use the `99_delete_site.py` example for cleanup.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")
ADMIN_USER = "riddhesh"
ADMIN_EMAIL = "riddhesh.sanghvi@rtcamp.com"
ADMIN_PASS = "MiHDRNKD-a_Very!Str0ng_P@ssw0rd_for_testing" # Replace with a strong password of your choice

# Define the site type for the _data meta key
SITE_TYPE = "internal"
SITE_DATA_V1 = {"v1": {"site_type": SITE_TYPE}}
# The _data key goes inside the 'meta' dictionary, which is passed as the 'meta' kwarg.
SITE_META_PAYLOAD = {
    "_data": json.dumps(SITE_DATA_V1)
}


def create_site(client):
    print(f"\n🚀 Creating site '{SITE_DOMAIN}' as '{SITE_TYPE}' with 10GB storage and 2 PHP workers...")
    try:
        creation_job: Job = client.sites.create(
            domain_name=SITE_DOMAIN,
            admin_user=ADMIN_USER,
            admin_email=ADMIN_EMAIL,
            admin_pass=ADMIN_PASS,
            php_version="8.3",
            space_quota="10G",
            default_php_conns="2",
            burst_php_conns="0",
            meta=SITE_META_PAYLOAD
        )
        print(f"🛠️ Site creation job started with ID: {creation_job.job_id}")
        print("⏳ Waiting for job to complete (this can take several minutes)...")
        final_status = creation_job.wait(timeout=600, poll_interval=5)

        if final_status != "success":
            raise RuntimeError(f"❌ Site creation failed with status: {final_status}")

        site_id = creation_job.atomic_site_id
        print(f"✅ Site '{SITE_DOMAIN}' created successfully! 🎉 Site ID: {site_id}")
        return site_id

    except AtomicAPIError as e:
        print(f"❌ An error occurred during site creation: {e}")
        return None


def main():
    """
    Demonstrates creating a non-billable, resource-constrained internal site
    and then retrieving its details to verify the settings.
    """
 
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("⚠️ Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("🔧 Initializing AtomicClient...")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    site_id = None
    try:
        print(f"\n🔍 Checking for existing site '{SITE_DOMAIN}'...")
        existing_site = client.sites.get(domain=SITE_DOMAIN)
        site_id = existing_site.atomic_site_id
        print(f"ℹ️ Site already exists with ID: {site_id}. Skipping creation.")
    except (NotFoundError, AtomicAPIError) as e:
        status_code = getattr(e, "status_code", None)
        if isinstance(e, NotFoundError) or status_code == 404:
            print("📭 Site does not exist. Proceeding with creation...")
            site_id = create_site(client)
        else:
            print(f"❌ API error while checking for site: {e}")
            return

    if site_id:
        print(f"\n🔍 Verifying settings for site ID: {site_id}...")
        try:
            site: Site = client.sites.get(site_id=site_id, extra=True)
            print(f"🆔 Site ID: {site.atomic_site_id}")
            print(f"🌐 Domain: {site.domain_name}")
            print(f"⚙️ PHP Version: {site.php_version}")
            print(f"👤 Admin User: {site.wp_admin_user}")
            print(f"📧 Admin Email: {site.wp_admin_email}")
            print(f"🧊 Cache Prefix: {site.cache_prefix}")
            server_pool = site.get_extra('server_pool', {})
            print(f"📍 Geo Affinity (from extra): {server_pool.get('geo_affinity')}")

            space_quota = client.sites.get_meta(key="space_quota", site_id=site_id)
            php_conns = client.sites.get_meta(key="default_php_conns", site_id=site_id)
            data_meta_str = client.sites.get_meta(key="_data", site_id=site_id)

            print(f"💾 Verified Space Quota: {space_quota}")
            print(f"🧵 Verified PHP Workers: {php_conns}")

            if data_meta_str:
                try:
                    unescaped_str = data_meta_str.encode('utf-8').decode('unicode_escape')
                    data_meta = json.loads(unescaped_str)
                    retrieved_site_type = data_meta.get("v1", {}).get("site_type")
                    print(f"📦 Verified Site Type (_data): {retrieved_site_type}")
                    if retrieved_site_type != SITE_TYPE:
                        print("⚠️ WARNING: Site type does not match expected value!")
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"❌ ERROR: Could not parse the _data string: {e}")
                    print(f"📝 Raw _data string: {repr(data_meta_str)}")
            else:
                print("⚠️ WARNING: _data meta key is not set on the site.")
        except AtomicAPIError as e:
            print(f"❌ Could not retrieve site details. Error: {e}")


if __name__ == "__main__":
    main()
