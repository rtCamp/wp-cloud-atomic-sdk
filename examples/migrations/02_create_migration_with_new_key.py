import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# Use the same domain as the previous script
DESTINATION_DOMAIN = "dest-sdk-site-12345.yourdomain.com"

# --- Source Site Details ---
# IMPORTANT: Replace these with the actual SSH details of the site you want to migrate FROM.
SOURCE_HOST = "source.example.com"
SOURCE_USER = "source_ssh_user"
# We are intentionally leaving ssh_id (private key) blank to get a public key from the API.

# File to store the migration ID for the next scripts
MIGRATION_ID_FILE = "migration_id.txt"

def main():
    """
    Step 2: Initiates a migration for the destination site and gets a public
    key that must be installed on the source server.
    """
    if not API_KEY or not CLIENT_ID: return
    if "source.example.com" in SOURCE_HOST:
        print("Error: Please update the SOURCE_HOST and SOURCE_USER variables in this script.")
        return

    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Initiate the migration ---
        print(f"🚀 Creating migration for destination site '{DESTINATION_DOMAIN}'...")

        creation_response = client.migrations.create(
            domain=DESTINATION_DOMAIN,
            remote_host=SOURCE_HOST,
            remote_user=SOURCE_USER,
            remote_domain="migration-src.rt.gw"
        )
        migration_id = creation_response.migration_id
        public_key = creation_response.ssh_id_pub

        if not public_key:
            raise RuntimeError("API did not return a public key. A key may already be configured for this migration.")

        # --- 2. Save the migration ID and display instructions ---
        with open(MIGRATION_ID_FILE, "w") as f:
            f.write(str(migration_id))
        print(f"✅ Migration created with ID: {migration_id} (saved to {MIGRATION_ID_FILE})")

        print("\n" + "="*60)
        print("🔑 Attempting to install public key on source server via SSH...")
        print("="*60)
        import subprocess
        import shlex
        import sys
        key_escaped = public_key.replace('"', '\\"')
        ssh_cmd = f"ssh {SOURCE_USER}@{SOURCE_HOST} 'mkdir -p ~/.ssh 2>/dev/null && chmod 700 ~/.ssh && printf \"%s\\n\" \"{key_escaped}\" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'"
        try:
            result = subprocess.run(ssh_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"\n✅ Success! Public key was added to '~/.ssh/authorized_keys' for user '{SOURCE_USER}' on server '{SOURCE_HOST}'.")
            print("🔒 ----- BEGIN PUBLIC KEY -----\n")
            print(public_key)
            print("\n-----  END PUBLIC KEY  -----🔒\n")
            print("="*60)
            print("The key is installed, run '03_run_preflight_and_monitor.py' to test the connection.")
        except subprocess.CalledProcessError as e:
            print("\n❌ Could not add public key automatically via SSH.")
            print("🛑 Error output:")
            sys.stderr.write(e.stderr.decode() if e.stderr else str(e))
            print(f"⚠️ Please add the following public key manually to '~/.ssh/authorized_keys' for user '{SOURCE_USER}' on server '{SOURCE_HOST}'.")
            print("🔒 ----- BEGIN PUBLIC KEY -----\n")
            print(public_key)
            print("\n-----  END PUBLIC KEY  -----🔒\n")
            print("="*60)
            print("Once the key is installed, run '03_run_preflight_and_monitor.py' to test the connection.")

    except NotFoundError:
        print(f"❌ Error: Destination site '{DESTINATION_DOMAIN}' not found. Please run '01_prepare_destination_site.py' first.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
