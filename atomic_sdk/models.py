from datetime import datetime
from typing import List, Optional, Literal, Any, Dict

from pydantic import BaseModel, Field, validator, ConfigDict


# A helper function to convert empty strings from the API to None for optional fields.
def empty_str_to_none(v: Any) -> Optional[Any]:
    if isinstance(v, str) and v == "":
        return None
    return v


class Site(BaseModel):
    """
    Represents the detailed information for a single site.
    """
    atomic_site_id: int
    wpcom_blog_id: Optional[int] = None
    domain_name: str
    server_pool_id: int
    db_pass: Optional[str] = None
    cache_prefix: str
    wp_admin_user: str
    wp_admin_email: str
    db_charset: str
    db_collate: str
    php_version: str
    wp_version: Optional[str] = None
    migrate_to_pool: Optional[int] = None
    migrate_readonly: Optional[int] = None
    photon_subsizes: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None

    def get_extra(self, key: str, default: Any = None) -> Any:
        """Helper to safely access a value from the 'extra' dictionary."""
        if self.extra:
            return self.extra.get(key, default)
        return default


class Job(BaseModel):
    """
    Represents an asynchronous job returned by the API.
    """
    job_id: int = Field(..., description="The unique identifier for the job.")
    wpcom_blog_id: Optional[int] = Field(None, description="WordPress.com blog ID, if applicable.")
    atomic_site_id: Optional[int] = Field(None, description="The Atomic site ID associated with the job.")
    domain_name: Optional[str] = Field(None, description="The domain name associated with the job.")

    # Placeholder for a client instance to be attached post-initialization
    # This will allow methods like job.status() to work.
    _client: Any = None

    def status(self) -> str:
        """
        Fetches the current status of the job from the API.

        Returns:
            The job status, e.g., 'queued', 'success', 'failure'.

        Raises:
            Exception: if the internal client reference is not set.
        """
        if not self._client:
            raise RuntimeError("Job object must be initialized with a client reference to fetch status.")
        return self._client.sites.get_job_status(self.job_id)

    def wait(self, timeout: int = 300, poll_interval: int = 5) -> str:
        """
        Blocks until the job is complete or the timeout is reached.

        Args:
            timeout: Maximum time to wait in seconds.
            poll_interval: Time to wait between status checks in seconds.

        Returns:
            The final status of the job ('success' or 'failure').

        Raises:
            TimeoutError: If the job does not complete within the timeout period.
        """
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_status = self.status()
            if current_status in ["success", "failure"]:
                return current_status
            time.sleep(poll_interval)

        raise TimeoutError(f"Job {self.job_id} did not complete within {timeout} seconds.")

class BackupJob(BaseModel):
    """
    Represents the response from a non-pollable, asynchronous backup request.
    The API provides a request ID but no endpoint to check its status.
    """
    request_id: int = Field(..., alias="atomic_backup_request_id")

class Backup(BaseModel):
    """

    Represents a backup record for a site.
    """
    atomic_backup_id: str = Field(..., description="The unique identifier for the backup.")
    atomic_site_id: str = Field(..., description="The Atomic site ID.")
    backup_timestamp: datetime = Field(..., description="Timestamp of when the backup was created.")
    type: Literal["fs", "db", "ondemand", "ondemand-fs", "ondemand-db"] = Field(
        ..., description="The type of backup."
    )

class TaskCreationResponse(BaseModel):
    """
    Represents the immediate response after creating a new bulk task.
    It contains the essential ID to begin monitoring.
    """
    task_id: int
    initial_task_manager_id: int
    meta: Dict[str, Any]

class Task(BaseModel):
    """Represents the full details of a bulk task, retrieved via the get() method."""
    task_id: int
    atomic_client_id: Optional[int] = Field(None, alias="client_id")
    type: Optional[str] = None
    created: Optional[datetime] = None
    complete: Optional[datetime] = None
    meta: Dict[str, Any]

    model_config = ConfigDict(populate_by_name=True)

    @validator("complete", pre=True)
    def _validate_complete(cls, v):
        if isinstance(v, str) and v == "":
            return None
        return v
