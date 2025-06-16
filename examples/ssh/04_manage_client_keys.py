import os
import sys
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# This is the special hostname for client-wide keys.
CLIENT_SSH_HOSTNAME = "client-ssh.atomicsites.net"
# A site domain is still needed to specify the target container.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")

# IMPORTANT: Replace with a real, valid public key string.
# For security, add a `from` restriction to limit where the key can connect from.
# Replace "198.51.100.1" with your own public IP address.
CLIENT_PUBLIC_KEY = "from=\"198.51.100.1\" ssh-ed25519 AAAA... automation-script@example.com"
KEY_NAME = "My Org Wide/Automation Script Key"

def main():
    """
    Demonstrates managing client-wide authorized SSH keys.
    These keys can access ALL sites associated with the client account.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID.")
        return
    if "automation-script@example.com" in CLIENT_PUBLIC_KEY:
        print("Error: Please replace the placeholder CLIENT_PUBLIC_KEY in the script.")
        print("       and ensure the 'from' IP address is your current public IP.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    key_id_to_delete = None
    site_id = None

    try:
        # --- We need the site_id to demonstrate the connection command ---
        print(f"\n--- Finding site '{SITE_DOMAIN}' to get its Atomic Site ID ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site_id}.")

        # --- 1. List existing client-wide keys ---
        print(f"\n--- [1/4] Listing existing client-wide keys ---")
        key_ids = client.ssh.list_client_keys()
        if not key_ids:
            print("  - No client-wide keys found.")
        else:
            print(f"  - Found {len(key_ids)} client-wide key ID(s):")
            # The API returns a list of strings (the IDs), not dicts.
            for key_id in key_ids:
                print(f"    - Key ID: {key_id}")

        # --- 2. Add a new client-wide key ---
        print(f"\n--- [2/4] Adding new client-wide key named '{KEY_NAME}' ---")
        add_response = client.ssh.add_client_key(key_line=CLIENT_PUBLIC_KEY, name=KEY_NAME)
        key_id_to_delete = add_response.get('id')
        print(f"  - ✅ Key added successfully with ID: {key_id_to_delete}")

        print("\n" + "="*55)
        print("  HOW TO CONNECT (CLIENT-WIDE / AUTOMATION KEY)")
        print("="*55)
        print("  IMPORTANT: This connection will only work if your current IP")
        print("             address has been allowlisted by the WP.cloud team.")
        print(f"\n  Use this special hostname: {CLIENT_SSH_HOSTNAME}")
        print(f"\n  The username for the connection IS the Atomic Site ID.")
        print(f"\n  SFTP Command:")
        print(f"    sftp {site_id}@{CLIENT_SSH_HOSTNAME}")
        print(f"\n  SSH Command:")
        print(f"    ssh {site_id}@{CLIENT_SSH_HOSTNAME}")
        print("="*55 + "\n")
        # --- END OF CORRECTION ---

        # --- 3. Verify the key was added ---
        print(f"\n--- [3/4] Verifying the new key exists ---")
        keys_after_add = client.ssh.list_client_keys()
        found = str(key_id_to_delete) in keys_after_add
        if found:
            print(f"  - ✅ Verification successful: Key ID {key_id_to_delete} found in list.")
        else:
            raise RuntimeError("Verification failed: Could not find new client key.")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Cannot get its ID to show connection example.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred: {e}")

    finally:
        # --- 4. Cleanup: Remove the client-wide key ---
        if key_id_to_delete:
            print(f"\n--- [4/4] Cleanup: Removing client-wide key ID {key_id_to_delete} ---")
            confirm = input(f"Proceed with removing client key '{KEY_NAME}'? [y/N]: ")
            if confirm.lower() == 'y':
                try:
                    client.ssh.remove_client_key(key_id=key_id_to_delete)
                    print(f"  - ✅ Key removed successfully.")
                except AtomicAPIError as e:
                    print(f"  - ❌ Cleanup failed. Error: {e}")
            else:
                print("  - Cleanup skipped.")

if __name__ == "__main__":
    main()
