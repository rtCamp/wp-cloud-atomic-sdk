import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# Load credentials from .env
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

"""
Example: List all sites for your account using the Atomic SDK.
"""
try:
    sites = client.sites.list()
    print(f"Found {len(sites)} sites.")
    for site in sites:
        print(f"- Site ID: {site['atomic_site_id']}, Domain: {site['domain_name']}")
except NotFoundError:
    print("No sites found for this account.")
except AtomicAPIError as e:
    print(f"API error occurred: {e}")
