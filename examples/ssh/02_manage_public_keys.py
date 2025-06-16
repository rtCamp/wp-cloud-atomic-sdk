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
    Demonstrates adding and updating a site-specific SSH user with a public key.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return
    if "your-email@example.com" in PUBLIC_KEY:
        print("Error: Please replace the placeholder PUBLIC_KEY in the script with your actual public key.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Find the site ---
        print(f"\n--- Looking for site '{SITE_DOMAIN}' ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        print(f"Found site ID: {site.atomic_site_id}.")

        # --- 2. Add user with a public key and no password ---
        print(f"\n--- Adding key-based user '{SSH_KEY_USER}' ---")
        # An empty string for the password disables password-based login.
        client.ssh.add_user(
            username=SSH_KEY_USER,
            site_id=site.atomic_site_id,
            public_key=PUBLIC_KEY,
            password=""
        )
        print("  - ✅ User with public key added successfully.")

        print("\n" + "="*35)
        print("  HOW TO CONNECT (KEY AUTH)")
        print("="*35)
        print("Use the following commands to connect to your site.")
        print("This assumes your corresponding private key is in your ssh-agent or ~/.ssh/")
        print(f"\n  SFTP Command:")
        print(f"    sftp {SSH_KEY_USER}@{SSH_HOSTNAME}")
        print("="*35 + "\n")

    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred: {e}")

    finally:
        # --- 3. Cleanup ---
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
