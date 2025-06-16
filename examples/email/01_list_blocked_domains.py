import os
from dotenv import load_dotenv
from typing import List, Dict, Any
from atomic_sdk import AtomicClient, AtomicAPIError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")


def main():
    """
    Demonstrates retrieving the list of domains that have been blocked
    from sending email from the platform.
    """
    if not API_KEY or not CLIENT_ID:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Fetch the list of blocked domains ---
        print(f"\n--- Fetching email blocklist for client '{CLIENT_ID}' ---")

        blocked_list: List[Dict[str, Any]] = client.email.list_blocked_domains()

        # --- 2. Display the results ---
        if not blocked_list:
            print("✅ No domains are currently on the email blocklist for this client.")
            return

        print(f"Found {len(blocked_list)} blocked domain(s):")
        for item in blocked_list:
            print("-" * 20)
            print(f"  Domain:         {item.get('domain')}")
            print(f"  Site ID:        {item.get('atomic_site_id')}")
            print(f"  Reason:         {item.get('reason')}")
            print(f"  Block Expires:  {item.get('expires_on')}")

    except AtomicAPIError as e:
        print(f"\nAn API error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
