from typing import List, Dict, Any, Union
from .base import ResourceClient


class ServersClient(ResourceClient):
    """
    A client for retrieving information about the hosting infrastructure.
    """

    def list_available_datacenters(self) -> List[str]:
        """
        Gets a list of datacenters with available (non-full, active) servers.

        These datacenter codes (e.g., 'bur', 'dca') can be used in the
        'geo_affinity' parameter when creating a site.

        Returns:
            A list of available datacenter codes.
        """
        endpoint = f"/get-available-datacenters/{self._client_id_or_name}"
        return self._get(endpoint)

    def list_php_versions(self, verbose: bool = False) -> Union[List[str], Dict[str, Any]]:
        """
        Gets a list of available PHP versions on the platform.

        Args:
            verbose: If True, returns a more detailed dictionary with deprecation
                     status and the default version. If False (default), returns
                     a simple list of version strings.

        Returns:
            A list of PHP version strings or a detailed dictionary if verbose is True.
        """
        endpoint = f"/get-php-versions/{self._client_id_or_name}"
        if verbose:
            endpoint += "/verbose"

        return self._get(endpoint)
