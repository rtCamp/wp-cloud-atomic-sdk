"""
Example: Manage Custom SSL Certificates

This script allows you to list, deactivate, and delete custom SSL certificates.

Usage:
    python 02_manage_certificate.py [list|deactivate|delete] [--domain example.com] [--id CERT_ID]
"""

import os
import argparse
import sys
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
DEFAULT_DOMAIN = os.environ.get("SITE_DOMAIN")


def main():
    parser = argparse.ArgumentParser(description="Manage custom SSL certificates on WP Cloud.")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute', required=True)

    # List command
    list_parser = subparsers.add_parser('list', help='List certificates')
    list_parser.add_argument("--domain", default=DEFAULT_DOMAIN, help="Target domain")
    list_parser.add_argument("--status", choices=['active', 'staged', 'all'], help="Filter by status")

    # Active command
    active_parser = subparsers.add_parser('active', help='Get active certificate')
    active_parser.add_argument("--domain", default=DEFAULT_DOMAIN, help="Target domain")
    active_parser.add_argument("--id-only", action="store_true", help="Only output the certificate ID (for scripting)")

    # Deactivate command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate a certificate')
    deactivate_parser.add_argument("--domain", default=DEFAULT_DOMAIN, help="Target domain")
    deactivate_parser.add_argument("--id", type=int, required=True, help="Certificate ID to deactivate")

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a certificate')
    delete_parser.add_argument("--domain", default=DEFAULT_DOMAIN, help="Target domain")
    delete_parser.add_argument("--id", type=int, required=True, help="Certificate ID to delete")

    args = parser.parse_args()

    if not API_KEY or not CLIENT_ID:
        print("Error: ATOMIC_API_KEY and ATOMIC_CLIENT_ID must be set in your .env file.")
        return

    domain = args.domain
    if not domain:
        print("Error: Domain must be provided via --domain or SITE_DOMAIN env var.")
        return

    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        if args.command == 'list':
            print(f"--- Listing certificates for '{domain}' ---")
            result = client.custom_certificates.list(domain=domain, status=args.status)
            certs = result.get('certificates', [])
            
            if not certs:
                print("No certificates found.")
            
            for cert in certs:
                status_icon = "🟢" if cert.get('is_active') else "⚪"
                print(f"{status_icon} ID: {cert.get('ssl_custom_certificate_id')} | "
                      f"Issued To: {cert.get('issued_to')} | "
                      f"Expires: {cert.get('expires_at')}")

        elif args.command == 'active':
            cert = client.custom_certificates.get_active(domain=domain)
            if cert:
                cert_id = cert.get('ssl_custom_certificate_id')
                if getattr(args, 'id_only', False):
                    print(cert_id)
                else:
                    print(f"--- Getting active certificate for '{domain}' ---")
                    print(f"🟢 Active Certificate ID: {cert_id}")
                    print(f"Issued To: {cert.get('issued_to')}")
            else:
                if not getattr(args, 'id_only', False):
                    print(f"--- Getting active certificate for '{domain}' ---")
                    print("⚪ No active certificate found.")

        elif args.command == 'deactivate':
            print(f"--- Deactivating certificate ID {args.id} on '{domain}' ---")
            client.custom_certificates.deactivate(certificate_id=args.id, domain=domain)
            print("✅ Certificate deactivated.")

        elif args.command == 'delete':
            print(f"--- Deleting certificate ID {args.id} on '{domain}' ---")
            client.custom_certificates.delete(certificate_id=args.id, domain=domain)
            print("✅ Certificate deleted.")

    except NotFoundError:
        print(f"Error: Site '{domain}' or certificate ID not found.")
    except AtomicAPIError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")


if __name__ == "__main__":
    main()
