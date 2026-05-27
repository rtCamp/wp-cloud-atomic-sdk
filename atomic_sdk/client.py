import requests
import sys

# Use the standard library for package metadata
if sys.version_info < (3, 8):
    from importlib_metadata import version
else:
    from importlib.metadata import version

from .api.backups import BackupsClient
from .api.client import ClientClient
from .api.cron import CronClient
from .api.custom_certificates import CustomCertificatesClient
from .api.edge_cache import EdgeCacheClient
from .api.email import EmailClient
from .api.metrics import MetricsClient
from .api.security import SecurityClient
from .api.servers import ServersClient
from .api.sites import SitesClient
from .api.ssh import SSHClient
from .api.tasks import TasksClient
from .api.utility import UtilityClient
from .api.migrations import MigrationsClient
from .api.response_tickets import ResponseTicketsClient


class AtomicClient:
    """The main client for interacting with the WP.cloud Atomic API."""

    BASE_URL = "https://atomic-api.wordpress.com/api/v1.0/"

    def __init__(
        self,
        api_key: str,
        client_id_or_name: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_base: float = 0.5,
    ):
        """
        Initializes the Atomic API client.

        Args:
            api_key: Your platform or developer API key for authentication.
            client_id_or_name: Your unique client identifier (e.g., 'your-client-name').
            timeout: The timeout in seconds for API requests. Defaults to 30.
            max_retries: Number of retries for 429, 5xx, and connection errors. Defaults to 3.
            backoff_base: Base delay in seconds for exponential backoff with jitter.
        """
        if not api_key:
            raise ValueError("An API key is required.")
        if not client_id_or_name:
            raise ValueError("A client identifier (name or ID) is required.")
        if max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to 0.")
        if backoff_base < 0:
            raise ValueError("backoff_base must be greater than or equal to 0.")

        self.api_key = api_key
        self.client_id_or_name = client_id_or_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base

        # Get the package version at runtime to avoid circular imports
        try:
            sdk_version = version('atomic-sdk')
        except Exception:
            sdk_version = "0.0.0" # Fallback if not installed

        # Create a session object to reuse connections and headers
        self._session = requests.Session()
        self._session.headers.update({
            "Auth": self.api_key,
            "User-Agent": f"Python AtomicSDK/{sdk_version}",
            "Accept": "application/json",
        })
        self._session.timeout = self.timeout

        resource_args = (
            self._session,
            self.BASE_URL,
            self.client_id_or_name,
            self.max_retries,
            self.backoff_base,
        )

        # Instantiate and attach all the resource-specific clients
        self.backups = BackupsClient(*resource_args)
        self.client = ClientClient(*resource_args)
        self.cron = CronClient(*resource_args)
        self.custom_certificates = CustomCertificatesClient(*resource_args)
        self.edge_cache = EdgeCacheClient(*resource_args)
        self.email = EmailClient(*resource_args)
        self.metrics = MetricsClient(*resource_args)
        self.security = SecurityClient(*resource_args)
        self.servers = ServersClient(*resource_args)
        self.sites = SitesClient(*resource_args)
        self.ssh = SSHClient(*resource_args)
        self.tasks = TasksClient(*resource_args)
        self.utility = UtilityClient(*resource_args)
        self.migrations = MigrationsClient(*resource_args)
        self.response_tickets = ResponseTicketsClient(*resource_args)

        # Pass a reference of the main client to resource clients that return Job objects,
        # so Job.status() can call self._client.sites.get_job_status().
        self.sites._client = self
        self.ssh._client = self

    def __repr__(self):
        return f"<AtomicClient client_id='{self.client_id_or_name}'>"
