import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# This is a test webhook.site URL, feel free to change it to your own.
WEBHOOK_URL = "https://webhook.site/9b400bcf-5b2d-41ac-a382-a2dd4d647625"

def main():
    """
    Demonstrates getting, setting, and removing client-level metadata.
    This example uses the 'webhook_url' as the target meta key.
    """
    if not API_KEY or not CLIENT_ID:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Get the current webhook_url (it might not exist) ---
        print(f"\n--- [1/4] Getting current 'webhook_url' for client '{CLIENT_ID}' ---")
        try:
            current_url = client.client.get_meta(key="webhook_url")
            print(f"  - Current webhook_url is: {current_url}")
        except AtomicAPIError as e:
            # A 404 is expected if the key has never been set
            if getattr(e, "status_code", None) == 404:
                print("  - No webhook_url currently set.")
            else:
                raise  # Re-raise other unexpected errors

        # --- 2. Set or update the webhook_url ---
        print(f"\n--- [2/4] Setting 'webhook_url' to '{WEBHOOK_URL}' ---")
        client.client.set_meta(key="webhook_url", value=WEBHOOK_URL)
        print("  - Set command sent successfully.")

        # --- 3. Verify the new value ---
        print(f"\n--- [3/4] Verifying the new 'webhook_url' ---")
        updated_url = client.client.get_meta(key="webhook_url")
        print(f"  - Verified webhook_url is: {updated_url}")
        if updated_url != WEBHOOK_URL:
            raise RuntimeError("Verification failed: The URL was not updated correctly.")
        print("  - Verification successful!")

        # --- 4. Remove the webhook_url (Cleanup) ---
        print(f"\n--- [4/4] Removing 'webhook_url' ---")
        confirm = input(f"Proceed with removing webhook? [y/N]: ")
        if confirm.lower() == 'y':
            try:
                client.client.remove_meta(key="webhook_url")
                print("  - Remove command sent successfully.")
                client.client.get_meta(key="webhook_url")
                print("  - Cleanup warning: Webhook URL still exists after removal.")
            except AtomicAPIError as e:
                if getattr(e, "status_code", None) == 404:
                    print("  - Cleanup successful: Webhook URL has been removed.")
                else:
                    print(f"  - Cleanup warning: An unexpected error occurred during verification: {e}")
        else:
            print("  - Cleanup skipped.")

    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the client meta management workflow: {e}")


if __name__ == "__main__":
    main()
