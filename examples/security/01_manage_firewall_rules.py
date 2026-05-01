"""
Example: Manage Site Egress Firewall Rules

Walks through the full lifecycle of an egress firewall rule for a single site:
list existing rules, add a new rule (TCP allow to a CIDR), verify it shows up,
then remove it. Mirrors the structure of `examples/edge_cache/01_manage_cache.py`.

The WP Cloud `firewall-rules` API controls outbound traffic from a site's PHP
workers. It is *not* a WAF and does *not* govern SSH ingress.

Usage:
    python 01_manage_firewall_rules.py [--domain example.com]
"""

import os
import argparse

from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
DEFAULT_DOMAIN = os.environ.get("SITE_DOMAIN")

# A safe, RFC 5737 documentation prefix — guaranteed never to route to a real
# host, so the demo rule cannot accidentally affect production traffic.
DEMO_DESTINATION = "203.0.113.10/32"
DEMO_PORT = 3306
DEMO_PROTOCOL = "tcp"
DEMO_ACTION = "allow"


def _print_rule(rule: dict, prefix: str = "  - ") -> None:
    print(
        f"{prefix}rule_id={rule.get('rule_id')} "
        f"{rule.get('action')} {rule.get('protocol')}/{rule.get('port')} "
        f"to {rule.get('destination')} ({rule.get('direction')})"
    )


def main():
    parser = argparse.ArgumentParser(description="Manage egress firewall rules on WP Cloud.")
    parser.add_argument("--domain", default=DEFAULT_DOMAIN, help="Target domain (defaults to SITE_DOMAIN env var)")
    args = parser.parse_args()

    if not API_KEY or not CLIENT_ID:
        print("Error: ATOMIC_API_KEY and ATOMIC_CLIENT_ID must be set in your .env file.")
        return

    if not args.domain:
        print("Error: Domain must be provided via --domain or SITE_DOMAIN env var.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
    new_rule_id = None

    try:
        # --- [1/4] Confirm the site exists ---
        print(f"\n--- Looking for site '{args.domain}' to manage its firewall rules ---")
        site = client.sites.get(domain=args.domain)
        site_id = site.atomic_site_id
        print(f"Found site ID: {site_id}.")

        # --- [2/4] List the current rules ---
        print(f"\n--- [1/4] Listing existing firewall rules ---")
        rules_before = client.security.list_rules(site_id=site_id)
        if rules_before:
            print(f"  - Found {len(rules_before)} existing rule(s):")
            for rule in rules_before:
                _print_rule(rule)
        else:
            print("  - No existing rules.")

        # --- [3/4] Add a demo rule ---
        print(
            f"\n--- [2/4] Adding rule: "
            f"{DEMO_ACTION} {DEMO_PROTOCOL}/{DEMO_PORT} to {DEMO_DESTINATION} ---"
        )
        new_rule = client.security.add_rule(
            action=DEMO_ACTION,
            protocol=DEMO_PROTOCOL,
            port=DEMO_PORT,
            destination=DEMO_DESTINATION,
            site_id=site_id,
            # direction defaults to "egress"; passing it explicitly for clarity:
            direction="egress",
        )
        new_rule_id = new_rule.get("rule_id")
        if not new_rule_id:
            raise RuntimeError("API did not return a rule_id for the newly added rule.")
        print(f"  - ✅ Rule created with rule_id={new_rule_id}.")

        # --- [4/4] Verify and remove ---
        print(f"\n--- [3/4] Verifying the new rule appears in the list ---")
        match = client.security.find_rule(site_id=site_id, rule_id=new_rule_id)
        if match:
            print("  - ✅ Verification successful:")
            _print_rule(match, prefix="    ")
        else:
            print(f"  - ❌ Verification failed: rule_id={new_rule_id} not found in list.")

    except NotFoundError:
        print(f"Error: Site '{args.domain}' not found. Please run '01_create_and_get_site.py' first.")
    except (AtomicAPIError, RuntimeError, ValueError) as e:
        print(f"\nAn error occurred during the firewall rule workflow: {e}")

    finally:
        # --- Cleanup: remove the demo rule if it was created ---
        if new_rule_id is not None:
            print(f"\n--- [4/4] Cleanup: removing demo rule rule_id={new_rule_id} ---")
            try:
                client.security.remove_rule(rule_id=new_rule_id, domain=args.domain)
                print("  - ✅ Demo rule removed.")
            except NotFoundError:
                print("  - ⚪ Rule already gone — nothing to remove.")
            except AtomicAPIError as e:
                print(f"  - ❌ Failed to remove demo rule: {e}")


if __name__ == "__main__":
    main()
