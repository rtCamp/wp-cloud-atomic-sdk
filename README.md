# Python SDK for the WP.cloud Atomic API

[![PyPI version](https://badge.fury.io/py/atomic-sdk.svg)](https://badge.fury.io/py/atomic-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This SDK provides a direct and efficient Python interface for the [WP.cloud Atomic API](https://wp.cloud/docs/api/). It handles the underlying complexities of authentication, API requests, and asynchronous job polling, providing a clean, object-oriented interface for managing your hosting resources.

This allows you to build automation and integrations without writing boilerplate code, focusing instead on your application's logic.

[▶️ Watch the example video: demo.mp4](https://github.com/user-attachments/assets/58ec3dd2-0515-4159-847a-56476897a23f)

For more examples see the [`examples/`](./examples) directory.

## ✨ Features

-   **Complete API Coverage**: Access every API resource group through dedicated client objects (e.g., `client.sites`, `client.backups`).
-   **Simplified Site Management**: Use clear methods to create, retrieve, list, update, and delete sites.
-   **Asynchronous Job Handling**: Long-running operations return a `Job` object. You can poll it or use the built-in `.wait()` method to block until completion.
-   **Specific Error Handling**: The SDK raises distinct exceptions for different API errors (`NotFoundError`, `InvalidRequestError`), making your code more resilient.
-   **Validated Data Models**: API responses are parsed into Pydantic models, providing type-hinting, validation, and simple attribute-based access to data.
-   **Intelligent Helpers**: The SDK abstracts away complexities such as building form-data payloads, handling different SSH connection types, and managing API inconsistencies.

This SDK provides clients for:
-   📂 **Sites**: Full lifecycle management.
-   🗄️ **Backups**: Create, list, download, and delete backups.
-   🔑 **SSH**: Manage site-specific users, client-wide keys, and aliases.
-   📊 **Metrics**: Query detailed performance and visitor analytics.
-   🚀 **Tasks**: Run bulk operations across all your sites.
-   🌐 **Edge Cache**: Control caching and DDoS protection.
-   ⚙️ **Servers**: Get information on available datacenters and PHP versions.
-   👤 **Client**: Manage account-wide settings like webhooks.
-   ✉️ **Email**: Check the email sending blocklist.
-   🛠️ **Utility**: Test API connectivity and authentication.

## ⚙️ Installation

Until this package is published on PyPI, you can install it locally for development and testing.

**Requirements:** Python 3.7+

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/rtCamp/wp-cloud-atomic-sdk.git
    cd wp-cloud-atomic-sdk
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install in Editable Mode:**
    Install the package with its development dependencies. The `-e` flag links the installation to your source code, so any changes you make are immediately available.
    ```bash
    pip install -e ".[dev]"
    ```

## 🚀 Getting Started

First, instantiate the main client with your API key and client identifier. For security, load these from environment variables.

```python
import os
from dotenv import load_dotenv
from atomic_sdk import AtomicClient

# Load credentials from a .env file
load_dotenv()
API_KEY = os.environ.get("ATOMIC_API_KEY")
CLIENT_ID = os.environ.get("ATOMIC_CLIENT_ID")

# Initialize the main client
client = AtomicClient(api_key=API_KEY, client_id_or_name=CLIENT_ID)
```

## 📝 Usage Examples

Once the client is initialized, you can access all API resource groups as attributes (e.g., `client.sites`, `client.backups`).

### 1. Listing All Sites

A common first step is to list all sites associated with your client account.

```python
from atomic_sdk import AtomicAPIError, NotFoundError

try:
    sites = client.sites.list()
    print(f"Found {len(sites)} sites.")
    for site in sites:
        print(f"- Site ID: {site['atomic_site_id']}, Domain: {site['domain_name']}")
except NotFoundError:
    print("No sites found for this account.")
except AtomicAPIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

### 2. Getting a Single Site's Details

Retrieve details for a specific site using either its domain or its Atomic Site ID. The SDK returns a `Site` object with type-hinted attributes.

```python
from atomic_sdk import NotFoundError
from atomic_sdk.models import Site

try:
    # Get by site ID
    site_details: Site = client.sites.get(site_id=123456789)
    print(f"Domain for site 123456789: {site_details.domain_name}")
    print(f"PHP Version: {site_details.php_version}")

except NotFoundError:
    print("The specified site could not be found.")
```

### 3. Creating a New Site (Asynchronous Job)

Creating a site is an asynchronous operation. The SDK returns a `Job` object that you can use to poll for its status.

```python
import time
from atomic_sdk import InvalidRequestError
from atomic_sdk.models import Job

try:
    print("Starting site creation...")
    new_site_job: Job = client.sites.create(
        domain_name="new-sdk-site.com", # Replace with your actual site domain
        admin_user="sdk_admin",
        admin_email="admin@new-sdk-site.com",
        php_version="8.3"
    )

    print(f"Site creation job started with ID: {new_site_job.job_id}")
    print("Waiting for job to complete...")

    # Poll the job status until it's finished
    while True:
        status = new_site_job.status()
        print(f"  - Job status: {status["_status"]}")

        job_state = status["_status"] if isinstance(status, dict) and "_status" in status else status

        if job_state in ("success", "failed", "error"):
            final_status = job_state
            break

        time.sleep(10) # Wait for 10 seconds before polling again

    if final_status == "success":
        print(f"Site '{new_site_job.domain_name}' was created successfully!")
    else:
        print(f"Site creation failed with status: {final_status}")

except InvalidRequestError as e:
    print(f"Error creating site: {e}")
```

### 4. Managing Site Software

Install, activate, or remove plugins and themes. This is also an asynchronous job.

```python
actions = {
    "plugins/akismet/latest": "activate",
    "themes/twentytwentyfour/latest": "install",
}

software_job = client.sites.manage_software(
    domain="new-sdk-site.com", # Replace with your actual site domain
    software_actions=actions
)

print(f"Software management job ({software_job.job_id}) has been queued.")
# You can use software_job.wait() or a polling loop here as well
```

### 5. Purging the Edge Cache

A simple, one-line command to purge a site's edge cache.

```python
client.edge_cache.purge(domain="new-sdk-site.com")
print("Edge cache purge command sent for new-sdk-site.com.")
```

### 6. Error Handling

The SDK uses custom exceptions to make error handling clean and predictable.

```python
from atomic_sdk import AtomicAPIError, NotFoundError

try:
    # Attempt to get a site that does not exist
    client.sites.get(site_id=999999999)
except NotFoundError:
    print("Caught a NotFoundError, as expected.")
except AtomicAPIError as e:
    # Catch any other API-related error
    print(f"An API error occurred with status {e.status_code}: {e.message}")
```

## 📚 In-Depth Examples

For detailed, runnable scripts covering every feature of the API—from managing backups to running bulk WP-CLI tasks—please see the [`examples/`](./examples) directory and its comprehensive [`README.md`](./examples/README.md).

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Does this interest you?

<a href="https://rtcamp.com/"><img src="https://rtcamp.com/wp-content/uploads/sites/2/2019/04/github-banner@2x.png" alt="Join us at rtCamp, we specialize in providing high performance enterprise WordPress solutions"></a>
