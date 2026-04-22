"""
Example: reverse lookup of an SSH/SFTP user by username.

``client.ssh.list_users(site_id=...)`` answers "which users does this site
have?". This example demonstrates the inverse: given a username, find which
site owns it.

Usage:
    python examples/ssh/06_lookup_ssh_user.py <username>
"""

import os
import sys

from dotenv import load_dotenv # type: ignore

from atomic_sdk import AtomicAPIError, AtomicClient, NotFoundError

load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")


def main() -> None:
    if not API_KEY or not CLIENT_ID:
        print("Error: set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python examples/ssh/06_lookup_ssh_user.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        info = client.ssh.get_user(username)
    except NotFoundError:
        print(f"❌ No SSH user named '{username}' exists on this client account.")
        sys.exit(1)
    except AtomicAPIError as exc:
        print(f"❌ API error: {exc}")
        sys.exit(1)

    print(f"✅ Found SSH user '{info.get('user')}'")
    print(f"   atomic_site_id : {info.get('atomic_site_id')}")
    print(f"   created        : {info.get('created')}")
    print(f"   last_updated   : {info.get('last_updated')}")


if __name__ == "__main__":
    main()
