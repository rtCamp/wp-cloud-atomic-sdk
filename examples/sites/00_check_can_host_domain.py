import os
import sys
import socket
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")


def main():
    """
    Performs pre-flight checks for a new domain:
    1. Checks if the domain can be hosted.
    2. Retrieves the IP addresses the domain should be pointed to.
    """
    if not API_KEY or not CLIENT_ID:
        print("⚠️ Error: Please set ATOMIC_API_KEY and CLIENT_ID in your .env file.")
        return

    # Accept domain from sys.argv or SITE_DOMAIN env var
    if len(sys.argv) >= 2:
        domain_to_check = sys.argv[1]
    elif SITE_DOMAIN:
        domain_to_check = SITE_DOMAIN
        print(f"🌐 Using SITE_DOMAIN from environment: {SITE_DOMAIN}")
    else:
        print("📘 Usage: python examples/sites/00_check_can_host_domain.py <domain_to_check>")
        print("   Or set SITE_DOMAIN in your .env file.")
        print("   Example: python examples/sites/00_check_can_host_domain.py example.com")
        return

    print("🔧 --- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- Step 1: Check if the domain can be hosted ---
        print(f"\n🔍 --- [1/3] Checking if domain '{domain_to_check}' can be hosted ---")
        can_host = client.sites.check_can_host_domain(domain=domain_to_check)

        if not can_host:
            print(f"❌ RESULT: The domain '{domain_to_check}' cannot be hosted at this time.")
            print("   🚫 This is usually because the domain is already in use on the WP.cloud platform.")
            print("   ⛔ You cannot proceed until this is resolved.")
            return

        print(f"✅ SUCCESS: The domain '{domain_to_check}' is available for creation.")

        # --- Step 2: Get the target IP addresses ---
        print(f"\n📡 --- [2/3] Retrieving target IP addresses ---")
        # We will call the endpoint WITH the domain to check for suggested IPs
        ip_data = client.sites.get_ips(domain=domain_to_check)
        print(f"   - Retrieved IP data: {ip_data}")
        target_ips = []

        # Handle the ACTUAL API behavior (returns a dict)
        if isinstance(ip_data, dict):
            # Prioritize 'suggested' IPs if they exist, otherwise use 'ips'
            if ip_data.get('suggested'):
                print("   - 📌 Using 'suggested' IPs from API response.")
                target_ips = ip_data.get('suggested', [])
            elif ip_data.get('ips'):
                print("   - 📌 Using standard 'ips' from API response.")
                target_ips = ip_data.get('ips', [])

        # Handle the DOCUMENTED API behavior (returns a list of dicts)
        elif isinstance(ip_data, list) and len(ip_data) > 0 and isinstance(ip_data[0], dict):
            ip_info_dict = ip_data[0]
            if ip_info_dict.get('suggested'):
                print("   - 📌 Using 'suggested' IPs from API response (list format).")
                target_ips = ip_info_dict.get('suggested', [])
            elif ip_info_dict.get('ips'):
                print("   - 📌 Using standard 'ips' from API response (list format).")
                target_ips = ip_info_dict.get('ips', [])

        # --- Process and display the results ---
        if target_ips:
            # Clean the IPs by removing CIDR notation
            cleaned_ips = [ip.split('/')[0] for ip in target_ips]
            print("✅ SUCCESS: Retrieved target IPs.")

        print(f"\n🔎 --- [3/3] Checking if domain is pointing to target IPs ---")
        print(f"   - Looking up DNS for '{domain_to_check}'...")
        try:
            current_ips = socket.gethostbyname_ex(domain_to_check)[2]
            print(f"   - 🌐 Current A record IPs for '{domain_to_check}': {current_ips}")
            if target_ips:
                cleaned_target_ips = [ip.split('/')[0] for ip in target_ips]
                missing = [ip for ip in cleaned_target_ips if ip not in current_ips]
                if missing:
                    print("\n🚨 ------------------ ACTION REQUIRED ------------------")
                    print(f"🛠️  To host '{domain_to_check}', create an 'A' record for EACH of the following IPs:")
                    print(f"   - ❌ These required IPs are NOT set: {missing}")
                else:
                    print(f"✅ SUCCESS: The domain '{domain_to_check}' is correctly pointing to the required IPs.")
        except Exception as dns_e:
            print(f"⚠️   - Could not resolve DNS for '{domain_to_check}': {dns_e}")

    except AtomicAPIError as e:
        print(f"\n❌ An API error occurred: {e}")
    except Exception as e:
        import traceback
        print(f"❗ An unexpected error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
