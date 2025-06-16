import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# This example assumes the site from '01_create_and_get_site.py' exists.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN") # Use the same domain as the create script


def main():
    """
    Demonstrates retrieving SSL certificate information and retrying provisioning.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Verify the site exists before proceeding ---
        print(f"\n--- Looking for site '{SITE_DOMAIN}' to manage its SSL settings ---")
        # We don't need the full site object, just confirmation it exists.
        client.sites.get(domain=SITE_DOMAIN)
        print(f"Found site '{SITE_DOMAIN}'.")

        # --- 2. Get SSL Certificate Information ---
        print(f"\n--- Fetching SSL info for '{SITE_DOMAIN}' ---")
        ssl_info = client.sites.get_ssl_info(domain=SITE_DOMAIN)

        if ssl_info.get("acme_certificate_id"):
            print("  - SSL Certificate appears to be active.")
            print(f"  - Certificate ID: {ssl_info.get('acme_certificate_id')}")
            print(f"  - Expires On: {ssl_info.get('certificate_expiration_date')}")
        elif ssl_info.get("broken_record"):
            print("  - SSL Certificate provisioning has failed.")
            broken_info = ssl_info.get("broken_record")
            print(f"  - Reason: {broken_info.get('reason')}")
            print(f"  - Last Error: {broken_info.get('last_error')}")
            print(f"  - Next Retry Date: {broken_info.get('retry_date')}")
        else:
            print("  - SSL Certificate is likely still provisioning.")

        # --- 3. Demonstrate Retrying SSL Provisioning ---
        # This is useful if DNS was recently corrected for a failing domain.
        print(f"\n--- Sending a request to retry SSL provisioning for '{SITE_DOMAIN}' ---")

        was_requeued = client.sites.retry_ssl_provisioning(domain=SITE_DOMAIN)

        if was_requeued:
            print("  - Successfully queued the domain for another SSL provisioning attempt.")
        else:
            print("  - Domain was not requeued. It might not have been in a failed state.")

        # --- 4. Demonstrate HSTS settings ---
        print("\n--- Managing HSTS settings ---")
        print("  - Disabling HSTS includeSubDomains directive...")
        client.sites.set_hsts_subdomain(domain=SITE_DOMAIN, enable=False)
        print("  - HSTS subdomain setting updated.")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Please run '01_create_and_get_site.py' first.")
    except AtomicAPIError as e:
        print(f"\nAn error occurred during the SSL management workflow: {e}")

if __name__ == "__main__":
    main()