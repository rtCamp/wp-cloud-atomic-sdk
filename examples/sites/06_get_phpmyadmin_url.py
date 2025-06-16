import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# This example assumes the site from '01_create_and_get_site.py' exists.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")


def main():
    """
    Demonstrates how to generate a secure, time-limited URL to access
    a site's database via phpMyAdmin.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Find the site to get the URL for ---
        print(f"\n--- Looking for site '{SITE_DOMAIN}' to generate phpMyAdmin URL ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site_id}.")

        # --- 2. Call the endpoint to generate the URL ---
        print("\n--- Requesting a single-use phpMyAdmin login URL ---")

        phpmyadmin_url = client.sites.get_phpmyadmin_url(site_id=site_id)

        if not phpmyadmin_url:
            raise RuntimeError("API did not return a URL.")

        # --- 3. Display the result ---
        print("\n" + "="*50)
        print("✅ Success! phpMyAdmin URL Generated.")
        print("This URL is time-limited and can only be used once.")
        print("\nCopy and paste this URL into your browser to access the database:")
        print(f"\n  {phpmyadmin_url}\n")
        print("="*50)

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Please run '01_create_and_get_site.py' first.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the workflow: {e}")


if __name__ == "__main__":
    main()
