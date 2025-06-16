# --- SDK Version ---
__version__ = "0.1.0"


# --- Main Client ---
# Make the main client class directly importable from the package root.
# Allows for `from atomic_sdk import AtomicClient`
from .client import AtomicClient


# --- Custom Exceptions ---
# Expose all custom exceptions for easy error handling.
# Allows for `from atomic_sdk import NotFoundError, AtomicAPIError`
from .exceptions import (
    AtomicAPIError,
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
    ServerError,
)


# --- Data Models ---
# Expose the core data models for type hinting and data access.
# Allows for `from atomic_sdk import Job, Backup, Task`
from .models import Job, Backup, Task


# --- Public API ---
# Define what gets imported with `from atomic_sdk import *`
# It's good practice to be explicit.
__all__ = [
    "AtomicClient",
    "AtomicAPIError",
    "AuthenticationError",
    "InvalidRequestError",
    "NotFoundError",
    "ServerError",
    "Job",
    "Backup",
    "Task",
    "__version__",
]
