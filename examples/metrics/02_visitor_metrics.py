import os
import time
from dotenv import load_dotenv
from atomic_sdk import AtomicClient, AtomicAPIError

# --- Configuration & Helper ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")

def print_metric_results(title: str, results: dict):
    """A helper function to print non-empty metric query results nicely."""
    print(f"\n--- {title} ---")
    if not results or "periods" not in results:
        print("  - No data returned for this query.")
        return

    meta = results.get("_meta", {})
    print(f"  - Query Time: {meta.get('took')}ms")
    print(f"  - Resolution: {meta.get('resolution')}s per period")

    # --- THIS IS THE KEY CHANGE ---
    # Filter out periods where the dimension dictionary is empty
    active_periods = [p for p in results.get("periods", []) if p.get("dimension")]

    if not active_periods:
        print("  - No activity found in the selected time range.")
        return

    print(f"\n  - Found {len(active_periods)} active period(s):")
    for period in active_periods:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(period.get('timestamp')))
        data = period.get('dimension', {})
        print(f"    - {timestamp} UTC: {data}")

def main():
    """Demonstrates querying various visitor-related metrics."""
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    # Define a time window that ended in the past to account for data ingestion delay.
    DATA_DELAY_SECONDS = 30 * 60
    QUERY_DURATION_SECONDS = 24 * 60 * 60 # Last 24 hours
    end_time = int(time.time()) - DATA_DELAY_SECONDS
    start_time = end_time - QUERY_DURATION_SECONDS

    print(f"\n--- Querying Visitor Metrics for site '{SITE_DOMAIN}' (Last 24 Hours, ending 30 mins ago) ---")
    try:
        # --- Example 1: Requests by Country ---
        by_country = client.metrics.query(
            start=start_time, end=end_time, query_type="site", key=SITE_DOMAIN,
            metric="requests", dimension="visitor_country_code"
        )
        print_metric_results("Requests by Country Code", by_country)

        # --- Example 2: Requests by Device Type ---
        by_device = client.metrics.query(
            start=start_time, end=end_time, query_type="site", key=SITE_DOMAIN,
            metric="requests", dimension="visitor_device_type"
        )
        print_metric_results("Requests by Device Type", by_device)

        # --- Example 3: Requests by Browser ---
        by_browser = client.metrics.query(
            start=start_time, end=end_time, query_type="site", key=SITE_DOMAIN,
            metric="requests", dimension="visitor_browser"
        )
        print_metric_results("Requests by Browser", by_browser)

        # --- Example 4: Requests by Operating System ---
        by_os = client.metrics.query(
            start=start_time, end=end_time, query_type="site", key=SITE_DOMAIN,
            metric="requests", dimension="visitor_os"
        )
        print_metric_results("Requests by Operating System", by_os)

    except AtomicAPIError as e:
        print(f"\nAn API error occurred: {e}")

if __name__ == "__main__":
    main()
