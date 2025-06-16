import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")


def main():
    """
    Demonstrates retrieving information about the WP.cloud platform's
    available datacenters and PHP versions.
    """
    if not API_KEY or not CLIENT_ID:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Get Available Datacenters ---
        # These are the codes you can use for 'geo_affinity' when creating a site.
        print(f"\n--- [1/2] Fetching available datacenters for client '{CLIENT_ID}' ---")

        datacenters = client.servers.list_available_datacenters()

        if datacenters:
            print("  - ✅ Success! Available datacenter codes:")
            for dc in datacenters:
                print(f"    - {dc}")
        else:
            print("  - No available datacenters returned.")

        # --- 2. Get Available PHP Versions (in two formats) ---
        print(f"\n--- [2/2] Fetching available PHP versions ---")

        # Simple format (default)
        print("\n  - Availabke PHP Versions:")
        php_versions_simple = client.servers.list_php_versions()
        print(f"    - {php_versions_simple}")

        # Verbose format
        print("\n  - Verbose Details:")
        php_versions_verbose = client.servers.list_php_versions(verbose=True)
        if php_versions_verbose:
            print(f"    - Default Version: {php_versions_verbose.get('default')}")
            available = php_versions_verbose.get('available', {})
            for version, details in available.items():
                print(f"      - Version {version}: Status='{details.get('status')}', Supported Until='{details.get('until')}'")

    except AtomicAPIError as e:
        print(f"\nAn API error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
