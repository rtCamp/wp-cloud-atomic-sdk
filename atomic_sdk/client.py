import requests
import sys

# Use the standard library for package metadata
if sys.version_info < (3, 8):
    from importlib_metadata import version
else:
    from importlib.metadata import version

from .api.backups import BackupsClient
from .api.client import ClientClient
from .api.edge_cache import EdgeCacheClient
from .api.email import EmailClient
from .api.metrics import MetricsClient
from .api.servers import ServersClient
from .api.sites import SitesClient
from .api.ssh import SSHClient
from .api.tasks import TasksClient
from .api.utility import UtilityClient


class AtomicClient:
    """The main client for interacting with the WP.cloud Atomic API."""

    BASE_URL = "https://atomic-api.wordpress.com/api/v1.0/"

    def __init__(self, api_key: str, client_id_or_name: str, timeout: int = 30):
        """
        Initializes the Atomic API client.

        Args:
            api_key: Your platform or developer API key for authentication.
            client_id_or_name: Your unique client identifier (e.g., 'your-client-name').
            timeout: The timeout in seconds for API requests. Defaults to 30.
        """
        if not api_key:
            raise ValueError("An API key is required.")
        if not client_id_or_name:
            raise ValueError("A client identifier (name or ID) is required.")

        self.api_key = api_key
        self.client_id_or_name = client_id_or_name
        self.timeout = timeout

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

        # Instantiate and attach all the resource-specific clients
        self.backups = BackupsClient(self._session, self.BASE_URL, self.client_id_or_name)
        self.client = ClientClient(self._session, self.BASE_URL, self.client_id_or_name)
        self.edge_cache = EdgeCacheClient(self._session, self.BASE_URL, self.client_id_or_name)
        self.email = EmailClient(self._session, self.BASE_URL, self.client_id_or_name)
        self.metrics = MetricsClient(self._session, self.BASE_URL, self.client_id_or_name)
        self.servers = ServersClient(self._session, self.BASE_URL, self.client_id_or_name)
        self.sites = SitesClient(self._session, self.BASE_URL, self.client_id_or_name)
        self.ssh = SSHClient(self._session, self.BASE_URL, self.client_id_or_name)
        self.tasks = TasksClient(self._session, self.BASE_URL, self.client_id_or_name)
        self.utility = UtilityClient(self._session, self.BASE_URL, self.client_id_or_name)

        # Pass a reference of the main client to the sites client for job status checks
        self.sites._client = self

    def __repr__(self):
        return f"<AtomicClient client_id='{self.client_id_or_name}'>"
