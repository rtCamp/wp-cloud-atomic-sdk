from typing import List, Optional, Literal, Union, TYPE_CHECKING

from .base import ResourceClient
from ..models import Backup, BackupJob

if TYPE_CHECKING:
    from ..client import AtomicClient

class BackupsClient(ResourceClient):
    """
    A client for interacting with the Backups endpoints of the Atomic API.
    """
    _client: 'AtomicClient' = None

    def create(
            self,
            site_id: int,
            backup_type: Literal["fs", "db"]
        ) -> BackupJob:
        """
        Requests the creation of an on-demand backup for a site.
        This is a 'fire-and-forget' asynchronous operation. The returned object
        contains a request ID, but the API does not support polling its status.
        """
        if backup_type not in ["fs", "db"]:
            raise ValueError("backup_type must be either 'fs' or 'db'")

        url = f"/on-demand-backup/create/{site_id}/{backup_type}"
        response_data = self._post(url)
        return BackupJob.parse_obj(response_data)

    def delete(self, site_id: int, backup_id: int) -> BackupJob:
        """
        Requests the removal of a specific on-demand backup.
        This is a 'fire-and-forget' asynchronous operation. The returned object
        contains a request ID, but the API does not support polling its status.
        """
        url = f"/on-demand-backup/delete/{site_id}/{backup_id}"
        response_data = self._post(url)
        return BackupJob.parse_obj(response_data)

    def list(
        self,
        site_id: Optional[int] = None,
        domain: Optional[str] = None,
        backup_types: Optional[List[Literal["db", "fs", "ondemand-fs", "ondemand-db"]]] = None,
    ) -> List[Backup]:
        """
        Retrieves a list of available backups for a site.

        Args:
            site_id: The Atomic site ID.
            domain: The domain name of the site.
            backup_types: Optional list to filter by backup type.
                          Valid types are 'db', 'fs', 'ondemand-fs', 'ondemand-db'.

        Returns:
            A list of Backup objects.
        """
        service, identifier = self._get_service_and_identifier(site_id=site_id, domain=domain)
        url = f"/site-backups-list/{service}/{identifier}"
        if backup_types:
            url += f"/{'/'.join(backup_types)}"
        response_data = self._get(url)
        return [Backup.parse_obj(item) for item in response_data]

    def info(self, backup_id: Union[int, str], site_id: Optional[int] = None, domain: Optional[str] = None) -> Backup:
        """
        Fetches the metadata for a single, specific backup (site-backup-info).

        Args:
            backup_id: The ID of the backup to retrieve information for.
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            A Backup object containing the backup's metadata.
        """
        service, identifier = self._get_service_and_identifier(site_id=site_id, domain=domain)
        url = f"/site-backup-info/{service}/{identifier}/{backup_id}"
        response_data = self._get(url)
        return Backup.parse_obj(response_data)

    def get(self, backup_id: Union[int, str], site_id: Optional[int] = None, domain: Optional[str] = None) -> bytes:
        """
        Downloads the raw content of a backup file (site-backup-get).

        The returned content is either a bzipped tar archive (for filesystem backups)
        or a MySQL dump (for database backups).

        Args:
            backup_id: The ID of the backup to download.
            site_id: The Atomic site ID.
            domain: The domain name of the site.

        Returns:
            The raw bytes of the backup file.
        """
        service, identifier = self._get_service_and_identifier(site_id=site_id, domain=domain)
        url = f"/site-backup-get/{service}/{identifier}/{backup_id}"
        return self._get_raw(url)
