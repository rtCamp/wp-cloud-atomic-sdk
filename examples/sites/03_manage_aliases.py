import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# This example assumes the site from '01_create_and_get_site.py' exists.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN") # Use the same domain as the create script
ALIAS_DOMAIN = f"alias-{SITE_DOMAIN}"


def main():
    """
    Demonstrates adding, listing, and removing domain aliases for a site.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Find the site to manage ---
        print(f"\n--- Looking for site '{SITE_DOMAIN}' to manage its aliases ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site_id}.")

        # --- 2. Add a new domain alias ---
        print(f"\n--- Adding alias '{ALIAS_DOMAIN}' to site {site_id} ---")
        client.sites.add_alias(alias_domain=ALIAS_DOMAIN, site_id=site_id)
        print("  - 'add_alias' command sent successfully.")

        # --- 3. List aliases to verify the addition ---
        print("\n--- Listing all aliases for the site to verify ---")
        aliases = client.sites.list_aliases(site_id=site_id)
        print(f"  - Current aliases: {aliases}")

        if ALIAS_DOMAIN in aliases:
            print(f"  - Verification successful: '{ALIAS_DOMAIN}' is in the list.")
        else:
            raise RuntimeError(f"Verification failed: Could not find '{ALIAS_DOMAIN}' in the list.")

        # --- 4. Remove the domain alias ---
        print(f"\n--- Removing alias '{ALIAS_DOMAIN}' from site {site_id} ---")
        client.sites.remove_alias(alias_domain=ALIAS_DOMAIN, site_id=site_id)
        print("  - 'remove_alias' command sent successfully.")

        # --- 5. List aliases again to verify removal ---
        print("\n--- Listing aliases again to verify removal ---")
        aliases_after_removal = client.sites.list_aliases(site_id=site_id)
        print(f"  - Current aliases after removal: {aliases_after_removal}")

        if ALIAS_DOMAIN not in aliases_after_removal:
            print(f"  - Verification successful: '{ALIAS_DOMAIN}' has been removed.")
        else:
            raise RuntimeError(f"Verification failed: '{ALIAS_DOMAIN}' was not removed.")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Please run '01_create_and_get_site.py' first.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the alias management workflow: {e}")

if __name__ == "__main__":
    main()
