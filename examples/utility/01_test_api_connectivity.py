import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")


def main():
    """
    Demonstrates using the utility endpoint to test API connectivity and authentication.
    """
    if not API_KEY or not CLIENT_ID:
        print("⚠️ Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("🔧 --- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    print("✅ Client initialized successfully.")

    try:
        # --- 1. Perform a basic success test ---
        print("\n🔍 --- Performing a standard connectivity test (expecting 200 OK) ---")

        response = client.utility.test_status()

        print(f"📡  - API Response: {response}")

        # The SDK's base client raises an exception for non-2xx responses,
        # so if we get here, the call was successful.
        print("✅  - Test successful! Authentication and connectivity are working.")

        # # --- 2. Perform a test to simulate a client error ---
        # print("\n🚫 --- Simulating a 'Bad Request' error (expecting 400) ---")
        # try:
        #     # We expect this call to fail and raise an exception.
        #     client.utility.test_status(status_code=400, message="Simulated-Bad-Request")
        # except AtomicAPIError as e:
        #     print(f"🎯  - Successfully caught expected exception: {e}")
        #     if getattr(e, "status_code", None) == 400:
        #         print("✅  - Test successful! Correctly handled a 400 error response.")
        #     else:
        #         print(f"❌  - Test failed: Expected status 400 but got {getattr(e, 'status_code', 'None')}")

    except AtomicAPIError as e:
        print(f"\n❌ An API error occurred during the initial test: {e}")
        print("🛠️  Please check your API Key and network connection.")
    except Exception as e:
        print(f"❗ An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
