import os
import time
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

SITE_DOMAIN = os.environ.get("SITE_DOMAIN")

def main():
    """
    Demonstrates checking cache status, turning it off/on, purging, and managing defensive mode.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    original_status = None

    try:
        print(f"\n--- Looking for site '{SITE_DOMAIN}' to manage its edge cache ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site_id}.")

        # --- Get the initial status to revert to later ---
        status_info = client.edge_cache.get_status(site_id=site_id)
        original_status = status_info.get('status_name')
        print(f"\n--- [1/6] Initial cache status: {original_status} ---")

        # --- Turn Edge Cache OFF ---
        print(f"\n--- [2/6] Turning Edge Cache OFF for '{SITE_DOMAIN}' ---")
        client.edge_cache.set_status(action="off", site_id=site_id)
        print("  - 'off' command sent. Waiting a moment to verify...")
        time.sleep(10)
        status_after_off = client.edge_cache.get_status(site_id=site_id)
        print(f"  - Verified status: {status_after_off.get('status_name')}")
        if status_after_off.get('status_name') != 'Disabled':
            print("  - ❌ Verification failed: Cache is not disabled.")
        else:
            print("  - ✅ Verification successful: Cache is now disabled.")

        # --- Turn Edge Cache ON ---
        print(f"\n--- [3/6] Turning Edge Cache ON for '{SITE_DOMAIN}' ---")
        client.edge_cache.set_status(action="on", site_id=site_id)
        print("  - 'on' command sent. Waiting a moment to verify...")
        time.sleep(10)
        status_after_on = client.edge_cache.get_status(site_id=site_id)
        print(f"  - Verified status: {status_after_on.get('status_name')}")
        if status_after_on.get('status_name') != 'Enabled':
            print("  - ❌ Verification failed: Cache is not enabled.")
        else:
            print("  - ✅ Verification successful: Cache is now enabled.")

        # --- Purge the cache ---
        print(f"\n--- [4/6] Purging the edge cache for '{SITE_DOMAIN}' ---")
        client.edge_cache.purge(site_id=site_id)
        print("  - ✅ Cache purge command sent successfully.")

        # --- Manage Defensive Mode ---
        print(f"\n--- [5/6] Enabling defensive (DDoS) mode for 5 minutes ---")
        client.edge_cache.enable_defensive_mode(duration_in_minutes=5, site_id=site_id)
        print("  - Defensive mode enabled...")
        time.sleep(10) # Give it time to activate
        status_after_enable = client.edge_cache.get_status(site_id=site_id)
        if status_after_enable.get('status_name') == 'DDoS':
            print("  - ✅ Verification successful: Defensive mode is active.")
        else:
            print("  - ❌ Verification failed.")

        print(f"\n--- [6/6] Disabling defensive mode ---")
        client.edge_cache.disable_defensive_mode(site_id=site_id)
        print("  - Defensive mode disabled...")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Please run '01_create_and_get_site.py' first.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the edge cache management workflow: {e}")

    finally:
        # --- Cleanup: Revert to original status if needed ---
        if site_id and original_status:
            print(f"\n--- Cleanup: Ensuring cache is restored to original state ({original_status}) ---")
            current_status_info = client.edge_cache.get_status(site_id=site_id)
            if current_status_info.get('status_name') != original_status:
                action_to_revert = "on" if original_status == "Enabled" else "off"
                client.edge_cache.set_status(action=action_to_revert, site_id=site_id)
                print(f"  - Revert command '{action_to_revert}' sent.")
            else:
                print("  - Cache is already in its original state. No action needed.")


if __name__ == "__main__":
    main()
