"""
Example: Install Custom SSL Certificate

This script validates, stages, and activates a custom SSL certificate for a site.
It accepts certificate and private key files as command-line arguments.

Usage:
    python 01_install_certificate.py --cert /path/to/cert.pem --key /path/to/key.pem [--domain example.com]
"""

import os
import argparse
import sys
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# Load environment variables
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
DEFAULT_DOMAIN = os.environ.get("SITE_DOMAIN")


def read_file(path):
    """Reads content from a file."""
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: File not found: {path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Install a custom SSL certificate on WP Cloud.")
    parser.add_argument("--cert", required=True, help="Path to the PEM-encoded certificate file")
    parser.add_argument("--key", required=True, help="Path to the PEM-encoded private key file")
    parser.add_argument("--domain", default=DEFAULT_DOMAIN, help="Target domain (defaults to SITE_DOMAIN env var)")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, do not install")

    args = parser.parse_args()

    if not API_KEY or not CLIENT_ID:
        print("Error: ATOMIC_API_KEY and ATOMIC_CLIENT_ID must be set in your .env file.")
        return

    if not args.domain:
        print("Error: Domain must be provided via --domain or SITE_DOMAIN env var.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    # Read files
    cert_content = read_file(args.cert)
    key_content = read_file(args.key)
    print(f"Read certificate ({len(cert_content)} bytes) and key ({len(key_content)} bytes).")

    try:
        # 1. Validate
        print(f"\n--- Validating Certificate for '{args.domain}' ---")
        validation = client.custom_certificates.validate(
            certificate=cert_content,
            private_key=key_content,
            domain=args.domain
        )
        
        is_valid = validation.get('valid')
        if not is_valid:
            print("❌ Validation Failed!")
            if 'errors' in validation:
                print("Errors:")
                for err in validation['errors']:
                    print(f"  - {err}")
            return
        
        print("✅ Certificate is valid.")
        if args.validate_only:
            print("Validate-only mode enabled. Exiting.")
            return

        # 2. Stage and Activate
        print(f"\n--- Staging and Activating Certificate ---")
        result = client.custom_certificates.stage_and_activate(
            certificate=cert_content,
            private_key=key_content,
            domain=args.domain
        )
        
        cert_id = result.get('certificate_id')
        print(f"✅ Success! Certificate {cert_id} has been activated for: {result.get('domains')}")

    except NotFoundError:
        print(f"Error: Site '{args.domain}' not found.")
    except AtomicAPIError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")


if __name__ == "__main__":
    main()
