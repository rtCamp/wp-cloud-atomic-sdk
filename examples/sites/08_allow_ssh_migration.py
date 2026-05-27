"""
Example: mark a destination site as willing to accept an incoming SSH migration.

WARNING: ``client.sites.allow_ssh_migration`` is DESTRUCTIVE and ONE-WAY. Once
set, it cannot be revoked, and the next migration into the site will OVERWRITE
its files and database. Only run this against a freshly-created destination
site that exists for the sole purpose of receiving a migration.

Usage:
    python examples/sites/08_allow_ssh_migration.py <site_domain>

Or set SITE_DOMAIN in your .env file.
"""

import os
import sys

from dotenv import load_dotenv # type: ignore

from atomic_sdk import AtomicAPIError, AtomicClient

load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")

CONFIRM_TOKEN = "I-UNDERSTAND-THIS-WILL-WIPE-THE-DESTINATION"


def main() -> None:
    if not API_KEY or not CLIENT_ID:
        print("Error: set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        sys.exit(1)

    if len(sys.argv) >= 2:
        domain = sys.argv[1]
    elif SITE_DOMAIN:
        domain = SITE_DOMAIN
    else:
        print("Usage: python examples/sites/08_allow_ssh_migration.py <site_domain>")
        sys.exit(1)

    print(f"\n⚠️  This will permanently mark '{domain}' as a migration target.")
    print("    The destination's files and database WILL be overwritten when the")
    print("    migration runs. This action cannot be undone.\n")
    typed = input(f"Type {CONFIRM_TOKEN!r} to continue: ").strip()
    if typed != CONFIRM_TOKEN:
        print("Aborted: confirmation token did not match.")
        sys.exit(1)

    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        result = client.sites.allow_ssh_migration(domain=domain)
    except AtomicAPIError as exc:
        print(f"❌ API error: {exc}")
        sys.exit(1)

    ready = result.get("ready_for_migration")
    if ready:
        print(f"✅ '{domain}' is now ready to receive an SSH migration.")
    else:
        # API documents `false` when the site already has a migration attached.
        print(f"⚠️  Site '{domain}' is not migration-ready (response: {result}).")
        print("   This usually means a migration is already attached to the site.")


if __name__ == "__main__":
    main()
