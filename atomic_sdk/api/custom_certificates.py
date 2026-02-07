"""
Client for managing custom SSL certificates for WP Cloud sites.

This module provides functionality to stage, activate, deactivate, delete,
and retrieve custom SSL certificates via the WP Cloud Atomic API.
"""

from typing import Optional, List, Dict, Any, Union

from .base import ResourceClient


class CustomCertificatesClient(ResourceClient):
    """
    A client for managing custom SSL certificates on WP Cloud sites.

    Custom certificates allow you to use your own SSL/TLS certificates
    instead of the automatically provisioned Let's Encrypt certificates.

    The typical workflow is:
    1. Stage a certificate using `stage()` - validates and stores the certificate
    2. Activate the staged certificate using `activate()` - makes it live
    3. Optionally deactivate with `deactivate()` to switch back to auto-provisioned
    4. Delete old/unused certificates with `delete()`
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

    def _prepare_domains_data(self, data: Dict[str, Any], domains: Optional[List[str]]) -> None:
        """Helper to correctly serialize domains array for PHP/WP Cloud API."""
        if domains:
            # PHP-based APIs typically expect 'domains[]' for array data in form-urlencoded POST requests.
            # Requests library will serialize {'domains[]': ['a', 'b']} as 'domains[]=a&domains[]=b'.
            data["domains[]"] = domains

    def stage(
        self,
        certificate: str,
        private_key: str,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        domains: Optional[List[str]] = None,
        csr: Optional[str] = None,
        trusted_certificates: Optional[str] = None,
        client_certificate: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Stage a custom SSL certificate for later activation.

        Args:
            certificate: PEM-encoded SSL certificate, or certificate chain.
            private_key: PEM-encoded private key.
            site_id: The Atomic site ID.
            domain: The domain name of the site.
            domains: Optional list of domains to validate the certificate for.
            csr: Optional PEM-encoded CSR.
            trusted_certificates: Optional PEM-encoded trusted CA certificates.
            client_certificate: Optional PEM-encoded client certificate.

        Returns:
            Dictionary with staging result.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/custom-certificates/{identifier}/stage"

        data: Dict[str, Any] = {
            "certificate": certificate,
            "private_key": private_key,
        }

        self._prepare_domains_data(data, domains)
        
        if csr:
            data["csr"] = csr
        if trusted_certificates:
            data["trusted_certificates"] = trusted_certificates
        if client_certificate:
            data["client_certificate"] = client_certificate

        return self._post(endpoint, data=data)

    def activate(
        self,
        certificate_id: int,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Activate a previously staged custom SSL certificate.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/custom-certificates/{identifier}/{certificate_id}/activate"

        data: Dict[str, Any] = {}
        self._prepare_domains_data(data, domains)

        return self._post(endpoint, data=data if data else None)

    def deactivate(
        self,
        certificate_id: int,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deactivate a custom SSL certificate.

        Args:
            certificate_id: The ID of the certificate to deactivate.
            site_id: The Atomic site ID.
            domain: The domain name of the site.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/custom-certificates/{identifier}/{certificate_id}/deactivate"
        return self._post(endpoint)

    def delete(
        self,
        certificate_id: int,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Delete a custom SSL certificate.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/custom-certificates/{identifier}/{certificate_id}/delete"
        return self._post(endpoint)

    def get(
        self,
        certificate_id: int,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get details for a specific custom SSL certificate.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/custom-certificates/{identifier}/{certificate_id}"
        return self._get(endpoint)
    
    def get_active(
        self,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Helper to retrieve the currently active certificate for a site.
        
        This fetches the list of certificates and returns the first one marked as active.
        Returns None if no active certificate is found.
        """
        result = self.list(site_id=site_id, domain=domain, status='active', limit=1)
        certificates = result.get('certificates', [])
        if certificates:
            # Double check is_active flag just in case
            cert = certificates[0]
            if cert.get('is_active'):
                return cert
        return None

    def list(
        self,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        expiring_within_days: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List custom SSL certificates for a site.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.
            status: Filter by status ('active', 'staged', 'all').
            limit: Max number of results (default 100).
            offset: Pagination offset (default 0).
            expiring_within_days: Filter certs expiring within N days.
            order_by: Sort order ('expiration', 'created').

        Returns:
            Dictionary containing list of 'certificates' and 'pagination' info.
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/custom-certificates/{identifier}/list"

        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if status:
            params["status"] = status
        if expiring_within_days is not None:
            params["expiring_within_days"] = expiring_within_days
        if order_by:
            params["order_by"] = order_by

        return self._get(endpoint, params=params)

    def update(
        self,
        certificate_id: int,
        certificate: Optional[str] = None,
        private_key: Optional[str] = None,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        domains: Optional[List[str]] = None,
        csr: Optional[str] = None,
        trusted_certificates: Optional[str] = None,
        client_certificate: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update/Renew an existing custom certificate.

        Args:
            certificate_id: ID of the certificate to update.
            certificate: Optional new PEM-encoded SSL certificate.
            private_key: Optional new PEM-encoded private key.
            domains: Optional new list of domains.
            ... other optional fields ...
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/custom-certificates/{identifier}/{certificate_id}/update"

        data: Dict[str, Any] = {}
        
        if certificate:
            data["certificate"] = certificate
        if private_key:
            data["private_key"] = private_key
            
        self._prepare_domains_data(data, domains)
        
        if csr:
            data["csr"] = csr
        if trusted_certificates:
            data["trusted_certificates"] = trusted_certificates
        if client_certificate:
            data["client_certificate"] = client_certificate

        return self._post(endpoint, data=data)

    def validate(
        self,
        certificate: str,
        private_key: str,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        domains: Optional[List[str]] = None,
        csr: Optional[str] = None,
        trusted_certificates: Optional[str] = None,
        client_certificate: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate a certificate and private key without saving.

        Args matches stage().
        """
        identifier = self._get_identifier(site_id, domain)
        endpoint = f"/custom-certificates/{identifier}/validate"

        data: Dict[str, Any] = {
            "certificate": certificate,
            "private_key": private_key,
        }
        self._prepare_domains_data(data, domains)
        
        if csr:
            data["csr"] = csr
        if trusted_certificates:
            data["trusted_certificates"] = trusted_certificates
        if client_certificate:
            data["client_certificate"] = client_certificate

        return self._post(endpoint, data=data)

    def stage_and_activate(
        self,
        certificate: str,
        private_key: str,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        domains: Optional[List[str]] = None,
        csr: Optional[str] = None,
        trusted_certificates: Optional[str] = None,
        client_certificate: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method to stage and immediately activate a certificate.

        Args matches stage().
        
        This method includes rollback logic: if activation fails (either via exception
        or via an `activated: false` response), it attempts to delete the staged
        certificate to prevent orphans.
        """
        # Stage the certificate first
        stage_result = self.stage(
            certificate=certificate,
            private_key=private_key,
            site_id=site_id,
            domain=domain,
            domains=domains,
            csr=csr,
            trusted_certificates=trusted_certificates,
            client_certificate=client_certificate,
        )

        certificate_id = stage_result.get("ssl_custom_certificate_id")
        if not certificate_id:
            raise RuntimeError("Failed to get certificate ID from staging response")

        def _rollback() -> None:
            """Attempt to delete the staged certificate."""
            try:
                self.delete(certificate_id=certificate_id, site_id=site_id, domain=domain)
            except Exception:
                # Swallow delete error so caller sees the original activation error
                pass

        try:
            # Activate the staged certificate
            activate_result = self.activate(
                certificate_id=certificate_id,
                site_id=site_id,
                domain=domain,
                domains=domains,
            )

            # Check if activation was successful via response field
            if not activate_result.get("activated", True):
                _rollback()
                raise RuntimeError(
                    f"Activation returned false for certificate {certificate_id}. "
                    "Staged certificate has been rolled back."
                )

            # Include the certificate ID in the response for convenience
            activate_result["certificate_id"] = certificate_id
            return activate_result
            
        except Exception:
            # Rollback: Attempt to delete the staged certificate
            _rollback()
            raise
