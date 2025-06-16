import os
import time
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError
from atomic_sdk.models import Site

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# This example assumes the site from '01_create_and_get_site.py' exists.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN") # Use the same domain as the create script


def main():
    """
    Demonstrates reading and updating various site properties and metadata values.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    site_id = None

    try:
        # --- 1. Find the site and get its main details ---
        print(f"\n--- Looking for site '{SITE_DOMAIN}' ---")
        site: Site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site_id}.")

        # --- 2. Read various properties from different sources ---
        print("\n--- Reading various site properties and metadata keys ---")

        # 'wp_version' is a direct property of the main site object
        wp_version = site.wp_version
        print(f"  - WordPress Version (from main object): {wp_version}")

        # 'space_quota', 'default_php_conns', etc., are true "meta" fields
        space_quota = client.sites.get_meta(key="space_quota", site_id=site_id)
        original_php_conns = client.sites.get_meta(key="default_php_conns", site_id=site_id)

        print(f"  - Space Quota (from meta): {space_quota}")
        print(f"  - Default PHP Workers (from meta): {original_php_conns}")

        # 'space_used' is a special case only available in the bulk /get-sites list
        sites_list = client.sites.list(limit=1000)
        space_used = "N/A"
        for s in sites_list:
            if s.get('atomic_site_id') == str(site_id):
                space_used = s.get('space_used', 'N/A')
                break
        print(f"  - Space Used (from sites list): {space_used} bytes")

        # --- 3. Update a metadata key (PHP Workers) ---
        target_php_conns = "3" if original_php_conns != "3" else "2"
        print(f"\n--- Updating Default PHP Workers to '{target_php_conns}' ---")

        client.sites.update_meta(key="default_php_conns", value=target_php_conns, site_id=site_id)
        print("  - Update command sent. This change should be quick.")
        time.sleep(5)

        # --- 4. Verify the metadata change ---
        new_php_conns = client.sites.get_meta(key="default_php_conns", site_id=site_id)
        print(f"  - New reported PHP workers: {new_php_conns}")
        if str(new_php_conns) == target_php_conns:
            print("  - Verification successful!")
        else:
            print(f"  - Verification failed. Expected {target_php_conns} but got {new_php_conns}.")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Please run '01_create_and_get_site.py' first.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the metadata management workflow: {e}")

    finally:
        # --- 5. Cleanup: Revert the change ---
        if site_id and original_php_conns:
            print(f"\n--- Cleanup: Reverting PHP workers back to '{original_php_conns}' ---")
            try:
                # Re-check current value before reverting
                current_conns = client.sites.get_meta(key="default_php_conns", site_id=site_id)
                if str(current_conns) != str(original_php_conns):
                    client.sites.update_meta(key="default_php_conns", value=original_php_conns, site_id=site_id)
                    print("  - Revert command sent.")
                else:
                    print("  - Value is already correct. No revert needed.")
            except AtomicAPIError as e:
                print(f"  - Cleanup warning: Could not revert PHP workers. Error: {e}")

if __name__ == "__main__":
    main()
