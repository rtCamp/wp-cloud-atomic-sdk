import os
import time
from dotenv import load_dotenv
from typing import Dict, Any, List
from atomic_sdk import AtomicClient, AtomicAPIError, NotFoundError

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# This example assumes the site from '01_create_and_get_site.py' exists.
SITE_DOMAIN = os.environ.get("SITE_DOMAIN")


def print_metric_results(title: str, results: Dict[str, Any]):
    """A helper function to print metric query results nicely."""
    print(f"\n--- {title} ---")
    if not results or "periods" not in results:
        print("  - No data returned for this query.")
        return

    meta = results.get("_meta", {})
    print(f"  - Query Time: {meta.get('took')}ms")
    print(f"  - Resolution: {meta.get('resolution')} seconds per period")
    print(f"  - Dimension: {meta.get('dimension')}")
    print(f"  - Metric: {meta.get('metric')}")

    periods = results.get("periods", [])
    if not periods:
        print("  - No data points in the selected time range.")
        return

    print("\n  - Sample Data Points:")
    # Print the first and last few data points to give a summary

    for period in periods[:3]: # Print first 3
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(period.get('timestamp')))
        data = period.get('dimension', {})
        print(f"    - {timestamp} UTC: {data}")

    if len(periods) > 6:
        print("      ...")

    if len(periods) > 3:
        for period in periods[-3:]: # Print last 3
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(period.get('timestamp')))
            data = period.get('dimension', {})
            print(f"    - {timestamp} UTC: {data}")

def main():
    """
    Demonstrates various ways to query the metrics endpoint for a specific site.
    """
    if not API_KEY or not CLIENT_ID or not SITE_DOMAIN:
        print("Error: Please set ATOMIC_API_KEY and ATOMIC_CLIENT_ID in your .env file.")
        return

    print("--- Initializing AtomicClient ---")
    client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)

    try:
        # --- 1. Define time range for queries (e.g., the last 6 hours) ---
        end_time = int(time.time())
        start_time = end_time - (6 * 60 * 60) # 6 hours ago

        print(f"\n--- Querying metrics for site '{SITE_DOMAIN}' ---")
        print(f"--- Time range: {time.strftime('%Y-%m-%d %H:%M', time.gmtime(start_time))} to {time.strftime('%Y-%m-%d %H:%M', time.gmtime(end_time))} UTC ---")

        # --- Example 2: Total Requests by HTTP Status Code ---
        requests_by_status = client.metrics.query(
            start=start_time,
            end=end_time,
            query_type="site",
            key=SITE_DOMAIN,
            metric="requests",
            dimension="http_status"
        )
        print_metric_results("Total Requests by HTTP Status", requests_by_status)

        # --- Example 3: Average PHP Response Time ---
        php_response_time = client.metrics.query(
            start=start_time,
            end=end_time,
            query_type="site",
            key=SITE_DOMAIN,
            metric="php_response_time",
            dimension="http_host"
        )
        print_metric_results("Average PHP Response Time", php_response_time)

        # --- Example 4: Summarized Bandwidth ---
        bandwidth_summary = client.metrics.query(
            start=start_time,
            end=end_time,
            query_type="site",
            key=SITE_DOMAIN,
            metric="response_bytes",
            dimension="http_host",
            summarize=True
        )

        print("\n--- Total Bandwidth (Summarized) ---")
        total_bytes = None
        if isinstance(bandwidth_summary, dict) and "periods" in bandwidth_summary and len(bandwidth_summary["periods"]) > 0:
            summary_period = bandwidth_summary["periods"][0]
            if "dimension" in summary_period:
                # Sum the values from the dimension dictionary. Cast to float for safety.
                total_bytes = sum(float(v) for v in summary_period["dimension"].values())

        if total_bytes is not None:
            total_mb = total_bytes / (1024 * 1024)
            print(f"  - Total bytes served: {int(total_bytes)} bytes (~{total_mb:.2f} MB)")
        else:
            print("  - Could not determine total from the summary response.")

    except NotFoundError:
        print(f"Error: Site '{SITE_DOMAIN}' not found. Please run '01_create_and_get_site.py' first.")
    except (AtomicAPIError, RuntimeError) as e:
        print(f"\nAn error occurred during the metrics query workflow: {e}")

if __name__ == "__main__":
    main()
