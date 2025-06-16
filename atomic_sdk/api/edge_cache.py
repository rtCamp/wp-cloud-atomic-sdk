from typing import Optional, Literal, Dict, Any, Union

from .base import ResourceClient
from ..exceptions import InvalidRequestError


class EdgeCacheClient(ResourceClient):
    """
    A client for managing a site's edge cache and defensive mode settings.
    """

    def _get_identifier(self, site_id: Optional[int] = None, domain: Optional[str] = None) -> Union[int, str]:
        """Internal helper to get the site identifier for endpoints in this group."""
        if domain:
            return domain
        if site_id:
            return site_id
        raise ValueError("You must provide either a 'site_id' or a 'domain'.")

    def get_status(self, site_id: Optional[int] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves a site's edge cache settings.

        The status can be "Enabled", "Disabled", or "DDoS".

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A dictionary containing the cache status information, including `status`,
            `status_name`, and `ddos_until` timestamp.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/edge-cache/{identifier}"
        return self._get(endpoint)

    def set_status(
        self,
        action: Literal["on", "off", "purge"],
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Manages a site's edge cache settings by performing an action.

        Args:
            action: The action to perform. Must be 'on' (enable),
                    'off' (disable), or 'purge'.
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            The response from the API, typically an empty dictionary on success.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/edge-cache/{identifier}/{action}"
        return self._post(endpoint)

    def set_defensive_mode(self, expiration_timestamp: int, site_id: Optional[int] = None, domain: Optional[str] = None) -> dict:
        """
        Enable or disable defensive (DDoS) mode for a site.

        Args:
            expiration_timestamp: A Unix timestamp for when defensive mode should expire.
                                  Set to 0 to disable defensive mode immediately.
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            The API response dictionary.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/edge-cache/{identifier}/ddos_until"
        return self._post(endpoint, data={"timestamp": str(expiration_timestamp)})

    def enable_defensive_mode(self, duration_in_minutes: int, site_id: Optional[int] = None, domain: Optional[str] = None) -> dict:
        """
        Convenience method to enable defensive mode for a specific duration.

        Args:
            duration_in_minutes: The number of minutes to keep defensive mode active.
            site_id: The Atomic site ID.
            domain: The domain name of the site.
        """
        import time
        if duration_in_minutes <= 0:
            raise ValueError("Duration must be a positive number of minutes.")

        expiration = int(time.time()) + (duration_in_minutes * 60)
        return self.set_defensive_mode(expiration, site_id=site_id, domain=domain)

    def disable_defensive_mode(self, site_id: Optional[int] = None, domain: Optional[str] = None) -> dict:
        """
        Convenience method to disable defensive mode immediately.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.
        """
        return self.set_defensive_mode(0, site_id=site_id, domain=domain)

    def purge(self, site_id: Optional[int] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        A convenience method to purge the edge cache for a site.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.
        """
        return self.set_status(action="purge", site_id=site_id, domain=domain)
