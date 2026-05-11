"""
Example: Manage WP-Cron Entries

This script demonstrates the complete lifecycle of a cron entry:
  1. List existing cron entries.
  2. Add a new cron entry.
  3. Verify the entry appears in the list.
  4. Remove the entry.

Usage:
    python 01_manage_cron.py [--domain example.com | --site-id 12345]
"""

import os
import argparse
from dotenv import load_dotenv # type: ignore
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# Load environment variables
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
DEFAULT_DOMAIN = os.environ.get("SITE_DOMAIN")


def main():
    parser = argparse.ArgumentParser(description="Manage WP-Cron entries on a WP Cloud site.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--domain", default=DEFAULT_DOMAIN, help="Target domain (defaults to SITE_DOMAIN env var)")
    group.add_argument("--site-id", type=int, help="Atomic site ID")
    args = parser.parse_args()

    if not API_KEY or not CLIENT_ID:
        print("Error: ATOMIC_API_KEY and ATOMIC_CLIENT_ID must be set in your .env file.")
        return

    site_id = args.site_id
    domain = args.domain if not site_id else None

    if not site_id and not domain:
        print("Error: Provide a target via --domain or --site-id (or set SITE_DOMAIN in .env).")
        return

    target = f"domain={domain}" if domain else f"site_id={site_id}"
    print(f"--- Initializing AtomicClient (target: {target}) ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    new_cron_id = None
    removed = False

    try:
        # 1. List existing cron entries
        print("\n--- Step 1: List existing cron entries ---")
        entries = client.cron.list(site_id=site_id, domain=domain)
        if entries:
            print(f"Found {len(entries)} existing entry/entries:")
            for e in entries:
                print(f"  [{e.get('cron_id')}] schedule={e.get('schedule')}  cmd={e.get('command')}")
        else:
            print("No cron entries found.")

        # 2. Add a new cron entry
        print("\n--- Step 2: Add a new cron entry ---")
        add_result = client.cron.add(
            schedule="hourly",
            command="wp cron event run --due-now",
            site_id=site_id,
            domain=domain,
        )
        new_cron_id = add_result.get("cron_id")
        print(f"✅ Created cron entry with cron_id={new_cron_id}")

        # 3. Verify the entry appears in the list
        print("\n--- Step 3: Verify entry appears in list ---")
        found = client.cron.find(cron_id=new_cron_id, site_id=site_id, domain=domain)
        if found:
            print(f"✅ Verified: {found}")
        else:
            print("⚠️  Entry not found in list after adding (may need a moment to propagate).")

        # 4. Remove the entry
        print("\n--- Step 4: Remove the cron entry ---")
        client.cron.remove(cron_id=new_cron_id, site_id=site_id, domain=domain)
        removed = True
        print(f"✅ Removed cron entry cron_id={new_cron_id}")

        # Confirm removal
        still_there = client.cron.find(cron_id=new_cron_id, site_id=site_id, domain=domain)
        if still_there:
            print("⚠️  Entry still present after removal.")
        else:
            print("✅ Confirmed: entry is no longer in the list.")

    except NotFoundError:
        print(f"Error: Site not found ({target}).")
    except AtomicAPIError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")
    finally:
        if new_cron_id is not None and not removed:
            try:
                print(f"\n--- Cleanup: Remove cron entry cron_id={new_cron_id} ---")
                client.cron.remove(cron_id=new_cron_id, site_id=site_id, domain=domain)
                print(f"✅ Cleanup removed cron entry cron_id={new_cron_id}")
            except AtomicAPIError as e:
                print(f"Cleanup API Error: {e}")
            except Exception as e:
                print(f"Cleanup Unexpected Error: {e}")


if __name__ == "__main__":
    main()
