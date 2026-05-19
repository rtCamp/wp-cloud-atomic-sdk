# Atomic SDK: Examples

Welcome to the examples directory! Each script here is a runnable, real-world demonstration of how to use the `atomic-sdk` to interact with a specific part of the WP.cloud Atomic API.

The scripts are numbered to suggest a logical order for learning the API, starting from basic checks and moving to more complex operations.

## 🚀 Getting Started

Before running any examples, you must set up your environment.

### 1. Install Dependencies
Ensure you have installed the SDK in editable mode with the `[dev]` dependencies, which includes `python-dotenv`. From the project root:
```bash
pip install -e ".[dev]"
```

### 2. Create Your `.env` File
This project uses a `.env` file to securely manage your API credentials.
1.  Copy the example file:
    ```bash
    cp .env.example .env
    ```
2.  Edit the new `.env` file and add your credentials:
    ```
    # Your main Atomic API Key
    ATOMIC_API_KEY="key_goes_here"
    
    # Your client identifier string (e.g., "myhostingco")
    ATOMIC_CLIENT_ID="your_client_id_goes_here"

    # The domain name you will use for testing the site examples
    SITE_DOMAIN="sdk-test.yourdomain.com"
    ```
All example scripts will automatically load these variables.

## 📖 A Step-by-Step User Story

Here is a recommended workflow for using the SDK, following the numbered example scripts.

## ✅ Step 0: Test Your Connection
*   **Goal:** Confirm your API key is valid and you can reach the platform.
*   **Run:** `python examples/utility/01_test_api_connectivity.py`
*   **Shows:**
    *   How to initialize the `AtomicClient`.
    *   Using the `client.utility.test_status()` endpoint for a basic success (200 OK) check.

## 🔧 Step 1: Configure Client Settings
*   **Goal:** Set up account-wide configurations, such as a webhook URL for receiving notifications.
*   **Run:** `python examples/client/01_manage_client_meta.py`
*   **Shows:**
    *   Getting a client-level metadata value using `client.client.get_meta()`.
    *   Handling the expected `NotFoundError` if the key has never been set.
    *   Setting up webhook via `client.client.set_meta()` .
    *   Verifying the change and optional prompt for cleaning it up via `client.client.remove_meta()`.

## 🛫 Step 2: Perform Pre-Flight Checks for a New Site
*   **Goal:** Before creating a site, ensure the domain is available and find out which IPs to point your DNS to.
*   **Run:** `python examples/sites/00_check_can_host_domain.py`
*   **Shows:**
    *   Checking if a domain is already in use on the platform with `client.sites.check_can_host_domain()`.
    *   Retrieving the target IP addresses for your DNS A records using `client.sites.get_ips()`.
    *   Comparing the required IPs with the domain's current DNS records.

## 🖥️🌐 Step 3: Create and Verify Your First Site
*   **Goal:** Provision a new site for testing and confirm its settings were applied correctly.
*   **Run:** `python examples/sites/01_create_and_get_site.py`
*   **Shows:**
    *   Checking if a site already exists with `client.sites.get()` to prevent errors.
    *   Creating a new site with `client.sites.create()`, specifying parameters like `php_version`, `space_quota`, and custom `meta` data.
    *   Using a helper function to poll the returned `Job` object until the creation is successful.
    *   Retrieving the full site details with `client.sites.get(extra=True)` and verifying all settings.

## ⚙️ Step 4: Manage Your New Site
Once your site exists, you can perform various management tasks.

### 💿 Manage Software
*   **Run:** `python examples/sites/02_manage_software.py`
*   **Shows:**
    *   Defining a dictionary of software actions (e.g., install a theme, install a plugin).
    *   Executing the changes with `client.sites.manage_software()` and waiting for the job to complete.
    *   Running a subsequent job to activate the newly installed software.

### 🏷️ Manage Domain Aliases
*   **Run:** `python examples/sites/03_manage_aliases.py`
*   **Shows:**
    *   Adding a secondary domain to a site with `client.sites.add_alias()`.
    *   Verifying the addition by retrieving all aliases with `client.sites.list_aliases()`.
    *   Removing the alias with `client.sites.remove_alias()` and verifying the removal.

### 🔧 Manage Metadata
*   **Run:** `python examples/sites/04_manage_metadata.py`
*   **Shows:**
    *   Reading a property directly from the main `Site` object (`site.wp_version`).
    *   Reading specific metadata keys like `space_quota` with `client.sites.get_meta()`.
    *   Updating a metadata key (`default_php_conns`) with `client.sites.update_meta()`.
    *   Verifying the change and reverting it in a `finally` block for cleanup.

### 🔒 Manage SSL
*   **Run:** `python examples/sites/05_manage_ssl.py`
*   **Shows:**
    *   Fetching detailed SSL certificate information with `client.sites.get_ssl_info()`.
    *   Retrying a failed SSL provisioning attempt with `client.sites.retry_ssl_provisioning()`.
    *   Managing HSTS settings like `includeSubDomains` with `client.sites.set_hsts_subdomain()`.

### 🔐 Manage Custom SSL Certificates
*   **Run:** `python examples/custom_certificates/01_install_certificate.py --cert <file> --key <file>`
*   **Shows:**
    *   Validating a certificate pair with `client.custom_certificates.validate()`.
    *   Staging and activating in one step with `client.custom_certificates.stage_and_activate()`.
*   **Run:** `python examples/custom_certificates/02_manage_certificate.py list`
*   **Shows:**
    *   Listing all certificates for a site.
    *   Getting the currently active certificate with `active` subcommand.
    *   Subcommands for `deactivate` and `delete` to manage specific certificate IDs.

### 🗃️ Access the Database
*   **Run:** `python examples/sites/06_get_phpmyadmin_url.py`
*   **Shows:**
    *   Generating a secure, time-limited, single-use login URL for phpMyAdmin using `client.sites.get_phpmyadmin_url()`.

## 🗄️ Step 5: Manage Backups
Learn how to create, list, download, and delete backups. Note that on-demand backup creation is a "fire-and-forget" operation; the API does not provide a way to poll its status.

### ➕ Create and List Backups
*   **Run:** `python examples/backups/01_create_and_list_backups.py`
*   **Shows:**
    *   Listing all existing backups for a site with `client.backups.list()`.
    *   Requesting a new on-demand database backup with `client.backups.create(backup_type="db")`.
    *   Accessing the `request_id` from the returned `BackupJob` object.

### 📥 Get and Download a Backup
*   **Run:** `python examples/backups/02_get_and_download_backup.py`
*   **Shows:**
    *   Finding the most recent backup by sorting the list.
    *   Getting specific metadata for that backup with `client.backups.info()`.
    *   Downloading the raw backup file content as bytes with `client.backups.get()`.
    *   Saving the downloaded content to a local file.

### 🗑️ Delete an On-Demand Backup
*   **Run:** `python examples/backups/99_delete_ondemand_backup.py`
*   **Shows:**
    *   Finding a specific on-demand backup to delete from the list.
    *   Requesting its deletion with `client.backups.delete()`.

## 🔑 Step 6: Manage SSH Access
Learn the different methods for granting SSH and SFTP access.

### 👤 Manage Site-Specific Users
*   **Run:** `python examples/ssh/01_manage_site_ssh_users.py`
*   **Shows:** How to add, list, update, and remove a standard SFTP/SSH user for a single site using password authentication.
*   **Run:** `python examples/ssh/02_manage_public_keys.py`
*   **Shows:** How to create a more secure, key-based user for a single site and disable password login.

### 🔌 Disconnect Active Users
*   **Run:** `python examples/ssh/03_disconnect_users.py`
*   **Shows:** How to forcefully terminate all active SSH and SFTP sessions for a site with `client.ssh.disconnect_all_users()`.

### 🤖 Manage Client-Wide Automation Keys
*   **Run:** `python examples/ssh/04_manage_client_keys.py`
*   **Shows:**
    *   Adding a powerful, account-wide key for automation using `client.ssh.add_client_key()`.
    *   The correct connection method for these keys: `<site-id>@client-ssh.atomicsites.net`.

### 🔗 Manage Reusable Aliasable Keys
*   **Run:** `python examples/ssh/05_manage_aliasable_keys.py`
*   **Shows:**
    *   Using the `client.ssh.alias_pkey` sub-client to create a named, reusable public key (`alias-pkey`).
    *   Updating the alias to point to a new public key.
    *   Verifying the key's fingerprint after each change.


## 📊 Step 7: Explore Metrics & Analytics
Learn how to query the powerful metrics endpoint. Remember that metrics have an ingestion delay, so it's best to query for a time window that ended ~30 minutes ago.

### 📈 General Site Metrics
*   **Run:** `python examples/metrics/01_query_site_metrics.py`
*   **Shows:** A general overview of querying, including requests by HTTP status, average PHP response time, and summarized bandwidth.

### 🧑‍💻 Visitor Metrics
*   **Run:** `python examples/metrics/02_visitor_metrics.py`
*   **Shows:** How to segment traffic by visitor country code, device type, browser, and operating system.

### 🐘 PHP Performance Metrics
*   **Run:** `python examples/metrics/03_php_metrics.py`
*   **Shows:** How to check PHP performance, including average worker usage, CPU time, and request burst/limit percentages.

### 👁️ Uniques and Views
*   **Run:** `python examples/metrics/04_uniques_and_views_metrics.py`
*   **Shows:** How to query for daily aggregated unique visitors and page views.

### 🐬 MySQL Performance Metrics
*   **Run:** `python examples/metrics/05_mysql_metrics.py`
*   **Shows:** How to monitor database performance, including concurrent connections, slow queries, and rows read/written.

### 📦 Container (CGroup) Metrics
*   **Run:** `python examples/metrics/06_cgroup_metrics.py`
*   **Shows:** How to inspect low-level container resource usage, specifically CPU usage per second.

## 🚀 Step 8: Run Bulk Tasks
Execute an operation across many or all of your sites at once.

### 📦 Bulk Software Management
*   **Run:** `python examples/tasks/01_run_bulk_software_task.py`
*   **Shows:** Creating a task with `client.tasks.create(task_type="software")` to install a plugin on all sites and monitoring its progress.

### 🔍 Bulk File Search
*   **Run:** `python examples/tasks/02_run_bulk_find_files_task.py`
*   **Shows:** Creating a `site-find-files` task to locate a specific file pattern across all sites.

### ⌨️ Bulk WP-CLI Commands
*   **Run:** `python examples/tasks/03_run_bulk_wp_cli_task.py`
*   **Shows:** Creating a `run-wp-cli-command` task to execute a WP-CLI command on all sites and get results via webhook.

## 🍃 Step 9: Explore Other Endpoints
### ⏱️ Manage Cron Entries
*   **Run:** `python examples/cron/01_manage_cron.py [--domain example.com | --site-id 12345]`
*   **Shows:**
    *   Listing all cron entries with `client.cron.list()`.
    *   Adding a new entry with `client.cron.add()` using a named schedule.
    *   Finding a specific entry with `client.cron.find()`.
    *   Removing an entry with `client.cron.remove()`.

### 🌐 Manage Edge Cache
*   **Run:** `python examples/edge_cache/01_manage_cache.py`
*   **Shows:** Using the `client.edge_cache` client to check status, turn caching on/off, purge, and manage defensive (DDoS) mode.

### 🌍 Get Server Information
*   **Run:** `python examples/servers/01_get_server_info.py`
*   **Shows:** Using `client.servers` to list available datacenters and supported PHP versions on the platform.

### 🛡️ Manage Egress Firewall Rules
*   **Run:** `python examples/security/01_manage_firewall_rules.py`
*   **Shows:**
    *   Listing existing egress firewall rules with `client.security.list_rules()`.
    *   Adding an outbound `allow`/`deny` rule with `client.security.add_rule()` (TCP/UDP, port 1-65535, IP/CIDR destination).
    *   Locating a rule by ID, port, destination, etc. with `client.security.find_rule()`.
    *   Removing a rule with `client.security.remove_rule()`.

### ✉️ Check Email Blocklist
*   **Run:** `python examples/email/01_list_blocked_domains.py`
*   **Shows:** Using `client.email` to retrieve a list of domains that have been blocked from sending email.

## 🧹 Step 10: Clean Up
*   **Goal:** Delete the test site created in the examples.
*   **Run:** `python examples/sites/99_delete_site.py`
*   **Shows:** A script that includes a safety prompt and then permanently deletes the test site from your account, waiting for the deletion job to complete.
