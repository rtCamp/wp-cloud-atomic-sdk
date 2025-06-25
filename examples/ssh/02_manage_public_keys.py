import os
import sys
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

SITE_DOMAIN = os.environ.get("SITE_DOMAIN")
SSH_KEY_USER = "sdk-key-user"
# Replace with your actual public key. Using a common example format.
# IMPORTANT: This must be a real, valid public key string.
PUBLIC_KEY = "ssh-ed25519 AAAA... your-email@example.com"
SSH_HOSTNAME = "ssh.atomicsites.net"

def main():
    """
    Demonstrates adding a key-based SSH user and enabling full SSH shell access for the site.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return
    if "your-email@example.com" in PUBLIC_KEY:
        print("Error: Please replace the placeholder PUBLIC_KEY in the script with your actual public key.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    site_id = None

    try:
        # --- 1. Find the site ---
        print(f"\n--- [1/3] Looking for site '{SITE_DOMAIN}' ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site.atomic_site_id}.")

        # --- 2. Add user with a public key and no password ---
        print(f"\n--- [2/3] Adding key-based user '{SSH_KEY_USER}' ---")
        client.ssh.add_user(
            username=SSH_KEY_USER,
            site_id=site_id,
            public_key=PUBLIC_KEY,
            password=""
        )
        print("  - ✅ User with public key added successfully.")

        # --- 3. Enable full SSH shell access for the site ---
        print(f"\n--- [3/3] Enabling full 'ssh' access for site {site_id} ---")
        # Default is often 'sftp'-only. This grants shell access.
        response = client.ssh.set_access_type(access_type="ssh", site_id=site_id)
        print(f"  - ✅ Access type set to '{response.get('type')}' successfully.")

        # --- How to Connect ---
        print("\n" + "="*35)
        print("  HOW TO CONNECT (KEY AUTH + SHELL)")
        print("="*35)
        print("Use the following command to get a full SSH shell.")
        print("This assumes your corresponding private key is in your ssh-agent or ~/.ssh/")
        print(f"\n  SSH Command:")
        print(f"    ssh {SSH_KEY_USER}@{SSH_HOSTNAME}")
        print("="*35 + "\n")

    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred: {e}")

    finally:
        # --- 4. Cleanup ---
        print(f"\n--- Cleanup: Removing user '{SSH_KEY_USER}' ---")
        confirm = input(f"Proceed with removing user '{SSH_KEY_USER}'? [y/N]: ")
        if confirm.lower() == 'y':
            try:
                client.ssh.remove_user(username=SSH_KEY_USER, domain=SITE_DOMAIN)
                print(f"  - ✅ User '{SSH_KEY_USER}' removed successfully.")
            except AtomicAPIError as e:
                print(f"  - ❌ Cleanup failed. Error: {e}")
        else:
            print("  - Cleanup skipped.")


if __name__ == "__main__":
    main()
