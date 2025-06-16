import os
import sys
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

SITE_DOMAIN = os.environ.get("SITE_DOMAIN")
SSH_USERNAME = "sdk-test-user"
SSH_PASSWORD = "a_Very!Str0ng_P@ssw0rd_for_testing" # Replace this with a secure password.
SSH_HOSTNAME = "ssh.atomicsites.net"

def main():
    """
    Demonstrates adding, listing, updating, and removing a site-specific SSH/SFTP user.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    user_created = False

    try:
        # --- 1. Find the site to manage ---
        print(f"\n--- Looking for site '{SITE_DOMAIN}' to manage SSH users ---")
        site = client.sites.get(domain=SITE_DOMAIN)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site_id}.")

        # --- 2. Add a new SSH user with a password ---
        print(f"\n--- [1/4] Adding SSH user '{SSH_USERNAME}' to site {site_id} ---")
        add_response = client.ssh.add_user(
            username=SSH_USERNAME,
            site_id=site_id,
            password=f"{SSH_PASSWORD}+something"
        )
        user_created = True
        print(f"  - User '{add_response.get('user')}' created successfully.")

        # --- 3. List users to verify the addition ---
        print(f"\n--- [2/4] Listing all SSH users on the site to verify ---")
        user_list = client.ssh.list_users(site_id=site_id)
        print(f"  - Current users: {user_list}")
        if SSH_USERNAME in user_list:
            print(f"  - ✅ Verification successful: '{SSH_USERNAME}' is in the list.")
        else:
            raise RuntimeError("Verification failed: Could not find new user in list.")

        # --- 4. Update the user (e.g., update password) ---
        print(f"\n--- [3/4] Updating user '{SSH_USERNAME}' with a new password ---")
        client.ssh.update_user(
            username=SSH_USERNAME,
            site_id=site_id,
            password=SSH_PASSWORD
        )
        print(f"  - Update command sent for user '{SSH_USERNAME}'.")

        print("\n" + "="*35)
        print("  HOW TO CONNECT (PASSWORD AUTH)")
        print("="*35)
        print("Use the following commands to connect to your site.")
        print("You will be prompted for the password defined in this script.")
        print(f"\n  SFTP Command:")
        print(f"    sftp {SSH_USERNAME}@{SSH_HOSTNAME}")
        print("="*35 + "\n")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Please run '01_create_and_get_site.py' first.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the SSH user management workflow: {e}")

    finally:
        # --- 5. Cleanup: Remove the user ---
        if user_created:
            print(f"\n--- [4/4] Cleanup: Removing SSH user '{SSH_USERNAME}' ---")
            confirm = input(f"Proceed with removing user '{SSH_USERNAME}'? [y/N]: ")
            if confirm.lower() == 'y':
                try:
                    client.ssh.remove_user(username=SSH_USERNAME, site_id=site_id)
                    print(f"  - ✅ User '{SSH_USERNAME}' removed successfully.")
                except AtomicAPIError as e:
                    print(f"  - ❌ Cleanup failed: Could not remove user. Error: {e}")
            else:
                print("  - Cleanup skipped by user.")


if __name__ == "__main__":
    main()
