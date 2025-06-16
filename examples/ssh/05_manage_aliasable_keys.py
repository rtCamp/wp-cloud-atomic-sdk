import os
import sys
import time
import base64
import hashlib

from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# Replace with your actual public key.
PUBLIC_KEY_V1 = "ssh-ed25519 AAAA... version1@example.com"
PUBLIC_KEY_V2 = "ssh-ed25519 BBBB... version2@example.com"

ALIAS_CATEGORY = "developers"
ALIAS_NAME = "jane-doe-laptop"

def get_key_fingerprint(public_key: str) -> str:
    """
    Calculates the SHA256 fingerprint of a public key in the standard format.
    """
    # Extract the base64 part of the key (the middle part)
    try:
        key_parts = public_key.strip().split()
        if len(key_parts) < 2:
            return "invalid-key-format"
        key_data = base64.b64decode(key_parts[1])
        sha256_hash = hashlib.sha256(key_data).digest()
        # The final fingerprint is base64 encoded and has the 'SHA256:' prefix and no padding.
        b64_digest = base64.b64encode(sha256_hash).rstrip(b'=').decode('utf-8')
        return f"SHA256:{b64_digest}"
    except Exception:
        return "fingerprint-calculation-failed"

def main():
    if not API_KEY or not CLIENT_ID: return
    if "..." in PUBLIC_KEY_V1 or "..." in PUBLIC_KEY_V2:
        print("Error: Please replace placeholder public keys.")
        return

    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    alias_created = False

    # Calculate fingerprints locally
    FINGERPRINT_V1 = get_key_fingerprint(PUBLIC_KEY_V1)
    FINGERPRINT_V2 = get_key_fingerprint(PUBLIC_KEY_V2)
    print(f"--- Local Fingerprint for V1: {FINGERPRINT_V1}")
    print(f"--- Local Fingerprint for V2: {FINGERPRINT_V2}")

    try:
        print(f"\n--- [1/4] Setting alias '{ALIAS_NAME}' to key V1 ---")
        set_v1_response = client.ssh.alias_pkey.set(category=ALIAS_CATEGORY, name=ALIAS_NAME, public_key=PUBLIC_KEY_V1)
        alias_created = True
        api_fingerprint_v1 = set_v1_response.get("fingerprint")
        print(f"  - API reports fingerprint: {api_fingerprint_v1}")
        if api_fingerprint_v1 != FINGERPRINT_V1:
            raise RuntimeError("Verification failed: API fingerprint for V1 does not match local calculation.")
        print("  - ✅ Initial set and fingerprint verification successful.")

        print(f"\n--- [2/4] Updating alias '{ALIAS_NAME}' to key V2 ---")
        set_v2_response = client.ssh.alias_pkey.set(category=ALIAS_CATEGORY, name=ALIAS_NAME, public_key=PUBLIC_KEY_V2)
        api_fingerprint_v2 = set_v2_response.get("fingerprint")
        print(f"  - API reports fingerprint: {api_fingerprint_v2}")
        if api_fingerprint_v2 != FINGERPRINT_V2:
            raise RuntimeError("Verification failed: API fingerprint for V2 does not match local calculation.")
        print("  - ✅ Update and fingerprint verification successful.")

        print("\n--- [3/4] Verifying with separate GET call ---")
        get_response = client.ssh.alias_pkey.get(category=ALIAS_CATEGORY, name=ALIAS_NAME)
        get_fingerprint = get_response.get("fingerprint")
        print(f"  - GET call returns fingerprint: {get_fingerprint}")
        if get_fingerprint != FINGERPRINT_V2:
            raise RuntimeError("GET verification failed: The retrieved fingerprint does not match V2.")
        print("  - ✅ Final verification successful!")

    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred: {e}")

    finally:
        if alias_created:
            print(f"\n--- [4/4] Cleanup ---")
            confirm = input(f"Proceed with removing alias '{ALIAS_NAME}'? [y/N]: ")
            if confirm.lower() == 'y':
                client.ssh.alias_pkey.remove(category=ALIAS_CATEGORY, name=ALIAS_NAME)
                print("  - Alias key removed.")

if __name__ == "__main__":
    main()
