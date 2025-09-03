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
    import json
    for site in sites:
        site_type = None
        try:
            data_meta_str = client.sites.get_meta(key="_data", site_id=site["atomic_site_id"])
            if data_meta_str:
                try:
                    unescaped_str = data_meta_str.encode('utf-8').decode('unicode_escape')
                except Exception:
                    unescaped_str = data_meta_str
                try:
                    data_meta = json.loads(unescaped_str)
                    site_type = data_meta.get("v1", {}).get("site_type")
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"❌ ERROR: Could not parse the _data string for site {site['atomic_site_id']}: {e}")
                    print(f"📝 Raw _data string: {repr(data_meta_str)}")
                    site_type = None
        except Exception:
            site_type = None
        print(f"- Site ID: {site['atomic_site_id']}, Domain: {site['domain_name']}, Type: {site_type if site_type else 'billable'}")
except NotFoundError:
    print("No sites found for this account.")
except AtomicAPIError as e:
    print(f"API error occurred: {e}")
