from typing import List, Optional, Literal, Dict, Any, Union

from .base import ResourceClient
from ..exceptions import InvalidRequestError
from ..models import Job, Site


class SitesClient(ResourceClient):
    """
    A client for interacting with the Sites and site-management endpoints.
    """

    # --- Helper for Log Payloads ---
    def _build_log_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Builds the specially-formatted payload for log endpoints."""
        payload = {}
        filters = data.pop('filters', {})

        for key, value in data.items():
            payload[f"data[{key}]"] = value

        if filters and isinstance(filters, dict):
            for f_key, f_values in filters.items():
                if not isinstance(f_values, list):
                    f_values = [f_values]
                for val in f_values:
                    payload[f'data[filter][{f_key}][]'] = val

        return payload

    # --- Core Site Management ---

    def list(self, limit: Optional[int] = None, after: Optional[int] = None) -> List[dict]:
        """
        Lists a client's sites, generally for auditing purposes. Supports pagination.
        Additional site meta keys can be added to the output by specifying them at the
        end of the endpoint URI separated by '/'. This SDK method provides the core listing;
        for detailed meta, use the `get()` or `get_meta()` methods for a specific site.

        Args:
            limit: Optional limit for the number of sites returned.
            after: Optional site ID to return results after (for pagination).

        Returns:
            A list of site data dictionaries.
        """
        params = {}
        if limit:
            params['limit'] = limit
        if after:
            params['after'] = after

        endpoint = f"/get-sites/{self._client_id_or_name}"
        return self._get(endpoint, params=params)

    def get(self, site_id: Optional[int] = None, domain: Optional[str] = None, extra: bool = False) -> Site:
        """
        Get site details by site ID or domain name.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.
            extra: If True, returns additional data (like server_pool and meta)
                   in the .extra field of the returned Site object.

        Returns:
            A Site object containing the site's details.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/get-site/{identifier}"

        if extra:
            endpoint += "/extra"

        response_data = self._get(endpoint)
        return Site.parse_obj(response_data)

    def create(self, admin_user: str, admin_email: str, domain_name: Optional[str] = None, **kwargs) -> Job:
        """
        Creates a new WP Cloud site. This is an asynchronous operation.

        Args:
            admin_user: The WordPress admin username for the new site.
            admin_email: The WordPress admin email for the new site.
            domain_name: The domain name for the site. Required unless `demo_domain` is True.
            **kwargs: Additional parameters for site creation, including:
                - `demo_domain` (bool): If True, generate a demo domain. Default is False.
                - `admin_pass` (str): Password for the admin user. If omitted, one is generated.
                - `db_charset` (str): Database charset. One of "latin1", "utf8", or "utf8mb4" (default).
                - `db_collate` (str): Database collation, e.g., "latin1_swedish_ci".
                - `php_version` (str): Desired PHP version, e.g., "8.1", "8.2", "8.3".
                - `space_quota` (str): Disk space limit, e.g., "200G". Default is "200G".
                - `clone_from` (int): Atomic site ID of a site to clone from.
                - `geo_affinity` (str): Preferred datacenter code (e.g., "dfw", "bur") for primary server assignment.
                - `software` (dict): Software to install/activate, e.g., `{"plugins/akismet/latest": "activate"}`.
                - `meta` (dict): Additional site metadata, e.g., `{"development_mode": "1"}`.

        Returns:
            A Job object representing the asynchronous site creation task.
        """
        payload = {
            "admin_user": admin_user,
            "admin_email": admin_email,
        }
        if domain_name:
            payload['domain_name'] = domain_name

        # Process the kwargs to build the final payload correctly
        meta_data = kwargs.pop('meta', {})
        software_data = kwargs.pop('software', {})

        # Add any remaining simple kwargs to the payload
        payload.update(kwargs)

        # Manually construct the array-like form data for 'meta' and 'software'
        for key, value in meta_data.items():
            payload[f"meta[{key}]"] = value

        for key, value in software_data.items():
            payload[f"software[{key}]"] = value

        endpoint = f"/create-site/{self._client_id_or_name}"
        response_data = self._post(endpoint, data=payload)

        job = Job.parse_obj(response_data)
        job._client = self._client
        return job

    def delete(self, site_id: Optional[int] = None, domain: Optional[str] = None) -> Job:
        """
        Marks a site for deletion. This is an asynchronous operation.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A Job object representing the asynchronous site deletion task.
        """
        service, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/delete-site/{service}/{identifier}"
        response_data = self._post(endpoint)

        job = Job.parse_obj(response_data)
        job._client = self._client
        return job

    def update_domain(self, new_domain: str, site_id: Optional[int] = None, domain: Optional[str] = None, keep_old_domain: bool = False) -> Job:
        """
        Updates a site's primary domain. This is an asynchronous operation.

        Args:
            new_domain: The new primary domain for the site.
            site_id: The current Atomic site ID.
            domain: The current domain name of the site.
            keep_old_domain: If True, keeps the old primary domain as an alias.

        Returns:
            A Job object for the asynchronous domain update task.
        """
        service, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/update-site-domain/{service}/{identifier}/{new_domain}"
        if keep_old_domain:
            endpoint += "/keep"
        response_data = self._post(endpoint)

        job = Job.parse_obj(response_data)
        job._client = self._client
        return job

    # --- Domain and DNS Management ---

    def check_can_host_domain(self, domain: str) -> bool:
        """
        Checks if a domain can be hosted on WP Cloud. Note that this check will return
        False for valid domains that are already hosted on WordPress.com or WP Cloud
        infrastructure, unless a verification TXT record is in place.

        Args:
            domain: The domain name to check.

        Returns:
            True if the domain can be hosted, False otherwise.
        """
        endpoint = f"/check-can-host-domain/{self._client_id_or_name}/{domain}"
        response_data = self._get(endpoint)
        return response_data.get('allowed', False)

    def get_domain_verification_code(self, domain: str) -> str:
        """
        Generates the domain verification code, to be used as a TXT record so that a
        domain can be "claimed" from another WP Cloud client or WordPress.com.

        Args:
            domain: The domain name that requires verification.

        Returns:
            The verification code string (e.g., "atomic-domain-12b2...").
        """
        endpoint = f"/get-domain-verification-code/{self._client_id_or_name}/{domain}"
        return self._get(endpoint)

    def get_ips(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Gets the IPs for the client. If a domain is included, also get suggested IPs
        if possible for the client.

        Args:
            domain: Optional domain name to get suggested IPs for.

        Returns:
            A dictionary containing IP information, including 'ips' and 'suggested'.
        """
        endpoint = f"/get-ips/{self._client_id_or_name}"
        if domain:
            endpoint += f"/{domain}"
        return self._get(endpoint)

    def list_aliases(self, site_id: Optional[int] = None, domain: Optional[str] = None) -> List[str]:
        """Lists all domain aliases for a site."""
        service, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-alias/{service}/{identifier}/list"
        response_data = self._get(endpoint)
        return response_data.get("domains", [])

    def add_alias(self, alias_domain: str, site_id: Optional[int] = None, domain: Optional[str] = None) -> List[str]:
        """Adds a domain alias to a site."""
        service, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-alias/{service}/{identifier}/add/{alias_domain}"
        response_data = self._get(endpoint)
        return response_data.get("domains", [])

    def remove_alias(self, alias_domain: str, site_id: Optional[int] = None, domain: Optional[str] = None) -> dict:
        """Removes a domain alias from a site."""
        service, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-alias/{service}/{identifier}/remove/{alias_domain}"
        return self._get(endpoint)

    # --- Site Configuration and Software ---

    def manage_software(self, software_actions: Dict[str, str], site_id: Optional[int] = None, domain: Optional[str] = None) -> Job:
        """
        Manages a site's software (install, activate, remove, lock, etc.).
        This is an asynchronous operation.

        Args:
            software_actions: A dictionary where keys are software slugs and values are the
                              action. Actions can be "activate", "install", "deactivate",
                              "remove", "lock", or "unlock". Slugs can be from the WordPress.org
                              repository (e.g., "plugins/akismet/latest") or a direct URL
                              (e.g., "plugin://url...").
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A Job object for the asynchronous task.
        """
        if not software_actions:
            raise InvalidRequestError("software_actions dictionary cannot be empty.")
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-manage-software/atomic/{identifier}"
        response_data = self._post(endpoint, data=software_actions)

        job = Job.parse_obj(response_data)
        job._client = self._client
        return job

    def set_wordpress_version(self, version: Literal["latest", "previous", "beta"], site_id: Optional[int] = None, domain: Optional[str] = None) -> Job:
        """
        Configures a site to use a specific managed version of WordPress. This is an
        asynchronous operation.

        Args:
            version: The WordPress version track. Must be one of "latest", "previous", or "beta".
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A Job object for the asynchronous task.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-wordpress-version/{identifier}/{version}"
        response_data = self._post(endpoint)
        job = Job.parse_obj(response_data)
        job._client = self._client
        return job

    def update_options(self, options: dict, site_id: Optional[int] = None, domain: Optional[str] = None) -> Job:
        """
        Updates a site's WordPress options. This is an asynchronous operation.

        The `options` dictionary can contain `set` and `patch` keys to perform
        different types of updates on the site's `wp_options` table.

        Args:
            options: A dictionary specifying the options to update.
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A Job object for the asynchronous task.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/update-site-options/atomic/{identifier}"
        response_data = self._post(endpoint, data={'options': options})
        job = Job.parse_obj(response_data)
        job._client = self._client
        return job

    def update_persistent_data(self, data_to_update: Dict[str, Any], site_id: Optional[int] = None, domain: Optional[str] = None) -> Job:
        """
        Adds or removes persistent data keys for a site. This is an asynchronous operation.
        The data is stored as a JSON-encoded array on the platform.

        Args:
            data_to_update: A dictionary specifying updates.
                            e.g., `{'foo': {'value': 'some data'}, 'bar': {'delete': 1}}`.
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A Job object for the asynchronous task.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-persist-data/{identifier}"
        payload = {}
        for key, actions in data_to_update.items():
            for action, value in actions.items():
                payload[f"data[{key}][{action}]"] = value
        response_data = self._post(endpoint, data=payload)
        job = Job.parse_obj(response_data)
        job._client = self._client
        return job

    # --- Site Metadata and Utilities ---

    def get_meta(self, key: str, site_id: Optional[int] = None, domain: Optional[str] = None) -> Any:
        """
        Gets a single metadata key for a site.

        Supported keys include: `wp_version`, `php_version`, `space_quota`, `space_used`,
        `db_file_size`, `suspended`, `suspend_after`, `burst_php_conns`, `default_php_conns`,
        `php_memory_limit`, `static_file_404`, `geo_affinity`, `privacy_model`, etc.

        Args:
            key: The metadata key to retrieve.
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            The value of the metadata key.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-meta/{identifier}/{key}/get"
        return self._get(endpoint)

    def update_meta(self, key: str, value: Any, site_id: Optional[int] = None, domain: Optional[str] = None) -> dict:
        """
        Updates a single metadata key for a site.

        Args:
            key: The metadata key to update (e.g., 'php_version', 'suspended').
            value: The new value for the key.
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            The API response data.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-meta/{identifier}/{key}/update"
        return self._post(endpoint, data={"value": value})

    def get_phpmyadmin_url(self, site_id: Optional[int] = None, domain: Optional[str] = None) -> str:
        """
        Gets a time-limited URL for accessing a site's database via phpMyAdmin.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            The phpMyAdmin login URL.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-phpmyadmin/{identifier}"
        response_data = self._post(endpoint)
        return response_data.get("url")

    def reset_db_password(self, site_id: Optional[int] = None, domain: Optional[str] = None) -> Job:
        """
        Resets the database password for a site. This is an asynchronous operation.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A Job object for the asynchronous task.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/reset-db-password/atomic/{identifier}"
        response_data = self._post(endpoint)
        job = Job.parse_obj(response_data)
        job._client = self._client
        return job

    # --- SSL Management ---

    def get_ssl_info(self, domain: str) -> Dict[str, Any]:
        """Fetches SSL certificate information for a domain."""
        return self._post(f"/ssl-info/{domain}")

    def retry_ssl_provisioning(self, domain: str) -> bool:
        """Retries SSL certificate provisioning for a domain."""
        response_data = self._post(f"/ssl-retry/{domain}")
        return response_data.get('queued', False)

    def set_ssl_android_compat(self, domain: str, enable: bool) -> dict:
        """Enable/disable SSL certificates compatible with older Android devices."""
        return self._post(f"/ssl-android-compat/{domain}/{str(enable).lower()}")

    def disable_hsts_preload(self, domain: str) -> dict:
        """Disables the HSTS preload directive."""
        return self._post(f"/ssl-hsts-preload/{domain}/false")

    def set_hsts_subdomain(self, domain: str, enable: bool) -> dict:
        """Enable/disable the HSTS includeSubDomains directive."""
        return self._post(f"/ssl-hsts-subdomain/{domain}/{str(enable).lower()}")

    def set_ssl_social_crawler_redirect(self, domain: str, enable: bool) -> dict:
        """
        Enable/disable redirect from https to http for social crawlers. This is used
        to retain share counts if links were originally shared as http.

        Args:
            domain: The site's domain name.
            enable: True to enable the redirect, False to disable.
        """
        return self._post(f"/ssl-social-crawler-redirect/{domain}/{str(enable).lower()}")

    # --- Logging ---

    def get_site_logs(self, start: int, end: int, site_id: Optional[int] = None, domain: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Get web server access log data from a site.

        Args:
            start: A Unix timestamp for the start of the log data range.
            end: A Unix timestamp for the end of the log data range.
            site_id: The Atomic site ID.
            domain: The domain name of the site.
            **kwargs: Optional log arguments: page_size (int), scroll_id (str),
                      sort_order ('asc' or 'desc'), filters (dict, e.g., {'status': ['404']}).

        Returns:
            A dictionary containing the logs, total results, and a potential scroll_id.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-logs/{identifier}"
        payload = self._build_log_payload({"start": start, "end": end, **kwargs})
        return self._post(endpoint, data=payload)

    def get_error_logs(self, start: int, end: int, site_id: Optional[int] = None, domain: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Get PHP error log data from a site. Arguments are identical to get_site_logs.
        """
        _, identifier = self._get_service_and_identifier(site_id, domain)
        endpoint = f"/site-error-logs/{identifier}"
        payload = self._build_log_payload({"start": start, "end": end, **kwargs})
        return self._post(endpoint, data=payload)

    # --- Job Status ---

    def get_job_status(self, job_id: int) -> str:
        """
        Gets the status of a specific job by its ID. A job's status can be
        'success', 'failure', or 'queued'.

        Args:
            job_id: The ID of the job to check.

        Returns:
            The job status string.
        """
        return self._get(f"/job-status/{job_id}")

    def get_job_completion(self, job_id: int) -> str:
        """
        Gets status of a job by ID (older endpoint, `get_job_status` is preferred).

        Args:
            job_id: The ID of the job to check.

        Returns:
            The job status string.
        """
        return self._get(f"/job-completion/{job_id}")
