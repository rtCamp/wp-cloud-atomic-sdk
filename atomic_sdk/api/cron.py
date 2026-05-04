"""
Client for managing WP-Cron entries on WP Cloud sites.

This module provides functionality to list, add, and remove cron entries
via the WP Cloud Atomic API's /crontab/* endpoints.
"""

from typing import Any, Dict, List, Optional, Union

from .base import ResourceClient


class CronClient(ResourceClient):
    """
    A client for managing WP-Cron entries on WP Cloud sites.

    Provides access to the three ``/crontab/{site}/*`` endpoints for listing,
    adding, and removing scheduled cron entries.

    Platform constraints for cron entries:

    - Maximum runtime per entry is **8 hours**; the platform kills longer runs.
    - A run is **skipped** if the previous run for the same entry has not
      finished yet (no stacking).
    - At most **3 concurrent entries** run in parallel per site; additional
      entries are postponed until a slot becomes free.
    - A ``site-cron-results`` webhook fires on any entry failure.
    """

    def _get_identifier(
        self, site_id: Optional[int] = None, domain: Optional[str] = None
    ) -> Union[int, str]:
        """Internal helper to resolve the site identifier for this endpoint group."""
        if domain:
            return domain
        if site_id:
            return site_id
        raise ValueError("You must provide either a 'site_id' or a 'domain'.")

    def list(
        self,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all cron entries for a site.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A list of dictionaries, each containing ``cron_id``, ``schedule``,
            and ``command`` for a scheduled entry.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/crontab/{identifier}/list"
        return self._get(endpoint)

    def add(
        self,
        schedule: str,
        command: str,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a new cron entry to a site.

        ``schedule`` accepts the following formats:

        - **Named intervals**: ``hourly``, ``daily``, ``twicedaily``, ``weekly``.
        - **Shorthand**: ``2h``, ``6d``, ``3w`` (N-per-unit).
        - **Full crontab expressions** (e.g. ``*/2 * * * *``) — only when
          advanced cron is enabled on the site/client.

        Platform constraints:

        - Maximum runtime per entry is **8 hours**.
        - Runs are skipped if the previous run has not finished (no stacking).
        - At most **3 concurrent entries** run in parallel per site.
        - A ``site-cron-results`` webhook fires on failure.

        Args:
            schedule: The cron schedule string (named interval, shorthand, or
                full crontab expression).
            command: The WP-CLI command or shell command to execute.
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A dictionary containing the newly created ``cron_id``.

        Raises:
            ValueError: If ``schedule`` or ``command`` is empty, or if neither
                ``site_id`` nor ``domain`` is supplied.
        """
        if not schedule or not schedule.strip():
            raise ValueError("'schedule' must not be empty.")
        if not command or not command.strip():
            raise ValueError("'command' must not be empty.")

        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/crontab/{identifier}/add"
        return self._post(endpoint, data={"schedule": schedule, "command": command})

    def remove(
        self,
        cron_id: int,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Remove a cron entry from a site.

        Args:
            cron_id: The ID of the cron entry to remove.
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            The API response dictionary (typically empty on success).
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/crontab/{identifier}/remove"
        return self._post(endpoint, data={"cron_id": str(cron_id)})

    def find(
        self,
        cron_id: Optional[int] = None,
        command: Optional[str] = None,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single cron entry by ``cron_id`` or ``command`` (client-side filter).

        Calls :meth:`list` and returns the first matching entry, or ``None`` if
        no match is found. When both filters are supplied, both must match the
        same entry.

        Args:
            cron_id: The cron entry ID to search for.
            command: A command string to match against (substring match).
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            The first matching entry dict, or ``None``.

        Raises:
            ValueError: If neither ``cron_id`` nor ``command`` is provided.
        """
        if cron_id is None and not command:
            raise ValueError("You must provide either a 'cron_id' or a 'command' to search for.")

        entries = self.list(site_id=site_id, domain=domain)
        for entry in entries:
            cron_id_matches = cron_id is None or entry.get("cron_id") == cron_id
            command_matches = not command or command in entry.get("command", "")
            if cron_id_matches and command_matches:
                return entry
        return None

    def clear(
        self,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> List[int]:
        """
        **Destructive** — remove *all* cron entries for a site.

        Lists every entry and calls :meth:`remove` for each one in sequence.
        Entries added after this call begins will not be removed.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A list of the ``cron_id`` values that were removed.
        """
        entries = self.list(site_id=site_id, domain=domain)
        removed = []
        for entry in entries:
            cron_id = entry.get("cron_id")
            if cron_id is not None:
                self.remove(cron_id, site_id=site_id, domain=domain)
                removed.append(cron_id)
        return removed
