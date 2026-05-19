"""
Client for managing site-level firewall rules (Security resource).

The WP Cloud `firewall-rules` API controls **egress** (outbound) traffic from a
site's PHP workers. Typical use cases include allow-listing an external MySQL
host or third-party API, or denying outbound SMTP. It is not a WAF, and it does
not control SSH ingress (see `client.client.set_meta('client_ssh_firewall', ...)`
for that surface).
"""

import ipaddress
from typing import Optional, List, Dict, Any, Union, Literal

from .base import ResourceClient


class SecurityClient(ResourceClient):
    """
    A client for managing a site's egress firewall rules.

    Each rule allows or denies outbound traffic from the site's PHP workers to
    a specific destination on a given protocol/port. Rules are evaluated
    server-side; the order and precedence are controlled by the platform.
    """

    def _get_identifier(
        self, site_id: Optional[int] = None, domain: Optional[str] = None
    ) -> Union[int, str]:
        """Internal helper to get the site identifier for endpoints in this group."""
        if domain:
            return domain
        if site_id:
            return site_id
        raise ValueError("You must provide either a 'site_id' or a 'domain'.")

    @staticmethod
    def _parse_destination(value: Any) -> Optional[str]:
        """Return the canonical CIDR string for an IP/CIDR, or None if unparseable."""
        if not isinstance(value, str):
            return None
        try:
            return str(ipaddress.ip_network(value.strip(), strict=False))
        except (ValueError, TypeError):
            return None

    def list_rules(
        self,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all firewall rules configured for a site.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A list of rule dictionaries, each containing `rule_id`, `direction`,
            `action`, `protocol`, `port`, and `destination`.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/firewall-rules/{identifier}/list"
        return self._get(endpoint)

    def add_rule(
        self,
        action: Literal["allow", "deny"],
        protocol: Literal["tcp", "udp"],
        port: int,
        destination: str,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        direction: Literal["egress"] = "egress",
    ) -> Dict[str, Any]:
        """
        Add a firewall rule to a site.

        Args:
            action: Whether to `allow` or `deny` traffic matching the rule.
            protocol: Transport protocol for the rule (`tcp` or `udp`).
            port: Destination port (1-65535).
            destination: IPv4/IPv6 address or CIDR range
                         (e.g. `10.20.30.40/32`, `2001:db8::/32`).
            site_id: The Atomic site ID.
            domain: The domain name of the site.
            direction: Traffic direction. Only `egress` is supported by the API.

        Returns:
            A dictionary describing the created rule (same shape as a list row),
            including the newly assigned `rule_id`.

        Raises:
            ConflictError: If an equivalent or overlapping rule already exists
                           on the site (HTTP 409).
        """
        if not isinstance(port, int) or isinstance(port, bool):
            raise ValueError("'port' must be an integer between 1 and 65535.")
        if not 1 <= port <= 65535:
            raise ValueError("'port' must be between 1 and 65535.")
        if not isinstance(destination, str):
            raise ValueError("'destination' must be a string IP address or CIDR range.")
        destination = destination.strip()
        if not destination:
            raise ValueError("'destination' must be a non-empty IP address or CIDR range.")
        try:
            # Accepts both bare IPs (`10.20.30.40`) and CIDR ranges
            # (`10.20.30.40/32`, `2001:db8::/32`). `strict=False` allows host
            # bits in the address portion of a CIDR.
            ipaddress.ip_network(destination, strict=False)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"'destination' must be a valid IPv4/IPv6 address or CIDR range "
                f"(got {destination!r}): {exc}"
            ) from exc

        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/firewall-rules/{identifier}/add"

        data: Dict[str, Any] = {
            "direction": direction,
            "action": action,
            "protocol": protocol,
            "port": port,
            "destination": destination,
        }
        return self._post(endpoint, data=data)

    def remove_rule(
        self,
        rule_id: int,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> List[Any]:
        """
        Remove a firewall rule from a site.

        Args:
            rule_id: The ID of the rule to remove (from `list_rules()` /
                     `add_rule()`).
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            An empty list on success.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/firewall-rules/{identifier}/remove"
        return self._post(endpoint, data={"rule_id": rule_id})

    def find_rule(
        self,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        rule_id: Optional[int] = None,
        destination: Optional[str] = None,
        port: Optional[int] = None,
        protocol: Optional[Literal["tcp", "udp"]] = None,
        action: Optional[Literal["allow", "deny"]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Convenience helper that returns the first rule matching all supplied
        filters, or `None` if no rule matches. Filters are AND-combined.

        The API has no "get one" endpoint, so this performs a `list_rules()`
        call and filters client-side.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.
            rule_id: Match by rule ID.
            destination: Match by destination IP/CIDR. Both sides are
                         normalized to canonical CIDR form before comparison,
                         so `10.20.30.40` matches a stored `10.20.30.40/32`.
            port: Match by port.
            protocol: Match by protocol (`tcp` or `udp`).
            action: Match by action (`allow` or `deny`).

        Returns:
            The first matching rule dictionary, or `None` if none match.
        """
        if rule_id is None and destination is None and port is None \
                and protocol is None and action is None:
            raise ValueError("At least one filter (rule_id, destination, port, protocol, action) must be provided.")

        if destination is not None:
            normalized = self._parse_destination(destination)
            if normalized is None:
                raise ValueError(
                    f"'destination' must be a valid IPv4/IPv6 address or CIDR range "
                    f"(got {destination!r})."
                )
            destination = normalized

        rules = self.list_rules(site_id=site_id, domain=domain)
        for rule in rules:
            if rule_id is not None and rule.get("rule_id") != rule_id:
                continue
            if destination is not None:
                rule_dest = rule.get("destination")
                if (self._parse_destination(rule_dest) or rule_dest) != destination:
                    continue
            if port is not None and rule.get("port") != port:
                continue
            if protocol is not None and rule.get("protocol") != protocol:
                continue
            if action is not None and rule.get("action") != action:
                continue
            return rule
        return None

    def clear_rules(
        self,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> int:
        """
        Remove every firewall rule from a site.

        ⚠️ Destructive: this issues one `remove_rule()` request per rule and
        is **not atomic**. If a removal fails partway through, iteration stops
        and any rules already removed stay removed; the exception from the
        failed call propagates to the caller. The API has no bulk-delete
        endpoint, so a per-rule loop is the only available primitive.

        Useful for tearing down a test environment.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            The number of rules successfully removed before iteration ended.
        """
        rules = self.list_rules(site_id=site_id, domain=domain)
        removed = 0
        for rule in rules:
            rid = rule.get("rule_id")
            if rid is None:
                continue
            self.remove_rule(rule_id=rid, site_id=site_id, domain=domain)
            removed += 1
        return removed
